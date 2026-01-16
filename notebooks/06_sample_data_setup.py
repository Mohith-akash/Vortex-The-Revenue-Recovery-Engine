# Databricks notebook source
# MAGIC %md
# MAGIC # Vortex Data Setup (Free Edition)
# MAGIC 
# MAGIC This notebook creates sample data for the dashboard.
# MAGIC Works with serverless compute - no streaming required.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Create Database

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE DATABASE IF NOT EXISTS vortex;
# MAGIC USE vortex;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Create Sample Events Table

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create the silver_events table with sample data
# MAGIC CREATE OR REPLACE TABLE vortex.silver_events (
# MAGIC     event_id STRING,
# MAGIC     event_type STRING,
# MAGIC     event_timestamp TIMESTAMP,
# MAGIC     event_date DATE,
# MAGIC     user_id STRING,
# MAGIC     session_id STRING,
# MAGIC     user_archetype STRING,
# MAGIC     product_id STRING,
# MAGIC     product_name STRING,
# MAGIC     product_category STRING,
# MAGIC     amount DOUBLE,
# MAGIC     cart_total DOUBLE,
# MAGIC     cart_item_count INT,
# MAGIC     device STRING,
# MAGIC     browser STRING,
# MAGIC     geo_region STRING,
# MAGIC     utm_source STRING,
# MAGIC     session_duration_seconds INT,
# MAGIC     page_views_before_cart INT,
# MAGIC     is_returning_user BOOLEAN,
# MAGIC     discount_code_used STRING,
# MAGIC     risk_level STRING,
# MAGIC     is_abandonment BOOLEAN,
# MAGIC     is_conversion BOOLEAN,
# MAGIC     recovery_priority STRING
# MAGIC );

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Insert Sample Data

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Insert realistic sample data for testing dashboards
# MAGIC INSERT INTO vortex.silver_events VALUES
# MAGIC -- Successful checkouts
# MAGIC ('e001', 'checkout_success', current_timestamp(), current_date(), 'u001', 's001', 'ImpulseBuyer', 'p_002', 'Nike Air Jordan 1', 'Fashion', 180.0, 180.0, 1, 'mobile', 'Chrome', 'NA', 'google', 45, 2, false, NULL, 'medium', false, true, NULL),
# MAGIC ('e002', 'checkout_success', current_timestamp(), current_date(), 'u002', 's002', 'CommittedBuyer', 'p_001', 'MacBook Pro 16', 'Electronics', 2499.0, 2499.0, 1, 'desktop', 'Safari', 'NA', 'direct', 120, 5, true, 'SAVE10', 'high', false, true, NULL),
# MAGIC ('e003', 'checkout_success', current_timestamp(), current_date(), 'u003', 's003', 'ImpulseBuyer', 'p_004', 'Sony WH-1000XM5', 'Electronics', 349.0, 349.0, 1, 'mobile', 'Chrome', 'EU', 'instagram', 30, 1, false, NULL, 'medium', false, true, NULL),
# MAGIC ('e004', 'checkout_success', current_timestamp(), current_date(), 'u004', 's004', 'CommittedBuyer', 'p_006', 'iPad Air', 'Electronics', 599.0, 599.0, 1, 'tablet', 'Safari', 'APAC', 'google', 90, 4, true, NULL, 'high', false, true, NULL),
# MAGIC ('e005', 'checkout_success', current_timestamp(), current_date(), 'u005', 's005', 'ImpulseBuyer', 'p_010', 'Stanley Tumbler 40oz', 'Home', 45.0, 45.0, 1, 'mobile', 'Chrome', 'NA', 'tiktok', 20, 1, false, NULL, 'low', false, true, NULL),
# MAGIC -- Abandonments
# MAGIC ('e006', 'cart_abandoned', current_timestamp(), current_date(), 'u006', 's006', 'WindowShopper', 'p_001', 'MacBook Pro 16', 'Electronics', 2499.0, 2499.0, 1, 'desktop', 'Chrome', 'EU', 'google', 300, 8, false, NULL, 'high', true, false, 'critical'),
# MAGIC ('e007', 'cart_abandoned', current_timestamp(), current_date(), 'u007', 's007', 'PriceChecker', 'p_004', 'Sony WH-1000XM5', 'Electronics', 349.0, 349.0, 1, 'mobile', 'Safari', 'NA', 'facebook', 180, 6, false, 'WELCOME20', 'medium', true, false, 'high'),
# MAGIC ('e008', 'cart_abandoned', current_timestamp(), current_date(), 'u008', 's008', 'WindowShopper', 'p_007', 'Lululemon Align Leggings', 'Fashion', 98.0, 98.0, 1, 'mobile', 'Chrome', 'NA', 'instagram', 240, 10, true, NULL, 'low', true, false, 'medium'),
# MAGIC ('e009', 'cart_abandoned', current_timestamp(), current_date(), 'u009', 's009', 'QuickBrowser', 'p_005', 'Protein Powder 5lb', 'Sports', 64.99, 64.99, 1, 'mobile', 'Edge', 'LATAM', 'google', 45, 2, false, NULL, 'low', true, false, 'low'),
# MAGIC ('e010', 'cart_abandoned', current_timestamp(), current_date(), 'u010', 's010', 'WindowShopper', 'p_003', 'Dyson V15 Vacuum', 'Home', 649.0, 649.0, 1, 'desktop', 'Firefox', 'EU', 'email', 360, 12, true, 'FLASH30', 'high', true, false, 'high'),
# MAGIC -- Add to cart events
# MAGIC ('e011', 'add_to_cart', current_timestamp(), current_date(), 'u011', 's011', 'ImpulseBuyer', 'p_002', 'Nike Air Jordan 1', 'Fashion', 180.0, 180.0, 1, 'mobile', 'Chrome', 'APAC', 'tiktok', 15, 1, false, NULL, 'medium', false, false, NULL),
# MAGIC ('e012', 'add_to_cart', current_timestamp(), current_date(), 'u012', 's012', 'CommittedBuyer', 'p_008', 'Instant Pot Duo', 'Home', 89.0, 89.0, 1, 'desktop', 'Chrome', 'NA', 'google', 60, 3, true, NULL, 'low', false, false, NULL);

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Create Recovery Actions Table

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE vortex.recovery_actions (
# MAGIC     action_id STRING,
# MAGIC     session_id STRING,
# MAGIC     user_id STRING,
# MAGIC     user_archetype STRING,
# MAGIC     cart_total DOUBLE,
# MAGIC     geo_region STRING,
# MAGIC     recovery_priority STRING,
# MAGIC     channel STRING,
# MAGIC     recovery_message STRING,
# MAGIC     status STRING,
# MAGIC     created_at TIMESTAMP
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO vortex.recovery_actions VALUES
# MAGIC ('a001', 's006', 'u006', 'WindowShopper', 2499.0, 'EU', 'critical', 'sms', 'Free shipping on your MacBook Pro 16!', 'pending', current_timestamp()),
# MAGIC ('a002', 's007', 'u007', 'PriceChecker', 349.0, 'NA', 'high', 'push', 'Your WELCOME20 code expires soon!', 'sent', current_timestamp()),
# MAGIC ('a003', 's010', 'u010', 'WindowShopper', 649.0, 'EU', 'high', 'email', 'Your Dyson V15 is waiting!', 'pending', current_timestamp());

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Verify Data

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Check events
# MAGIC SELECT event_type, COUNT(*) as count, SUM(cart_total) as total_value
# MAGIC FROM vortex.silver_events
# MAGIC GROUP BY event_type
# MAGIC ORDER BY count DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Check recovery actions
# MAGIC SELECT * FROM vortex.recovery_actions;

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Done!
# MAGIC 
# MAGIC Now you can run the dashboard queries. Go to:
# MAGIC 1. **SQL Editor**
# MAGIC 2. Paste queries from `04_dashboard_queries`
# MAGIC 3. **Important:** Change `vortex.main.silver_events` to `vortex.silver_events`
