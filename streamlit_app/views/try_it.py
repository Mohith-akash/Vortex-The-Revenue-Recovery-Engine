"""Try It tab: build a cart and generate a recovery message."""

import random
import time

import streamlit as st
from ai_recovery import RecoveryContext
from data_generator import ARCHETYPES, PRODUCTS


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
            "📦 Product", PRODUCTS, format_func=lambda p: f"{p['name']} (${p['price']:,.0f})"
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
