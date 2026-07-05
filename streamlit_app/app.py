"""
Vortex - The Revenue Recovery Engine
Vibrant dashboard with recovery timing analytics.
"""

import random
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

from ai_recovery import (  # noqa: E402
    AIRecoveryEngine,
    RecoveryContext,
    create_recovery_context_from_event,
)
from data_generator import ARCHETYPES, PRODUCTS, generate_sample_data  # noqa: E402
from semantic_search import SemanticSearchEngine  # noqa: E402
from styles import inject_css  # noqa: E402

st.set_page_config(
    page_title="Vortex", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed"
)

inject_css()

# Session state
if "events" not in st.session_state:
    st.session_state.events = generate_sample_data(1000)
if "search_engine" not in st.session_state:
    st.session_state.search_engine = SemanticSearchEngine()
    st.session_state.search_engine.index_sessions(st.session_state.events)
if "recovery_engine" not in st.session_state:
    st.session_state.recovery_engine = AIRecoveryEngine()


def get_df():
    return pd.DataFrame(st.session_state.events)


def chart_theme():
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#a5a5c0", "size": 12},
        "margin": {"l": 50, "r": 30, "t": 40, "b": 50},
        "xaxis": {"gridcolor": "rgba(124,58,237,0.1)", "tickfont": {"color": "#8b8ba7"}},
        "yaxis": {"gridcolor": "rgba(124,58,237,0.1)", "tickfont": {"color": "#8b8ba7"}},
    }


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
    st.subheader("📈 Hourly Abandonment Trend — Simulated Baseline")
    st.caption(
        "Simulated baseline pattern (not a real forecast). "
        "Past 24h is a deterministic diurnal curve seeded on the generated data; "
        "the next 6h is a 7-point rolling average of that curve."
    )

    # Simulate hourly pattern (past 24 hours + 6 hour forecast)
    hours = list(range(-24, 7))
    base_rate = len(df[df["event_type"] == "cart_abandoned"]) / 24

    # Deterministic diurnal pattern (no randomness) — higher during day, lower at night
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
    # extended forward. No randomness, no fake ML — just a moving average.
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

    # Projection (next 6 hours) — rolling-average extension, not a real forecast
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


