"""Queue tab: abandoned carts ranked for recovery."""

import streamlit as st
from ai_recovery import create_recovery_context_from_event
from common import get_df


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
