# vortex_analytics (dbt)

dbt Core project on top of the DLT pipeline. It reads the `silver_events` table that `notebooks/01_dlt_pipeline.py` writes and builds one mart:

- `models/marts/gold_user_sales.sql`: transactions, revenue and average order value per shopper archetype and risk level, materialized as a Delta table.

The rest of the Gold layer (recovery queue, abandonment metrics, revenue by region, marketing attribution) is built inside the DLT pipeline itself.

Run against a Databricks profile named `vortex_analytics`:

```bash
dbt run
```
