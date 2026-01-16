# Databricks notebook source
# MAGIC %md
# MAGIC # Vortex Recovery Orchestration
# MAGIC 
# MAGIC Processes abandoned carts and triggers recovery actions.
# MAGIC Runs as a scheduled task after the DLT pipeline updates.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

from pyspark.sql.functions import col, current_timestamp, lit, udf
from pyspark.sql.types import StringType
from datetime import datetime, timedelta
import json

# Catalog and schema where DLT pipeline writes
CATALOG = "vortex"
SCHEMA = "main"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Recovery Queue

# COMMAND ----------

# Read from the gold_recovery_queue table populated by DLT
recovery_queue_df = spark.table(f"{CATALOG}.{SCHEMA}.gold_recovery_queue")

# Only process recent abandonments (last 24 hours)
cutoff_time = datetime.now() - timedelta(hours=24)
pending_recoveries = (
    recovery_queue_df
    .filter(col("event_timestamp") >= lit(cutoff_time))
    .orderBy(col("priority_score").desc(), col("cart_total").desc())
)

print(f"Found {pending_recoveries.count()} carts pending recovery")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Message Generation Logic

# COMMAND ----------

def generate_recovery_message(archetype: str, cart_total: float, main_item: str, discount_used: str) -> str:
    """
    Create personalized recovery message based on customer type.
    In production, this would call Cerebras AI for better personalization.
    """
    if archetype == "PriceChecker":
        if discount_used:
            return f"Your {main_item} is still waiting! Your {discount_used} code expires soon. Complete your ${cart_total:.2f} order now."
        return f"Price drop alert! Save 10% on your {main_item}. Your new total: ${cart_total * 0.9:.2f}"
    
    elif archetype == "WindowShopper":
        return f"Free shipping on your {main_item}! Complete your ${cart_total:.2f} order today and we'll cover delivery."
    
    elif archetype == "ImpulseBuyer":
        return f"Still thinking about that {main_item}? It's selling fast! Complete your order: ${cart_total:.2f}"
    
    elif archetype == "CommittedBuyer":
        return f"Your {main_item} is saved in your cart. Ready to finish checkout? Total: ${cart_total:.2f}"
    
    else:
        return f"Don't forget about your cart! Your {main_item} is waiting for you. Total: ${cart_total:.2f}"


# Register as UDF for Spark
generate_message_udf = udf(generate_recovery_message, StringType())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Select Channel Based on Priority

# COMMAND ----------

def select_channel(priority: str, cart_total: float) -> str:
    """
    Pick the best communication channel based on cart value and priority.
    """
    if priority == "critical":
        return "sms" if cart_total >= 500 else "push"
    elif priority == "high":
        return "push"
    else:
        return "email"

select_channel_udf = udf(select_channel, StringType())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Recovery Actions

# COMMAND ----------

from pyspark.sql.functions import element_at

# Process the queue and generate recovery actions
recovery_actions = (
    pending_recoveries
    .withColumn(
        "main_item",
        # Get first item name from cart_items array
        element_at(col("cart_items.name"), 1)
    )
    .withColumn(
        "recovery_message",
        generate_message_udf(
            col("user_archetype"),
            col("cart_total"),
            col("main_item"),
            col("discount_code_used")
        )
    )
    .withColumn(
        "channel",
        select_channel_udf(col("recovery_priority"), col("cart_total"))
    )
    .withColumn("created_at", current_timestamp())
    .withColumn("status", lit("pending"))
    .select(
        "event_id",
        "session_id",
        "user_id",
        "user_archetype",
        "cart_total",
        "main_item",
        "geo_region",
        "recovery_priority",
        "channel",
        "recovery_message",
        "status",
        "created_at"
    )
)

display(recovery_actions.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Recovery Actions Table

# COMMAND ----------

# Create table if not exists
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.recovery_actions (
        event_id STRING,
        session_id STRING,
        user_id STRING,
        user_archetype STRING,
        cart_total DOUBLE,
        main_item STRING,
        geo_region STRING,
        recovery_priority STRING,
        channel STRING,
        recovery_message STRING,
        status STRING,
        created_at TIMESTAMP,
        sent_at TIMESTAMP,
        converted_at TIMESTAMP
    )
    USING DELTA
    PARTITIONED BY (geo_region)
    TBLPROPERTIES (
        'delta.autoOptimize.optimizeWrite' = 'true',
        'delta.autoOptimize.autoCompact' = 'true'
    )
""")

# Merge new actions (avoid duplicates)
recovery_actions.createOrReplaceTempView("new_actions")

spark.sql(f"""
    MERGE INTO {CATALOG}.{SCHEMA}.recovery_actions AS target
    USING new_actions AS source
    ON target.event_id = source.event_id
    WHEN NOT MATCHED THEN
        INSERT *
""")

print("Recovery actions written successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary Metrics

# COMMAND ----------

# Show what we just processed
summary = spark.sql(f"""
    SELECT 
        recovery_priority,
        channel,
        COUNT(*) as action_count,
        SUM(cart_total) as potential_revenue,
        AVG(cart_total) as avg_cart_value
    FROM {CATALOG}.{SCHEMA}.recovery_actions
    WHERE created_at >= current_timestamp() - INTERVAL 1 HOUR
    GROUP BY recovery_priority, channel
    ORDER BY recovery_priority DESC
""")

display(summary)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cleanup Old Records

# COMMAND ----------

# Remove actions older than 7 days that were never converted
spark.sql(f"""
    DELETE FROM {CATALOG}.{SCHEMA}.recovery_actions
    WHERE created_at < current_timestamp() - INTERVAL 7 DAY
    AND status = 'pending'
""")

print("Old pending actions cleaned up")
