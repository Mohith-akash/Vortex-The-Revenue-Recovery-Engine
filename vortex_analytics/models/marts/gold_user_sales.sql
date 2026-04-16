{{ config(
    materialized='table',
    file_format='delta'
) }}

with silver_data as (
    -- We read from the source we just defined in sources.yml
    select * from {{ source('vortex_source', 'silver_events') }}
),

aggregated_data as (
    -- This is the business logic: Who buys the most?
    select
        user_archetype,
        risk_level,
        count(event_id) as total_transactions,
        sum(cart_total) as total_revenue,
        avg(cart_total) as avg_transaction_value
    from silver_data
    group by 1, 2
)

select * from aggregated_data
order by total_revenue desc