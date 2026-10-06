"""Search tab: semantic search over sessions."""

import streamlit as st


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