def render_recovery_analytics():
    """Recovery timing analytics based on actual data."""
    df = get_df()

    st.markdown("## ⏱️ Recovery Analytics")

    # Calculate actual values from the data
    abandoned = df[df["event_type"] == "cart_abandoned"]

    total_lost = abandoned["cart_total"].sum()
    num_abandoned = len(abandoned)
    avg_cart = abandoned["cart_total"].mean() if len(abandoned) > 0 else 0

    # Calculate potential recovery at different timings (based on rates)
    recovery_5min = total_lost * 0.32
    recovery_1hr = total_lost * 0.24
    recovery_24hr = total_lost * 0.07
    recovery_none = total_lost * 0.02

    # Dynamic KPIs based on actual data
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💸 Total Lost", f"${total_lost:,.0f}")
    c2.metric("🎯 Recoverable @5min", f"${recovery_5min:,.0f}")
    c3.metric("⏱️ Recoverable @1hr", f"${recovery_1hr:,.0f}")
    c4.metric("🕐 Recoverable @24hr", f"${recovery_24hr:,.0f}")
    c5.metric("💀 No Action", f"${recovery_none:,.0f}")

    st.caption(f"Based on **{num_abandoned}** abandoned carts with avg value **${avg_cart:,.0f}**")

    st.markdown("---")

    # Key Insights with actual values
    st.subheader("🔥 Key Insights (Your Data)")

    col1, col2, col3 = st.columns(3)

    with col1:
        opportunity = recovery_5min - recovery_none
        st.success(f"""
        **⚡ Recovery Opportunity**

        From your **${total_lost:,.0f}** in lost revenue:
        - At 5 min: **${recovery_5min:,.0f}** recoverable
        - No action: only ${recovery_none:,.0f}

        **Gap: ${opportunity:,.0f}** you're leaving behind!
        """)

    with col2:
        per_cart_5min = (avg_cart * 0.32) if avg_cart > 0 else 0
        per_cart_none = (avg_cart * 0.02) if avg_cart > 0 else 0
        st.info(f"""
        **💰 Per Abandoned Cart**

        With avg cart value **${avg_cart:,.0f}**:
        - Expected at 5 min: **${per_cart_5min:,.0f}**
        - Expected no action: ${per_cart_none:,.0f}

        **${per_cart_5min - per_cart_none:.0f} extra** per cart recovered!
        """)

    with col3:
        carts_recoverable = int(num_abandoned * 0.32)
        st.warning(f"""
        **📊 Volume Impact**

        Of **{num_abandoned}** abandoned carts:
        - 5 min response: **{carts_recoverable}** will convert
        - No action: only {int(num_abandoned * 0.02)}

        That's **{carts_recoverable - int(num_abandoned * 0.02)} extra orders**!
        """)

    st.markdown("---")

    # Timing simulation chart using actual avg cart value
    st.subheader("📈 Projected Recovery by Timing")
    st.caption(f"Simulated recovery based on your avg cart value of ${avg_cart:,.0f}")

    timing_data = pd.DataFrame(
        {
            "Timing": [
                "5 min",
                "30 min",
                "1 hr",
                "3 hr",
                "6 hr",
                "12 hr",
                "24 hr",
                "48 hr",
                "None",
            ],
            "Rate": [32, 28, 24, 18, 14, 10, 7, 4, 2],
        }
    )
    timing_data["Revenue"] = (timing_data["Rate"] / 100) * total_lost
    timing_data["Carts"] = (timing_data["Rate"] / 100 * num_abandoned).astype(int)

    colors = [
        "#10b981",
        "#22c55e",
        "#84cc16",
        "#eab308",
        "#f59e0b",
        "#f97316",
        "#ef4444",
        "#dc2626",
        "#991b1b",
    ]

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure(
            go.Bar(
                x=timing_data["Timing"],
                y=timing_data["Revenue"],
                marker=dict(color=colors),
                text=timing_data["Revenue"].apply(lambda x: f"${x:,.0f}"),
                textposition="outside",
            )
        )
        fig.update_layout(
            **chart_theme(), height=280, showlegend=False, title="💰 Revenue Recoverable"
        )
        st.plotly_chart(fig)

    with col2:
        fig = go.Figure(
            go.Bar(
                x=timing_data["Timing"],
                y=timing_data["Carts"],
                marker=dict(color=colors),
                text=timing_data["Carts"],
                textposition="outside",
            )
        )
        fig.update_layout(
            **chart_theme(), height=280, showlegend=False, title="🛒 Carts Recoverable"
        )
        st.plotly_chart(fig)

    st.markdown("---")

    # Priority breakdown from actual data
    st.subheader("🎯 Abandoned Carts by Priority")

    if len(abandoned) > 0 and "recovery_priority" in abandoned.columns:
        priority_data = (
            abandoned.groupby("recovery_priority")
            .agg(count=("cart_total", "count"), value=("cart_total", "sum"))
            .reset_index()
        )

        col1, col2 = st.columns(2)

        with col1:
            fig = go.Figure(
                go.Bar(
                    x=priority_data["recovery_priority"],
                    y=priority_data["count"],
                    marker=dict(color=["#ef4444", "#f59e0b", "#eab308", "#22c55e"]),
                )
            )
            fig.update_layout(**chart_theme(), height=250, showlegend=False, title="# of Carts")
            st.plotly_chart(
                fig,
            )

        with col2:
            fig = go.Figure(
                go.Bar(
                    x=priority_data["recovery_priority"],
                    y=priority_data["value"],
                    marker=dict(color=["#ef4444", "#f59e0b", "#eab308", "#22c55e"]),
                )
            )
            fig.update_layout(
                **chart_theme(), height=250, showlegend=False, title="$ Value at Risk"
            )
            st.plotly_chart(
                fig,
            )
    else:
        st.info("No priority data available")

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════════
    # 📱 Channel Effectiveness
    # ═══════════════════════════════════════════════════════════════════════════

    st.subheader("📱 Channel Effectiveness by Timing (Industry Benchmarks)")
    st.caption("""
    **What this shows:** Recovery rate comparison between SMS, Push Notifications, and Email at different timings.
    Based on industry benchmark data.
    """)

    channel_data = pd.DataFrame(
        {
            "Timing": [
                "5 min",
                "5 min",
                "5 min",
                "1 hour",
                "1 hour",
                "1 hour",
                "24 hours",
                "24 hours",
                "24 hours",
            ],
            "Channel": ["SMS", "Push", "Email", "SMS", "Push", "Email", "SMS", "Push", "Email"],
            "Rate": [35, 30, 28, 22, 18, 26, 5, 3, 12],
        }
    )

    fig = px.bar(
        channel_data,
        x="Timing",
        y="Rate",
        color="Channel",
        barmode="group",
        color_discrete_map={"SMS": "#7c3aed", "Push": "#ec4899", "Email": "#06b6d4"},
    )
    fig.update_layout(
        **chart_theme(),
        height=350,
        xaxis_title="⏱️ Time After Abandonment",
        yaxis_title="📈 Recovery Rate (%)",
        legend_title="📱 Channel",
    )
    st.plotly_chart(fig)

    st.markdown("---")

    # ROI Calculator
    st.subheader("🧮 ROI Calculator — Estimate Your Potential Revenue Gain")
    st.caption("""
    Adjust the sliders to match your store's metrics and see how much more revenue you could recover
    by optimizing your message timing.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📊 Your Store Metrics**")

        daily_abandons = st.slider(
            "Daily Abandoned Carts",
            min_value=100,
            max_value=5000,
            value=500,
            help="How many carts are abandoned each day on your store",
        )
        st.caption("Number of customers who add items to cart but leave without buying each day")

        avg_cart = st.slider(
            "Average Cart Value ($)",
            min_value=50,
            max_value=500,
            value=150,
            help="Average dollar value of items in abandoned carts",
        )
        st.caption("The typical dollar amount in a customer's cart when they abandon")

        current_delay = st.selectbox(
            "Current Message Delay",
            options=["No messages", "48 hours", "24 hours", "6 hours", "1 hour", "5 minutes"],
            help="How long after abandonment do you currently send recovery messages?",
        )
        st.caption("When your current system sends cart recovery messages after abandonment")

    with col2:
        st.markdown("**💰 Revenue Comparison**")

        delay_rates = {
            "No messages": 2,
            "48 hours": 4,
            "24 hours": 7,
            "6 hours": 14,
            "1 hour": 24,
            "5 minutes": 32,
        }
        current_rate = delay_rates[current_delay]
        optimal_rate = 32  # Best rate at 5 minutes

        current_revenue = daily_abandons * avg_cart * (current_rate / 100)
        optimal_revenue = daily_abandons * avg_cart * (optimal_rate / 100)
        improvement = optimal_revenue - current_revenue

        st.metric("CURRENT DAILY RECOVERY", f"${current_revenue:,.0f}", f"{current_rate}% rate")
        st.caption(f"Revenue you recover today with {current_delay} response time")

        st.metric("OPTIMAL RECOVERY (5 MIN)", f"${optimal_revenue:,.0f}", f"{optimal_rate}% rate")
        st.caption("Revenue you could recover by messaging within 5 minutes")

        st.metric(
            "POTENTIAL DAILY GAIN",
            f"${improvement:,.0f}",
            f"↑ {((optimal_rate / max(1, current_rate)) - 1) * 100:.0f}%",
        )
        st.caption("Extra revenue per day by switching to 5-minute response time")


def render_try_it():
    st.markdown("## 🎮 Interactive Demo")

    st.info(
        "**⚡ Experience AI-powered cart recovery in action!** Fill in your details, add a product to cart, then abandon it to see the AI generate a personalized recovery message."
    )

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("🛒 Simulate Your Shopping Session")

        name = st.text_input("👤 Your Name", placeholder="e.g., Sarah Johnson")
        archetype = st.selectbox("🧠 Shopping Behavior", list(ARCHETYPES.keys()))
        st.caption(f"*{ARCHETYPES[archetype]['description']}*")

        product = st.selectbox(
            "📦 Product", PRODUCTS, format_func=lambda p: f"{p['name']} — ${p['price']:,.0f}"
        )

        st.markdown("---")

        st.markdown("**Actions:**")
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            add = st.button("🛒 Add to Cart")
        with btn_col2:
            buy = st.button("✅ Checkout")
        with btn_col3:
            abandon = st.button("🚪 Abandon", type="primary")

        # Session status
        st.markdown("---")
        st.markdown("**📊 Session Summary:**")
        st.markdown(f"""
        | Detail | Value |
        |--------|-------|
        | Customer | {name or "(enter name)"} |
        | Type | {archetype} |
        | Product | {product["name"]} |
        | Cart Value | ${product["price"]:,.0f} |
        | Discount | {"SAVE10" if product["price"] > 100 else "None"} |
        """)

    with col2:
        st.subheader("🤖 AI Recovery Response")

        if abandon and name:
            ctx = RecoveryContext(
                customer_name=name,
                customer_archetype=archetype,
                product_name=product["name"],
                product_category=product["category"],
                cart_total=product["price"],
                abandonment_stage="cart",
                is_returning=False,
                discount_code="SAVE10" if product["price"] > 100 else None,
                utm_source="demo",
                session_duration=180,
                page_views=5,
            )
            with st.spinner("🧠 AI thinking..."):
                result = st.session_state.recovery_engine.generate_message(ctx)

            # Show result with styling
            source = (
                "🤖 AI Generated (Cerebras)"
                if result["is_ai_generated"]
                else "📝 Template Fallback"
            )
            channel = result["channel"].upper()

            st.success(f"**{source}**")
            st.markdown(f"**Channel:** {channel}")
            st.markdown("**Message:**")
            st.info(f'"{result["message"]}"')

            with st.expander("📋 Technical Details"):
                st.json(
                    {
                        "customer": name,
                        "archetype": archetype,
                        "product": product["name"],
                        "price": product["price"],
                        "model": result.get("model", "template"),
                        "channel": result["channel"],
                        "ai_generated": result["is_ai_generated"],
                    }
                )

            # Webhook Simulator
            st.markdown("---")
            st.markdown("**📡 Webhook Delivery Simulation:**")

            webhook_log = st.empty()

            # Simulate webhook delivery
            logs = [
                f"🔄 Preparing {channel} message...",
                f"📤 Sending to {channel.lower()} gateway...",
                f"✅ Message queued - ID: msg_{random.randint(10000, 99999)}",
                f"📱 Delivered to {name}'s device",
                "👁️ Message opened!" if random.random() > 0.3 else "⏳ Awaiting open...",
            ]

            log_text = ""
            for log in logs:
                log_text += f"```\n{log}\n```\n"
                webhook_log.markdown(log_text)
                time.sleep(0.4)

            # Delivery status metrics
            delivery_time = random.randint(150, 800)
            open_rate = random.randint(35, 68)
            col1, col2 = st.columns(2)
            col1.metric("📡 Delivery Time", f"{delivery_time}ms")
            col2.metric("📊 Channel Open Rate", f"{open_rate}%")

        elif buy and name:
            st.success("🎉 **Order Confirmed!**")
            st.markdown(f"**{product['name']}** purchased for **${product['price']:,.0f}**")
            st.balloons()

        elif add and name:
            st.info(
                f"🛒 Added **{product['name']}** to cart. Now click **Abandon** to trigger recovery!"
            )

        elif (add or buy or abandon) and not name:
            st.warning("⚠️ Please enter your name first")

        else:
            st.markdown("""
            **How it works:**
            1. Enter your name
            2. Select a shopping behavior type
            3. Choose a product
            4. Click **🚪 Abandon** to trigger AI recovery

            The AI will generate a personalized message based on your profile!
            """)


def render_recovery_queue():
    st.markdown("## 🤖 Recovery Queue")

    st.info(
        "**Priority-based recovery queue.** Click 'Generate' to create personalized AI recovery messages for each abandoned cart."
    )

    df = get_df()
    abandoned = df[df["event_type"] == "cart_abandoned"]

    if abandoned.empty:
        st.warning("No abandoned carts in queue")
        return

    # Queue stats
    c1, c2, c3, c4, c5 = st.columns(5)
    critical = len(abandoned[abandoned["recovery_priority"] == "critical"])
    high = len(abandoned[abandoned["recovery_priority"] == "high"])
    medium = len(abandoned[abandoned["recovery_priority"] == "medium"])
    low = len(abandoned[abandoned["recovery_priority"] == "low"])
    total_val = abandoned["cart_total"].sum()

    c1.metric(
        "🔴 Critical",
        critical,
        f"${abandoned[abandoned['recovery_priority'] == 'critical']['cart_total'].sum():,.0f}",
    )
    c2.metric("🟠 High", high)
    c3.metric("🟡 Medium", medium)
    c4.metric("🟢 Low", low)
    c5.metric("💰 Total Value", f"${total_val:,.0f}")

    st.markdown("---")

    # Filter
    col1, col2 = st.columns([1, 3])
    with col1:
        filt = st.multiselect(
            "Filter Priority", ["critical", "high", "medium", "low"], default=["critical", "high"]
        )
    with col2:
        st.caption(f"Showing {len(abandoned[abandoned['recovery_priority'].isin(filt)])} carts")

    if filt:
        abandoned = abandoned[abandoned["recovery_priority"].isin(filt)]

    st.markdown("---")

    # Queue items as cards
    for _, row in abandoned.head(10).iterrows():
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
            row["recovery_priority"], "⚪"
        )
        session_id = row["session_id"]

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.markdown(f"**{icon} {row['user_name']}**")
            st.caption(f"{row['user_archetype']} • {row['geo_region']}")

        with col2:
            st.markdown(f"**{row['product_name']}**")
            st.caption(f"${row['cart_total']:,.0f} • {row['device']}")

        with col3:
            if st.button(
                "🤖 Generate",
                key=f"g_{session_id}",
            ):
                ctx = create_recovery_context_from_event(row.to_dict())
                res = st.session_state.recovery_engine.generate_message(ctx)
                st.session_state[f"m_{session_id}"] = res

        msg_key = f"m_{session_id}"
        if msg_key in st.session_state:
            msg_data = st.session_state[msg_key]
            st.success(f'📱 **{msg_data["channel"].upper()}**: "{msg_data["message"]}"')

        st.markdown("---")

    # Priority Explainability Section
    st.subheader("🧠 Priority Explainability")
    st.caption("Why carts are prioritized the way they are")

    st.markdown("""
    | Factor | Weight | Impact |
    |--------|--------|--------|
    | **Cart Value ≥ $500** | +3 pts | High value = critical priority |
    | **Cart Value ≥ $200** | +2 pts | Medium-high value |
    | **Cart Value ≥ $50** | +1 pt | Standard cart |
    | **Returning Customer** | +2 pts | Known buyers convert better |
    | **CommittedBuyer/ImpulseBuyer** | +1 pt | High-intent archetypes |
    | **WindowShopper** | -1 pt | Low conversion likelihood |

    **Priority Thresholds:** Critical ≥ 4 pts, High ≥ 2 pts, Medium ≥ 1 pt, Low = 0 pts
    """)

    # Sample explanation for top cart
    if len(abandoned) > 0:
        top_cart = abandoned.iloc[0]
        score = 0
        reasons = []

        if top_cart["cart_total"] >= 500:
            score += 3
            reasons.append(f"💰 High value: ${top_cart['cart_total']:,.0f}")
        elif top_cart["cart_total"] >= 200:
            score += 2
            reasons.append(f"💵 Medium value: ${top_cart['cart_total']:,.0f}")

        if top_cart.get("user_archetype") in ["CommittedBuyer", "ImpulseBuyer"]:
            score += 1
            reasons.append(f"🎯 High-intent: {top_cart['user_archetype']}")
        elif top_cart.get("user_archetype") == "WindowShopper":
            score -= 1
            reasons.append(f"👀 Low-intent: {top_cart['user_archetype']}")

        st.info(
            f"**Example:** {top_cart['user_name']}'s cart → Priority **{top_cart.get('recovery_priority', 'unknown').upper()}** because: {' + '.join(reasons)}"
        )


def render_search():
    st.markdown("## 🔍 Semantic Search")

    st.info(
        "**AI-powered natural language search** using Voyage AI embeddings. Search for customer sessions using plain English descriptions."
    )

    engine = st.session_state.search_engine

    # Sample queries
    st.markdown("**💡 Try these queries:**")
    sample_queries = [
        "high value abandoned electronics",
        "mobile users from West",
        "impulse buyers with expensive carts",
        "window shoppers who left",
    ]
    query_cols = st.columns(4)
    selected_sample = None
    for i, sq in enumerate(sample_queries):
        with query_cols[i]:
            if st.button(sq, key=f"sample_{i}"):
                selected_sample = sq

    st.markdown("---")

    query = st.text_input(
        "🔎 Search Query",
        value=selected_sample or "",
        placeholder="Describe the sessions you're looking for...",
    )

    if query:
        with st.spinner("🧠 Searching with AI embeddings..."):
            results = engine.search(query, top_k=8)

        if results:
            st.subheader(f"📊 Found {len(results)} matching sessions")

            for r in results:
                d = r["data"]
                similarity = r["similarity"]

                # Color based on similarity
                if similarity > 0.8:
                    match_color = "🟢"
                elif similarity > 0.6:
                    match_color = "🟡"
                else:
                    match_color = "🟠"

                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.markdown(f"**{d.get('user_name', 'Unknown')}**")
                    st.caption(f"{d.get('user_archetype')} • {d.get('geo_region')}")

                with col2:
                    st.markdown(f"**{d.get('product_name', 'Unknown')}**")
                    status = "🚪 Abandoned" if d.get("is_abandonment") else "✅ Converted"
                    st.caption(f"${d.get('cart_total', 0):,.0f} • {status}")

                with col3:
                    st.markdown(f"{match_color} **{similarity:.0%}**")
                    st.caption("Match")

                st.markdown("---")
        else:
            st.warning("No results found. Try a different query.")

    # Session stats
    st.subheader("📈 Session Analytics")
    patterns = engine.analyze_patterns()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📊 Total Sessions", patterns.get("total_sessions", 0))
    c2.metric("🚪 Abandoned", patterns.get("by_outcome", {}).get("abandoned", 0))
    c3.metric("✅ Converted", patterns.get("by_outcome", {}).get("converted", 0))

    if patterns.get("total_sessions", 0) > 0:
        conv_rate = (
            patterns.get("by_outcome", {}).get("converted", 0)
            / patterns.get("total_sessions", 1)
            * 100
        )
        c4.metric("📈 Conv Rate", f"{conv_rate:.1f}%")


def render_architecture():
    st.markdown("## 🏗️ System Architecture")

    # Tech Stack Table
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔧 Technology Stack")
        st.markdown("""
| Layer | Technology | Purpose |
|-------|------------|---------|
| **Data Ingestion** | Azure Event Hub | Real-time event streaming |
| **Processing** | Databricks | Distributed computing |
| **Storage** | Delta Lake | ACID transactions, time travel |
| **Data Quality** | DLT Expectations | Schema validation, quality checks |
| **Transformation** | dbt Core | SQL-based data modeling |
| **LLM** | Cerebras Llama 3.1 8B | AI-powered recovery messages |
| **Embeddings** | Voyage AI | Semantic search vectors |
| **Frontend** | Streamlit | Interactive dashboards |
| **Charts** | Plotly | Dynamic visualizations |
| **Language** | Python 3.11+ | Core development |
| **CI/CD** | GitHub Actions | Automated testing & deployment |
        """)

    with col2:
        st.subheader("✨ Key Features")
        st.markdown("""
| Feature | Description |
|---------|-------------|
| **Real-time Streaming** | Sub-second event ingestion from Event Hub |
| **Bronze/Silver/Gold** | DLT medallion architecture |
| **Time Travel** | Query historical data versions |
| **AI Recovery** | Context-aware personalized messages |
| **Semantic Search** | Natural language session queries |
| **Recovery Analytics** | Timing impact visualization |
| **Multi-channel** | SMS, Email, Push orchestration |
| **Customer Archetypes** | Behavioral segmentation |
| **Priority Scoring** | Cart value-based prioritization |
| **Interactive Demo** | Try the recovery system live |
        """)

    st.markdown("---")

    # Skills Demonstrated
    st.subheader("🎯 Skills Demonstrated")

    skills = {
        "Data Engineering": [
            "Event-driven architecture",
            "ETL/ELT pipelines",
            "Delta Lake",
            "DLT",
            "Streaming",
        ],
        "Analytics Engineering": [
            "Medallion architecture",
            "Data modeling",
            "KPI design",
            "A/B metrics",
        ],
        "AI/ML Engineering": [
            "LLM integration",
            "Prompt engineering",
            "Embeddings",
            "Semantic search",
        ],
        "Software Engineering": ["Python", "API design", "CI/CD", "Modular code"],
        "Data Visualization": ["Plotly", "Streamlit", "Dashboard design"],
        "Cloud & DevOps": [
            "Azure Event Hub",
            "Databricks",
            "GitHub Actions",
            "Environment management",
        ],
    }

    cols = st.columns(3)
    for i, (category, items) in enumerate(skills.items()):
        with cols[i % 3]:
            st.markdown(f"**{category}**")
            for item in items:
                st.markdown(f"- {item}")

    st.markdown("---")

    # Data Flow
    st.subheader("🔄 Data Flow")
    st.markdown("""
    ```
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   E-commerce    │───▶│  Azure Event    │───▶│   Databricks    │
    │    Events       │    │      Hub        │    │   (Bronze)      │
    └─────────────────┘    └─────────────────┘    └────────┬────────┘
                                                           │
    ┌─────────────────┐    ┌─────────────────┐    ┌────────▼────────┐
    │   Streamlit     │◀───│   Delta Lake    │◀───│    DLT Silver   │
    │   Dashboard     │    │   (Gold Layer)  │    │   (Cleaned)     │
    └────────┬────────┘    └─────────────────┘    └─────────────────┘
             │
    ┌────────▼────────┐    ┌─────────────────┐
    │   Cerebras AI   │───▶│  Recovery SMS/  │
    │   (Messages)    │    │  Email/Push     │
    └─────────────────┘    └─────────────────┘
    ```
    """)

    # Libraries Used
    st.subheader("📦 Libraries & Dependencies")
    libs = [
        "streamlit",
        "pandas",
        "plotly",
        "numpy",
        "faker",
        "cerebras-sdk",
        "voyageai",
        "python-dotenv",
        "azure-eventhub",
    ]
    st.markdown(" • ".join([f"`{lib}`" for lib in libs]))


def render_ab_testing():
    """A/B Testing dashboard for recovery message experiments."""
    st.markdown("## 🧪 A/B Testing")

    st.info(
        "**Message Experiment Dashboard** - Compare recovery message variants and identify winners with statistical significance."
    )

    df = get_df()
    abandoned = df[df["event_type"] == "cart_abandoned"]
    total_abandoned = len(abandoned)

    if total_abandoned == 0:
        st.warning("No abandoned carts to run experiments on")
        return

    # Simulate A/B test data based on current data (changes with new data)
    random.seed(total_abandoned + int(abandoned["cart_total"].sum()) % 1000)  # Data-dependent seed

    # Create experiment scenarios with slight variations based on data
    def vary(base, variance=0.05):
        return base * (1 + random.uniform(-variance, variance))

    experiments = {
        "Urgency vs Friendly": {
            "variant_a": {
                "name": "🔥 Urgency",
                "message": "Your cart expires in 1 hour! Complete now →",
                "sends": int(total_abandoned * 0.5),
                "opens": vary(0.42),
                "clicks": vary(0.18),
                "conversions": vary(0.085),
            },
            "variant_b": {
                "name": "💚 Friendly",
                "message": "Hey! Your items are waiting. No rush! 😊",
                "sends": int(total_abandoned * 0.5),
                "opens": vary(0.38),
                "clicks": vary(0.15),
                "conversions": vary(0.072),
            },
        },
        "Discount vs Free Shipping": {
            "variant_a": {
                "name": "💰 10% Off",
                "message": "Get 10% off your cart - use code SAVE10!",
                "sends": int(total_abandoned * 0.5),
                "opens": vary(0.45),
                "clicks": vary(0.22),
                "conversions": vary(0.095),
            },
            "variant_b": {
                "name": "🚚 Free Ship",
                "message": "Free shipping on your order - limited time!",
                "sends": int(total_abandoned * 0.5),
                "opens": vary(0.40),
                "clicks": vary(0.19),
                "conversions": vary(0.082),
            },
        },
        "SMS vs Email": {
            "variant_a": {
                "name": "📱 SMS",
                "message": "Quick checkout: tap to complete →",
                "sends": int(total_abandoned * 0.5),
                "opens": vary(0.68),
                "clicks": vary(0.28),
                "conversions": vary(0.110),
            },
            "variant_b": {
                "name": "📧 Email",
                "message": "Your cart is saved - complete your order",
                "sends": int(total_abandoned * 0.5),
                "opens": vary(0.35),
                "clicks": vary(0.12),
                "conversions": vary(0.065),
            },
        },
    }

    # Experiment selector
    selected_exp = st.selectbox("📊 Select Experiment", list(experiments.keys()))
    exp = experiments[selected_exp]

    st.markdown("---")

    # Variant comparison cards
    col1, col2 = st.columns(2)

    for col, (_variant_key, variant) in zip([col1, col2], exp.items(), strict=False):
        with col:
            st.subheader(variant["name"])
            st.caption(f'"{variant["message"]}"')

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📤 Sent", variant["sends"])
            m2.metric("👁️ Opens", f"{variant['opens'] * 100:.1f}%")
            m3.metric("👆 Clicks", f"{variant['clicks'] * 100:.1f}%")
            m4.metric("✅ Conv", f"{variant['conversions'] * 100:.1f}%")

    st.markdown("---")

    # Statistical Analysis
    st.subheader("📈 Statistical Analysis")

    a = exp["variant_a"]
    b = exp["variant_b"]

    # Calculate lift
    conv_lift = ((a["conversions"] - b["conversions"]) / b["conversions"]) * 100
    winner = "A" if a["conversions"] > b["conversions"] else "B"
    winner_name = a["name"] if winner == "A" else b["name"]

    n = a["sends"]
    p1, p2 = a["conversions"], b["conversions"]
    se = ((p1 * (1 - p1) / n) + (p2 * (1 - p2) / n)) ** 0.5
    z_score = abs(p1 - p2) / se if se > 0 else 0
    is_significant = z_score > 1.96  # 95% confidence

    col1, col2, col3 = st.columns(3)

    with col1:
        if conv_lift > 0:
            st.success(f"**Variant A** is winning by **+{abs(conv_lift):.1f}%**")
        else:
            st.success(f"**Variant B** is winning by **+{abs(conv_lift):.1f}%**")

    with col2:
        if is_significant:
            st.success(f"**95% Confident** (z={z_score:.2f})")
        else:
            st.warning(f"**Not Significant** (z={z_score:.2f})")

    with col3:
        winner_revenue = int(
            abandoned["cart_total"].sum()
            * (a["conversions"] if winner == "A" else b["conversions"])
        )
        loser_revenue = int(
            abandoned["cart_total"].sum()
            * (b["conversions"] if winner == "A" else a["conversions"])
        )
        st.info(f"**Revenue Impact:** +${winner_revenue - loser_revenue:,}")

    # Recommendation
    st.markdown("---")
    st.subheader("🎯 Recommendation")

    if is_significant:
        st.success(f"""
        ✅ **Deploy {winner_name}** as the winning variant!

        - Conversion rate: **{max(a["conversions"], b["conversions"]) * 100:.1f}%**
        - Lift over control: **+{abs(conv_lift):.1f}%**
        - Statistical confidence: **95%+**
        """)
    else:
        st.warning(f"""
        ⏳ **Continue testing** - Results not yet significant

        - Current leader: **{winner_name}**
        - Need more data to reach 95% confidence
        - Estimated samples needed: ~{int(n * 1.5):,}
        """)


def main():
    t1, t2, t3, t4, t5, t6, t7 = st.tabs(
        [
            "📊 Dashboard",
            "⏱️ Recovery Analytics",
            "🧪 A/B Testing",
            "🎮 Try It",
            "🤖 Queue",
            "🔍 Search",
            "🏗️ Architecture",
        ]
    )
    with t1:
        render_dashboard()
    with t2:
        render_recovery_analytics()
    with t3:
        render_ab_testing()
    with t4:
        render_try_it()
    with t5:
        render_recovery_queue()
    with t6:
        render_search()
    with t7:
        render_architecture()


if __name__ == "__main__":
    main()
