"""Architecture tab: stack, features and data flow."""

import streamlit as st


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
| **LLM** | Cerebras GPT-OSS 120B | AI-powered recovery messages |
| **Embeddings** | Voyage AI | Semantic search vectors |
| **Frontend** | Streamlit | Interactive dashboards |
| **Charts** | Plotly | Dynamic visualizations |
| **Language** | Python 3.11+ | Core development |
| **CI/CD** | GitHub Actions | Lint, format and unit tests on every push |
        """)

    with col2:
        st.subheader("✨ Key Features")
        st.markdown("""
| Feature | Description |
|---------|-------------|
| **Streaming** | Event Hub events flow into Delta Live Tables |
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
