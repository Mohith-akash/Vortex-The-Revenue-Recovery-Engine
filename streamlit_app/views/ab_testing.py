"""A/B Testing tab: message experiments with z-tests."""

import random

import streamlit as st
from common import get_df


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
