# Databricks notebook source
# MAGIC %md
# MAGIC # Vortex Streaming Pipeline (Non-DLT Version)
# MAGIC 
# MAGIC Simple streaming pipeline for Free Edition - no DLT required.
# MAGIC Reads from Event Hub and writes to Delta tables.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

from pyspark.sql.functions import col, from_json, current_timestamp, when
from pyspark.sql.types import (
    StructType, StructField, StringType, 
    DoubleType, IntegerType, BooleanType, ArrayType
)

# Get secrets
connection_string = dbutils.secrets.get(scope="vortex", key="azure-connection-string")
event_hub_name = dbutils.secrets.get(scope="vortex", key="event-hub-name")

print(f"Connecting to Event Hub: {event_hub_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Event Hub Config

# COMMAND ----------

# Event Hub configuration
ehConf = {
    "eventhubs.connectionString": sc._jvm.org.apache.spark.eventhubs.EventHubsUtils.encrypt(connection_string),
    "eventhubs.consumerGroup": "$Default",
    "eventhubs.startingPosition": '{"offset": "-1", "enqueuedTime": null, "isInclusive": true}'
}

# Schema matching traffic_generator.py
event_schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("session_id", StringType(), True),
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
    StructField("cart_items", ArrayType(StructType([
        StructField("id", StringType(), True),
        StructField("name", StringType(), True),
        StructField("price", DoubleType(), True)
    ])), True),
    StructField("abandonment_stage", StringType(), True),
    StructField("recovery_priority", StringType(), True),
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Database and Tables

# COMMAND ----------

# Create database if not exists
spark.sql("CREATE DATABASE IF NOT EXISTS vortex")
spark.sql("USE vortex")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read Stream from Event Hub

# COMMAND ----------

# Read streaming data from Event Hub
raw_stream = (
    spark.readStream
    .format("eventhubs")
    .options(**ehConf)
    .load()
)

# Parse JSON and extract fields
parsed_stream = (
    raw_stream
    .select(
        col("enqueuedTime").alias("ingested_at"),
        from_json(col("body").cast("string"), event_schema).alias("data"),
        current_timestamp().alias("processed_at")
    )
    .select("ingested_at", "processed_at", "data.*")
    .withColumn("event_timestamp", col("timestamp").cast("timestamp"))
    .withColumn("event_date", col("event_timestamp").cast("date"))
    .withColumn(
        "is_abandonment",
        col("event_type") == "cart_abandoned"
    )
    .withColumn(
        "is_conversion", 
        col("event_type") == "checkout_success"
    )
    .withColumn(
        "risk_level",
        when(col("cart_total") >= 500, "high")
        .when(col("cart_total") >= 100, "medium")
        .otherwise("low")
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Delta Table

# COMMAND ----------

# Write stream to Delta table
checkpoint_path = "/tmp/vortex/checkpoints/silver_events"
table_path = "/tmp/vortex/tables/silver_events"

# Start the streaming query
query = (
    parsed_stream
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", checkpoint_path)
    .option("path", table_path)
    .trigger(processingTime="10 seconds")
    .start()
)

print("Streaming started! Run this cell and then start your traffic generator.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register Table for SQL Queries

# COMMAND ----------

# Create table reference so SQL queries work
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS vortex.silver_events
    USING DELTA
    LOCATION '{table_path}'
""")

print("Table vortex.silver_events is ready for queries!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Monitor the Stream

# COMMAND ----------

# Check stream status
# Run this to see how many records have been processed
display(query.recentProgress)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Quick Data Check

# COMMAND ----------

# See what data we have
# Run this AFTER starting the traffic generator
spark.sql("SELECT event_type, COUNT(*) as count FROM vortex.silver_events GROUP BY event_type").show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Stop Stream (when done)

# COMMAND ----------

# Run this cell to stop the streaming query
# query.stop()
# print("Stream stopped")
