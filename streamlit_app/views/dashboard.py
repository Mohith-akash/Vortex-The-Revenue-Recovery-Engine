"""Dashboard tab: KPIs, simulated recovery activity, hourly trend."""

import random

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from common import chart_theme, get_df
from data_generator import generate_sample_data
from semantic_search import SemanticSearchEngine


def render_dashboard():
    df = get_df()

    # Header row with title and generate button
    col_t, col_b = st.columns([4, 1])
    with col_t:
        st.markdown("## ⚡ Vortex Dashboard")
    with col_b:
        if st.button("🎲 New Data"):
            st.session_state.events = generate_sample_data(1000)
            st.session_state.search_engine = SemanticSearchEngine()
            st.session_state.search_engine.index_sessions(st.session_state.events)
            st.rerun()

    st.caption(
        f"{len(df)} events • {len(df[df['event_type'] == 'cart_abandoned'])} abandoned • {len(df[df['event_type'] == 'checkout_success'])} orders"
    )

    # Calculate metrics
    revenue = df[df["event_type"] == "checkout_success"]["cart_total"].sum()
    lost = df[df["event_type"] == "cart_abandoned"]["cart_total"].sum()
    recovery = lost * 0.32
    conv = len(df[df["event_type"] == "checkout_success"])
    total = len(df[df["event_type"].isin(["checkout_success", "cart_abandoned"])])
    rate = (conv / max(1, total)) * 100
    aov = df[df["event_type"] == "checkout_success"]["cart_total"].mean() or 0

    # Compact 6-column KPIs
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("💰 Revenue", f"${revenue:,.0f}")
    c2.metric("💸 Lost", f"${lost:,.0f}")
    c3.metric("🎯 Recoverable", f"${recovery:,.0f}")
    c4.metric("📈 Conv. Rate", f"{rate:.1f}%")
    c5.metric("🛒 AOV", f"${aov:,.0f}")
    c6.metric("✅ Orders", f"{conv}")

    # Recovery Activity Log - AT TOP
    st.subheader("📧 Recovery Activity (Simulated)")

    abandoned = df[df["event_type"] == "cart_abandoned"]  # All abandoned carts
    if len(abandoned) > 0:
        channels = ["📱 SMS", "📧 Email", "🔔 Push"]
        statuses = ["✅ Delivered", "✅ Opened", "⏳ Pending", "✅ Clicked"]

        activity = []
        for _, row in abandoned.iterrows():
            channel = random.choice(channels)
            status = random.choice(statuses)
            mins_ago = random.randint(1, 60)
            # Simulate conversion: ~32% convert if delivered/opened/clicked
            converted = random.random() < 0.32 if "Pending" not in status else False

            activity.append(
                {
                    "Customer": row["user_name"],
                    "Product": row["product_name"][:20] + "..."
                    if len(row["product_name"]) > 20
                    else row["product_name"],
                    "Value": f"${row['cart_total']:,.0f}",
                    "Channel": channel,
                    "Status": status,
                    "Converted": "✅ Yes" if converted else "❌ No",
                    "Sent": f"{mins_ago}m ago",
                }
            )

        activity_df = pd.DataFrame(activity)
        st.dataframe(activity_df, hide_index=True)

        # Quick stats
        sms_count = sum(1 for a in activity if "SMS" in a["Channel"])
        email_count = sum(1 for a in activity if "Email" in a["Channel"])
        converted_count = sum(1 for a in activity if "Yes" in a["Converted"])
        conv_rate = (converted_count / len(activity) * 100) if len(activity) > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📱 SMS", sms_count)
        c2.metric("📧 Email", email_count)
        c3.metric("✅ Converted", converted_count)
        c4.metric("📈 Conv Rate", f"{conv_rate:.0f}%")

    st.markdown("---")

    # Charts - 2x2 grid with captions
    col1, col2 = st.columns(2)

    with col1:
        data = (
            df[df["event_type"] == "checkout_success"]
            .groupby("geo_region")["cart_total"]
            .sum()
            .reset_index()
        )
        top_region = data.loc[data["cart_total"].idxmax(), "geo_region"] if len(data) > 0 else "N/A"
        top_pct = (
            (data["cart_total"].max() / data["cart_total"].sum() * 100) if len(data) > 0 else 0
        )
        fig = go.Figure(
            go.Bar(
                x=data["geo_region"],
                y=data["cart_total"],
                marker=dict(
                    color=data["cart_total"],
                    colorscale=[[0, "#7c3aed"], [0.5, "#a855f7"], [1, "#ec4899"]],
                ),
            )
        )
        fig.update_layout(
            **chart_theme(), height=250, showlegend=False, title="🌍 Revenue by Region"
        )
        st.plotly_chart(fig)
        st.caption(f"**Top:** {top_region} ({top_pct:.1f}% of revenue)")

    with col2:
        data = df["event_type"].value_counts()
        abandon_pct = (data.get("cart_abandoned", 0) / data.sum() * 100) if data.sum() > 0 else 0
        success_pct = (data.get("checkout_success", 0) / data.sum() * 100) if data.sum() > 0 else 0
        fig = go.Figure(
            go.Pie(
                labels=data.index,
                values=data.values,
                hole=0.5,
                marker=dict(colors=["#7c3aed", "#ec4899", "#10b981", "#f59e0b", "#06b6d4"]),
            )
        )
        fig.update_layout(**chart_theme(), height=250, title="📊 Events")
        st.plotly_chart(fig)
        st.caption(f"**Abandoned:** {abandon_pct:.1f}% • **Checkout:** {success_pct:.1f}%")

    col3, col4 = st.columns(2)

    with col3:
        data = (
            df[df["event_type"] == "cart_abandoned"]
            .groupby("user_archetype")["cart_total"]
            .sum()
            .reset_index()
        )
        worst = data.loc[data["cart_total"].idxmax(), "user_archetype"] if len(data) > 0 else "N/A"
        worst_val = data["cart_total"].max() if len(data) > 0 else 0
        fig = go.Figure(
            go.Bar(
                x=data["user_archetype"],
                y=data["cart_total"],
                marker=dict(color=["#f87171", "#fb923c", "#fbbf24", "#a3e635", "#4ade80"]),
            )
        )
        fig.update_layout(
            **chart_theme(), height=250, showlegend=False, title="🎯 Lost by Archetype"
        )
        st.plotly_chart(fig)
        st.caption(f"**Highest loss:** {worst} (${worst_val:,.0f})")

    with col4:
        data = (
            df[df["event_type"] == "checkout_success"]
            .groupby("device")["cart_total"]
            .sum()
            .reset_index()
        )
        mobile = (
            data[data["device"] == "mobile"]["cart_total"].sum()
            if "mobile" in data["device"].values
            else 0
        )
        desktop = (
            data[data["device"] == "desktop"]["cart_total"].sum()
            if "desktop" in data["device"].values
            else 0
        )
        mobile_pct = (mobile / (mobile + desktop) * 100) if (mobile + desktop) > 0 else 0
        fig = go.Figure(
            go.Bar(
                x=data["device"],
                y=data["cart_total"],
                marker=dict(color=["#7c3aed", "#a855f7", "#c084fc"]),
            )
        )
        fig.update_layout(
            **chart_theme(), height=250, showlegend=False, title="📱 Revenue by Device"
        )
        st.plotly_chart(fig)
        st.caption(f"**Mobile share:** {mobile_pct:.1f}% of revenue")

    st.markdown("---")

    # Hourly Abandonment Trend (Simulated baseline pattern)
    st.subheader("📈 Hourly Abandonment Trend: Simulated Baseline")
    st.caption(
        "Simulated baseline pattern (not a real forecast). "
        "Past 24h is a deterministic diurnal curve seeded on the generated data; "
        "the next 6h is a 7-point rolling average of that curve."
    )

    # Simulate hourly pattern (past 24 hours + 6 hour forecast)
    hours = list(range(-24, 7))
    base_rate = len(df[df["event_type"] == "cart_abandoned"]) / 24

    # Deterministic diurnal pattern (no randomness): higher during day, lower at night
    historical = []
    for h in hours[:24]:
        hour_of_day = (h % 24 + 24) % 24  # Convert to 0-23
        # Peak during 10am-8pm, low at night
        if 10 <= hour_of_day <= 20:
            multiplier = 1.2
        elif 6 <= hour_of_day < 10 or 20 < hour_of_day <= 23:
            multiplier = 0.8
        else:
            multiplier = 0.4
        historical.append(int(base_rate * multiplier))

    # Honest "forecast": simple 7-point rolling average of the historical curve
    # extended forward. No randomness, no fake ML, just a moving average.
    hist_series = pd.Series(historical)
    rolling = hist_series.rolling(window=7, min_periods=1).mean()
    last_avg = float(rolling.iloc[-1])
    forecast = [int(round(last_avg))] * 6
    # Smooth toward the rolling mean of the tail
    tail_mean = float(hist_series.tail(7).mean())
    forecast = [int(round((last_avg + tail_mean) / 2))] * 6

    hourly_pattern = historical + forecast

    # Create the chart
    fig = go.Figure()

    # Historical data (past 24 hours)
    fig.add_trace(
        go.Scatter(
            x=hours[:24],
            y=hourly_pattern[:24],
            mode="lines+markers",
            name="Historical",
            line=dict(color="#7c3aed", width=2),
            marker=dict(size=6),
        )
    )

    # Projection (next 6 hours): rolling-average extension, not a real forecast
    fig.add_trace(
        go.Scatter(
            x=hours[24:],
            y=hourly_pattern[24:],
            mode="lines+markers",
            name="Rolling-avg projection",
            line=dict(color="#ec4899", width=2, dash="dash"),
            marker=dict(size=8, symbol="diamond"),
        )
    )

    # Add "now" line
    fig.add_vline(x=0, line_dash="dot", line_color="#10b981", annotation_text="Now")

    fig.update_layout(
        **chart_theme(),
        height=280,
        xaxis_title="Hours",
        yaxis_title="Abandoned Carts",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig)

    # Projection insight (rolling-average based, not a real forecast)
    forecast_total = sum(hourly_pattern[24:])
    col1, col2, col3 = st.columns(3)
    col1.metric("📉 Next 6h (rolling avg)", f"{forecast_total} carts")
    col2.metric("💰 At Risk", f"${forecast_total * (df['cart_total'].mean() or 150):,.0f}")
    col3.metric(
        "🎯 Recoverable", f"${forecast_total * (df['cart_total'].mean() or 150) * 0.32:,.0f}"
    )
