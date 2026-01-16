-- Vortex Dashboard SQL Queries
-- Create these in Databricks SQL Editor and add to a dashboard

-- ============================================
-- QUERY 1: Real-Time Revenue & Abandonment KPIs
-- ============================================
-- Name: "KPI Summary"

SELECT
    COALESCE(SUM(CASE WHEN event_type = 'checkout_success' THEN cart_total ELSE 0 END), 0) as total_revenue,
    COUNT(CASE WHEN event_type = 'checkout_success' THEN 1 END) as total_purchases,
    COUNT(CASE WHEN event_type = 'cart_abandoned' THEN 1 END) as total_abandonments,
    COALESCE(SUM(CASE WHEN event_type = 'cart_abandoned' THEN cart_total ELSE 0 END), 0) as lost_revenue,
    ROUND(
        COUNT(CASE WHEN event_type = 'checkout_success' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(CASE WHEN event_type IN ('checkout_success', 'cart_abandoned') THEN 1 END), 0),
        1
    ) as conversion_rate_pct
FROM vortex.silver_events
WHERE event_date = current_date();


-- ============================================
-- QUERY 2: Revenue by Hour (Today)
-- ============================================
-- Name: "Hourly Revenue"
-- Visualization: Line chart

SELECT
    date_trunc('hour', event_timestamp) as hour,
    SUM(CASE WHEN event_type = 'checkout_success' THEN cart_total ELSE 0 END) as revenue,
    COUNT(CASE WHEN event_type = 'checkout_success' THEN 1 END) as orders,
    SUM(CASE WHEN event_type = 'cart_abandoned' THEN cart_total ELSE 0 END) as abandoned_value
FROM vortex.silver_events
WHERE event_date = current_date()
GROUP BY 1
ORDER BY 1;


-- ============================================
-- QUERY 3: Abandonment by Archetype
-- ============================================
-- Name: "Abandonment by Customer Type"
-- Visualization: Pie chart or bar chart

SELECT
    user_archetype,
    COUNT(*) as abandonment_count,
    SUM(cart_total) as lost_revenue,
    ROUND(AVG(cart_total), 2) as avg_cart_value
FROM vortex.silver_events
WHERE event_type = 'cart_abandoned'
    AND event_date >= current_date() - INTERVAL 7 DAY
GROUP BY user_archetype
ORDER BY lost_revenue DESC;


-- ============================================
-- QUERY 4: Geographic Performance
-- ============================================
-- Name: "Revenue by Region"
-- Visualization: Map or bar chart

SELECT
    geo_region,
    SUM(CASE WHEN event_type = 'checkout_success' THEN cart_total ELSE 0 END) as revenue,
    COUNT(CASE WHEN event_type = 'checkout_success' THEN 1 END) as orders,
    COUNT(CASE WHEN event_type = 'cart_abandoned' THEN 1 END) as abandonments,
    ROUND(
        COUNT(CASE WHEN event_type = 'checkout_success' THEN 1 END) * 100.0 /
        NULLIF(COUNT(CASE WHEN event_type IN ('checkout_success', 'cart_abandoned') THEN 1 END), 0),
        1
    ) as conversion_rate
FROM vortex.silver_events
WHERE event_date >= current_date() - INTERVAL 7 DAY
GROUP BY geo_region
ORDER BY revenue DESC;


-- ============================================
-- QUERY 5: Marketing Channel Attribution
-- ============================================
-- Name: "Channel Performance"
-- Visualization: Bar chart

SELECT
    utm_source,
    COUNT(DISTINCT session_id) as sessions,
    SUM(CASE WHEN event_type = 'checkout_success' THEN cart_total ELSE 0 END) as revenue,
    COUNT(CASE WHEN event_type = 'checkout_success' THEN 1 END) as conversions,
    SUM(CASE WHEN event_type = 'cart_abandoned' THEN cart_total ELSE 0 END) as lost_revenue,
    ROUND(
        COUNT(CASE WHEN event_type = 'checkout_success' THEN 1 END) * 100.0 /
        NULLIF(COUNT(DISTINCT session_id), 0),
        2
    ) as conversion_rate
FROM vortex.silver_events
WHERE event_date >= current_date() - INTERVAL 7 DAY
GROUP BY utm_source
ORDER BY revenue DESC;


-- ============================================
-- QUERY 6: Device Performance
-- ============================================
-- Name: "Mobile vs Desktop"
-- Visualization: Donut chart

SELECT
    device,
    COUNT(DISTINCT session_id) as sessions,
    SUM(CASE WHEN event_type = 'checkout_success' THEN cart_total ELSE 0 END) as revenue,
    COUNT(CASE WHEN event_type = 'cart_abandoned' THEN 1 END) as abandonments,
    ROUND(AVG(session_duration_seconds), 0) as avg_session_seconds
FROM vortex.silver_events
WHERE event_date >= current_date() - INTERVAL 7 DAY
GROUP BY device
ORDER BY revenue DESC;


-- ============================================
-- QUERY 7: Recovery Queue Status
-- ============================================
-- Name: "Pending Recoveries"
-- Visualization: Table

SELECT
    recovery_priority,
    channel,
    COUNT(*) as pending_count,
    SUM(cart_total) as potential_revenue,
    ROUND(AVG(cart_total), 2) as avg_value
FROM vortex.recovery_actions
WHERE status = 'pending'
    AND created_at >= current_timestamp() - INTERVAL 24 HOUR
GROUP BY recovery_priority, channel
ORDER BY 
    CASE recovery_priority 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'medium' THEN 3 
        ELSE 4 
    END;


-- ============================================
-- QUERY 8: 7-Day Trend
-- ============================================
-- Name: "Weekly Trend"
-- Visualization: Area chart

SELECT
    event_date,
    SUM(CASE WHEN event_type = 'checkout_success' THEN cart_total ELSE 0 END) as revenue,
    SUM(CASE WHEN event_type = 'cart_abandoned' THEN cart_total ELSE 0 END) as abandoned,
    COUNT(CASE WHEN event_type = 'checkout_success' THEN 1 END) as orders
FROM vortex.silver_events
WHERE event_date >= current_date() - INTERVAL 7 DAY
GROUP BY event_date
ORDER BY event_date;
