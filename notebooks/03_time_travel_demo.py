# Databricks notebook source
# MAGIC %md
# MAGIC # Delta Lake Time Travel Demo
# MAGIC 
# MAGIC Demonstrates Delta Lake's versioning capabilities for auditing,
# MAGIC debugging, and data recovery scenarios.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

CATALOG = "vortex"
SCHEMA = "main"
TABLE = "silver_events"

full_table_name = f"{CATALOG}.{SCHEMA}.{TABLE}"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. View Table History
# MAGIC 
# MAGIC Every write operation to a Delta table is tracked with metadata.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- See all changes made to the table
# MAGIC DESCRIBE HISTORY vortex.main.silver_events
# MAGIC LIMIT 20

# COMMAND ----------

# Store history in a dataframe for analysis
history_df = spark.sql(f"DESCRIBE HISTORY {full_table_name}")
display(history_df.select("version", "timestamp", "operation", "operationMetrics", "userName"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Query Historical Versions
# MAGIC 
# MAGIC Access any previous state of your data.

# COMMAND ----------

# Get the latest version number
latest_version = history_df.select("version").first()[0]
print(f"Current table version: {latest_version}")

# Query an older version (if available)
if latest_version >= 2:
    older_version = latest_version - 2
    print(f"\nQuerying version {older_version}:")
    
    old_data = spark.sql(f"""
        SELECT event_type, COUNT(*) as count, SUM(cart_total) as total_value
        FROM {full_table_name} VERSION AS OF {older_version}
        GROUP BY event_type
    """)
    display(old_data)

# COMMAND ----------

# Query by timestamp
from datetime import datetime, timedelta

# What did the data look like 1 hour ago?
one_hour_ago = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")

print(f"Querying data as of {one_hour_ago}")

historical_data = spark.sql(f"""
    SELECT user_archetype, COUNT(*) as events, SUM(cart_total) as revenue
    FROM {full_table_name} TIMESTAMP AS OF '{one_hour_ago}'
    GROUP BY user_archetype
    ORDER BY revenue DESC
""")
display(historical_data)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Compare Versions (Audit Changes)
# MAGIC 
# MAGIC Useful for debugging when metrics suddenly change.

# COMMAND ----------

if latest_version >= 1:
    # Compare current vs previous version
    current_stats = spark.sql(f"""
        SELECT 'current' as version,
               COUNT(*) as total_events,
               SUM(CASE WHEN is_conversion THEN 1 ELSE 0 END) as conversions,
               SUM(CASE WHEN is_abandonment THEN 1 ELSE 0 END) as abandonments,
               SUM(cart_total) as total_cart_value
        FROM {full_table_name}
    """)
    
    previous_stats = spark.sql(f"""
        SELECT 'previous' as version,
               COUNT(*) as total_events,
               SUM(CASE WHEN is_conversion THEN 1 ELSE 0 END) as conversions,
               SUM(CASE WHEN is_abandonment THEN 1 ELSE 0 END) as abandonments,
               SUM(cart_total) as total_cart_value
        FROM {full_table_name} VERSION AS OF {latest_version - 1}
    """)
    
    comparison = current_stats.union(previous_stats)
    display(comparison)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Restore to Previous Version
# MAGIC 
# MAGIC Undo mistakes or recover from bad data loads.

# COMMAND ----------

# MAGIC %md
# MAGIC ### ⚠️ RESTORE operation - use carefully!
# MAGIC 
# MAGIC ```sql
# MAGIC -- Restore to a specific version
# MAGIC RESTORE TABLE vortex.main.silver_events TO VERSION AS OF 5
# MAGIC 
# MAGIC -- Or restore to a timestamp
# MAGIC RESTORE TABLE vortex.main.silver_events TO TIMESTAMP AS OF '2026-01-19 10:00:00'
# MAGIC ```

# COMMAND ----------

# This is commented out to prevent accidental execution
# Uncomment and modify when you actually need to restore

# restore_version = 5  # Change this to the version you want
# spark.sql(f"RESTORE TABLE {full_table_name} TO VERSION AS OF {restore_version}")
# print(f"Table restored to version {restore_version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Clone Tables for Testing
# MAGIC 
# MAGIC Create a copy of historical data for experimentation.

# COMMAND ----------

# Create a shallow clone (references same files, no data copy)
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {CATALOG}.{SCHEMA}.silver_events_test_clone
    SHALLOW CLONE {full_table_name}
    VERSION AS OF {latest_version}
""")

print("Shallow clone created - you can experiment without affecting production data")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Vacuum Old Versions
# MAGIC 
# MAGIC Clean up old files to save storage (be careful - this removes time travel ability!)

# COMMAND ----------

# Check how much storage each version uses
spark.sql(f"DESCRIBE DETAIL {full_table_name}").select("sizeInBytes", "numFiles").show()

# COMMAND ----------

# MAGIC %md
# MAGIC ### ⚠️ VACUUM operation
# MAGIC 
# MAGIC By default, Delta keeps files for 7 days. Vacuuming removes older files.
# MAGIC 
# MAGIC ```sql
# MAGIC -- Remove files older than 7 days (default retention)
# MAGIC VACUUM vortex.main.silver_events
# MAGIC 
# MAGIC -- Remove files older than 24 hours (requires override)
# MAGIC SET spark.databricks.delta.retentionDurationCheck.enabled = false;
# MAGIC VACUUM vortex.main.silver_events RETAIN 24 HOURS
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary
# MAGIC 
# MAGIC Delta Lake Time Travel enables:
# MAGIC 
# MAGIC | Capability | Use Case |
# MAGIC |------------|----------|
# MAGIC | **VERSION AS OF** | Query exact version by number |
# MAGIC | **TIMESTAMP AS OF** | Query state at specific time |
# MAGIC | **DESCRIBE HISTORY** | Audit all changes |
# MAGIC | **RESTORE** | Undo mistakes |
# MAGIC | **CLONE** | Safe experimentation |
# MAGIC | **VACUUM** | Storage management |
