# Vortex: Revenue Recovery Engine

Real-time cart-abandonment recovery platform: e-commerce events stream through Azure Event Hubs into a Databricks medallion lakehouse, and an LLM generates personalized recovery messages per customer archetype.

**Live demo:** https://vortex-the-revenue-recovery-engine.streamlit.app/

## About the demo

The public demo runs on **generated sample data** (~1,000 events), because keeping Event Hubs plus a Databricks cluster hot 24/7 costs real money for a portfolio project. The streaming pipeline itself is real and in this repo: `scripts/traffic_generator.py` produces events into Azure Event Hubs, and the notebooks in `notebooks/` consume them into Bronze/Silver/Gold Delta tables with end-to-end latency under 500ms. The demo runs the analytics and AI layers on top of a static snapshot of that data.

What you can do in the demo:

- KPI dashboard with revenue-at-risk and recovery metrics
- AI recovery-message generation (Cerebras LLaMA 3.1-8B)
- Semantic session search (Voyage AI embeddings)
- A/B testing framework with z-score significance
- Interactive cart-abandonment simulator

## Problem

Average cart-abandonment rates sit around 70%, so most potential e-commerce revenue never converts.

| Challenge | Approach |
|-----------|----------|
| Late detection | Streaming ingestion via Azure Event Hubs |
| Generic messages | LLM-personalized recovery per customer archetype |
| No optimization | A/B testing with statistical significance |
| Hidden patterns | Semantic search over session embeddings |

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  INGESTION                                                           │
│  E-commerce events → Azure Event Hubs → Delta Live Tables            │
│  (page_view, add_to_cart, checkout_success, cart_abandoned)          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MEDALLION LAKEHOUSE (Databricks + Delta Lake + dbt Core)            │
│  ├── Bronze: raw event ingestion                                     │
│  ├── Silver: cleaned, validated, sessionized                         │
│  └── Gold:   aggregated metrics + recovery candidates                │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AI SERVICES                                                         │
│  Cerebras (LLaMA 3.1-8B) → recovery message generation               │
│  Voyage AI (voyage-2)    → semantic embeddings + search              │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PRESENTATION                                                        │
│  Streamlit dashboard: KPIs | Recovery Analytics | A/B Testing |      │
│  Simulator | Recovery Queue | Semantic Search | Architecture         │
└─────────────────────────────────────────────────────────────────────┘
```

Data quality is enforced with DLT expectations on every layer: bad records are quarantined into a dead-letter table instead of failing the pipeline. dbt Core models build the cart-abandonment analytics, including a recovery queue for carts over $500.

## Features

**Recovery analytics:** timing analysis comparing 5-minute vs 24-hour response windows, channel effectiveness (SMS/push/email), and an ROI calculator with priority-scoring breakdown.

**AI recovery messages:** customer archetype detection (bargain hunter, premium shopper, ...), context-aware tone matching, multi-channel templates, and graceful fallback to templates when no API key is configured.

**A/B testing:** three experiments (urgency vs. friendly, discount vs. free shipping, SMS vs. email) evaluated with z-scores at 95% confidence, including projected revenue lift.

**Semantic search:** natural-language queries like "high-value electronics abandonments" matched against session embeddings via cosine similarity, with keyword fallback.

**Simulator:** build a cart, abandon it, and watch the recovery flow run end to end.

## Tech stack

| Layer | Technology |
|-------|------------|
| Streaming | Azure Event Hubs |
| Lakehouse | Databricks, Delta Lake, Delta Live Tables |
| Transformation | dbt Core |
| LLM | Cerebras Cloud (LLaMA 3.1-8B) |
| Embeddings | Voyage AI (voyage-2) |
| Dashboard | Streamlit + Plotly |
| CI/CD | GitHub Actions (lint + deploy) |

## Quick start

```bash
git clone https://github.com/Mohith-akash/Vortex-The-Revenue-Recovery-Engine.git
cd Vortex-The-Revenue-Recovery-Engine

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cd streamlit_app
streamlit run app.py
```

The app runs without any API keys, using sample data and template-based messages. To enable the AI features and the real streaming pipeline, create a `.env` in the project root:

```env
# AI services (optional, app falls back to templates without them)
CEREBRAS_API_KEY=your_cerebras_key
VOYAGE_API_KEY=your_voyage_key

# Azure Event Hubs (for the streaming pipeline)
AZURE_CONNECTION_STRING=your_connection_string
EVENT_HUB_NAME=vortex-events

# Databricks (for lakehouse-backed data)
DBT_DATABRICKS_HOST=your_workspace.cloud.databricks.com
DBT_DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your_warehouse
DBT_DATABRICKS_TOKEN=your_token
```

## Project structure

```
Vortex-The-Revenue-Recovery-Engine/
├── notebooks/                      # Databricks notebooks
│   ├── 01_dlt_pipeline.py          # DLT pipeline with expectations (Bronze/Silver/Gold)
│   ├── 02_recovery_orchestration.py# Recovery queue orchestration
│   ├── 03_time_travel_demo.py      # Delta Lake versioning: audit, debug, restore
│   ├── 04_dashboard_queries.sql    # Gold-layer analytics queries
│   ├── 05_streaming_pipeline_no_dlt.py  # Same pipeline without DLT; runs on
│   │                               #   Databricks Free Edition (structured streaming)
│   └── 06_sample_data_setup.py     # Seed sample data in Databricks
├── scripts/
│   ├── traffic_generator.py        # Simulates shopper events into Event Hubs
│   ├── databricks_consumer.py      # Event Hubs → Delta consumer
│   ├── recovery_tracker.py         # Recovery outcome monitoring
│   └── heartbeat.py                # Keeps the Streamlit demo awake
├── streamlit_app/
│   ├── app.py                      # Dashboard (7 tabs)
│   ├── styles.py                   # CSS theme
│   ├── ai_recovery.py              # Cerebras integration + archetype logic
│   ├── semantic_search.py          # Voyage AI search with keyword fallback
│   └── data_generator.py           # Demo sample data
├── vortex_analytics/               # dbt project (gold models)
├── databricks/databricks.yml       # Asset bundle config
└── .github/workflows/ci.yml        # Lint + deploy
```

Two pipeline variants exist on purpose: `01_dlt_pipeline.py` is the production-style DLT version with expectations; `05_streaming_pipeline_no_dlt.py` implements the same flow with plain structured streaming so it runs on Databricks Free Edition.

## License

MIT license, see [LICENSE](LICENSE).

Built by [Mohith Akash](https://github.com/Mohith-akash) · [LinkedIn](https://linkedin.com/in/mohith-akash)
