# Databricks notebook source
# MAGIC %md
# MAGIC # Vortex DLT Pipeline
# MAGIC 
# MAGIC Real-time streaming pipeline from Azure Event Hub to Delta Lake.
# MAGIC Uses expectations for data quality at each layer.

# COMMAND ----------

import dlt
from pyspark.sql.functions import (
    col, from_json, current_timestamp, 
    when, lit, expr
)
from pyspark.sql.types import (
    StructType, StructField, StringType, 
    DoubleType, IntegerType, BooleanType, 
    TimestampType, ArrayType
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Event Hub connection - reads from Databricks Secrets
# Secrets already configured: scope="vortex", keys="azure-connection-string" and "event-hub-name"
EVENTHUB_CONNECTION_STRING = dbutils.secrets.get(scope="vortex", key="azure-connection-string")
EVENTHUB_NAME = dbutils.secrets.get(scope="vortex", key="event-hub-name")

# Event Hub config for Spark
eventhub_conf = {
    "eventhubs.connectionString": sc._jvm.org.apache.spark.eventhubs.EventHubsUtils.encrypt(EVENTHUB_CONNECTION_STRING),
    "eventhubs.consumerGroup": "$Default",
    "eventhubs.startingPosition": '{"offset": "-1", "enqueuedTime": null, "isInclusive": true}'
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Schema Definition

# COMMAND ----------

# Match the schema from our traffic_generator.py
event_schema = StructType([
    StructField("event_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("timestamp", StringType(), False),
    StructField("user_id", StringType(), False),
    StructField("session_id", StringType(), False),
    StructField("user_archetype", StringType(), True),
    StructField("product_id", StringType(), True),
    StructField("product_name", StringType(), True),
    StructField("product_category", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("cart_total", DoubleType(), True),
    StructField("cart_item_count", IntegerType(), True),
    StructField("device", StringType(), True),
    StructField("browser", StringType(), True),
    StructField("geo_region", StringType(), True),
    StructField("utm_source", StringType(), True),
    StructField("session_duration_seconds", IntegerType(), True),
    StructField("page_views_before_cart", IntegerType(), True),
    StructField("is_returning_user", BooleanType(), True),
    StructField("discount_code_used", StringType(), True),
    # Abandonment-specific fields
    StructField("cart_items", ArrayType(StructType([
        StructField("id", StringType(), True),
        StructField("name", StringType(), True),
        StructField("price", DoubleType(), True)
    ])), True),
    StructField("abandonment_stage", StringType(), True),
    StructField("recovery_priority", StringType(), True),
])

# Valid values for expectations
VALID_ARCHETYPES = ["ImpulseBuyer", "WindowShopper", "PriceChecker", "CommittedBuyer", "QuickBrowser"]
VALID_EVENT_TYPES = ["add_to_cart", "checkout_start", "checkout_success", "page_view", "cart_abandoned"]
VALID_GEO_REGIONS = ["NA", "EU", "APAC", "LATAM"]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze Layer - Raw Ingestion

# COMMAND ----------

@dlt.table(
    name="bronze_events",
    comment="Raw events from Azure Event Hub - minimal transformation",
    table_properties={
        "quality": "bronze",
        "pipelines.autoOptimize.zOrderCols": "event_type,user_id"
    }
)
@dlt.expect("has_event_id", "event_id IS NOT NULL")
@dlt.expect("has_timestamp", "timestamp IS NOT NULL")
@dlt.expect("has_body", "body IS NOT NULL")
def bronze_events():
    """
    Ingest raw events from Event Hub.
    Keep the original payload for debugging and reprocessing.
    """
    return (
        spark.readStream
            .format("eventhubs")
            .options(**eventhub_conf)
            .load()
            .select(
                col("body").cast("string").alias("raw_body"),
                col("enqueuedTime").alias("ingested_at"),
                col("offset").alias("eventhub_offset"),
                col("partitionId").alias("partition_id"),
                # Parse the JSON body
                from_json(col("body").cast("string"), event_schema).alias("parsed"),
                current_timestamp().alias("processed_at")
            )
            .select(
                "raw_body",
                "ingested_at",
                "eventhub_offset",
                "partition_id",
                "processed_at",
                col("parsed.*")
            )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver Layer - Cleaned & Validated

# COMMAND ----------

@dlt.table(
    name="silver_events",
    comment="Cleaned and validated events - ready for analytics",
    table_properties={
        "quality": "silver",
        "pipelines.autoOptimize.zOrderCols": "event_type,geo_region,timestamp"
    }
)
# Core field validations
@dlt.expect_or_drop("valid_event_type", f"event_type IN {tuple(VALID_EVENT_TYPES)}")
@dlt.expect_or_drop("valid_archetype", f"user_archetype IN {tuple(VALID_ARCHETYPES)}")
@dlt.expect_or_drop("valid_geo", f"geo_region IN {tuple(VALID_GEO_REGIONS)}")
# Business rule validations
@dlt.expect("positive_cart", "cart_total >= 0")
@dlt.expect("reasonable_cart", "cart_total < 50000")
@dlt.expect("valid_session_duration", "session_duration_seconds > 0 AND session_duration_seconds < 86400")
# Suspicious activity detection (log but don't drop)
@dlt.expect("not_suspicious_amount", "cart_total < 10000")
def silver_events():
    """
    Apply data quality rules and enrich the events.
    Bad rows are dropped, suspicious rows are flagged.
    """
    return (
        dlt.read_stream("bronze_events")
        .withColumn(
            "event_timestamp",
            col("timestamp").cast("timestamp")
        )
        .withColumn(
            "event_date",
            col("event_timestamp").cast("date")
        )
        .withColumn(
            "risk_level",
            when(col("cart_total") >= 500, "high")
            .when(col("cart_total") >= 100, "medium")
            .otherwise("low")
        )
        .withColumn(
            "is_abandonment",
            col("event_type") == "cart_abandoned"
        )
        .withColumn(
            "is_conversion",
            col("event_type") == "checkout_success"
        )
        .select(
            "event_id",
            "event_type",
            "event_timestamp",
            "event_date",
            "user_id",
            "session_id",
            "user_archetype",
            "product_id",
            "product_name",
            "product_category",
            "amount",
            "cart_total",
            "cart_item_count",
            "device",
            "browser",
            "geo_region",
            "utm_source",
            "session_duration_seconds",
            "page_views_before_cart",
            "is_returning_user",
            "discount_code_used",
            "risk_level",
            "is_abandonment",
            "is_conversion",
            "cart_items",
            "abandonment_stage",
            "recovery_priority",
            "processed_at"
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold Layer - Business Aggregates

# COMMAND ----------

@dlt.table(
    name="gold_revenue_by_region",
    comment="Revenue metrics aggregated by geographic region"
)
def gold_revenue_by_region():
    """
    Track revenue and conversion by region for business reporting.
    """
    return (
        dlt.read("silver_events")
        .filter(col("is_conversion") == True)
        .groupBy("geo_region", "event_date")
        .agg(
            expr("COUNT(DISTINCT session_id) as total_purchases"),
            expr("SUM(cart_total) as total_revenue"),
            expr("AVG(cart_total) as avg_order_value"),
            expr("COUNT(DISTINCT user_id) as unique_customers")
        )
    )

# COMMAND ----------

@dlt.table(
    name="gold_abandonment_metrics",
    comment="Cart abandonment analytics for recovery optimization"
)
def gold_abandonment_metrics():
    """
    Track abandonment patterns to optimize recovery efforts.
    """
    return (
        dlt.read("silver_events")
        .filter(col("is_abandonment") == True)
        .groupBy("user_archetype", "geo_region", "event_date", "recovery_priority")
        .agg(
            expr("COUNT(*) as abandonment_count"),
            expr("SUM(cart_total) as lost_revenue"),
            expr("AVG(cart_total) as avg_abandoned_cart"),
            expr("AVG(session_duration_seconds) as avg_session_duration")
        )
    )

# COMMAND ----------

@dlt.table(
    name="gold_marketing_attribution",
    comment="Marketing channel performance metrics"
)
def gold_marketing_attribution():
    """
    Measure which channels drive conversions vs abandonments.
    """
    return (
        dlt.read("silver_events")
        .groupBy("utm_source", "event_date")
        .agg(
            expr("SUM(CASE WHEN is_conversion THEN 1 ELSE 0 END) as conversions"),
            expr("SUM(CASE WHEN is_abandonment THEN 1 ELSE 0 END) as abandonments"),
            expr("SUM(CASE WHEN is_conversion THEN cart_total ELSE 0 END) as revenue"),
            expr("SUM(CASE WHEN is_abandonment THEN cart_total ELSE 0 END) as lost_revenue"),
            expr("COUNT(DISTINCT session_id) as total_sessions")
        )
        .withColumn(
            "conversion_rate",
            col("conversions") / col("total_sessions") * 100
        )
    )

# COMMAND ----------

@dlt.table(
    name="gold_recovery_queue",
    comment="Abandoned carts prioritized for recovery actions"
)
def gold_recovery_queue():
    """
    Live queue of carts that need recovery attention.
    High-priority items should be processed first.
    """
    return (
        dlt.read("silver_events")
        .filter(col("is_abandonment") == True)
        .filter(col("cart_total") >= 25)  # Skip tiny carts
        .select(
            "event_id",
            "session_id",
            "user_id",
            "user_archetype",
            "cart_total",
            "cart_items",
            "geo_region",
            "utm_source",
            "device",
            "is_returning_user",
            "discount_code_used",
            "recovery_priority",
            "abandonment_stage",
            "event_timestamp",
            "processed_at"
        )
        .withColumn(
            "priority_score",
            when(col("recovery_priority") == "critical", 4)
            .when(col("recovery_priority") == "high", 3)
            .when(col("recovery_priority") == "medium", 2)
            .otherwise(1)
        )
        .orderBy(col("priority_score").desc(), col("cart_total").desc())
    )
