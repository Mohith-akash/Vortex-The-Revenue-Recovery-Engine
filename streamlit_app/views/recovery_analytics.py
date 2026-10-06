"""Recovery Analytics tab: timing, channels and ROI."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from common import chart_theme, get_df


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
    st.subheader("🧮 ROI Calculator: Estimate Your Potential Revenue Gain")
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
