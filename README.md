<p align="center">
  <img src="https://img.shields.io/badge/🚀_Status-Live-brightgreen?style=for-the-badge" alt="Status"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-1.31+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Databricks-Delta%20Lake-FF3621?style=for-the-badge&logo=databricks&logoColor=white" alt="Databricks"/>
  <img src="https://img.shields.io/badge/Cerebras-LLaMA_3.1-00D4AA?style=for-the-badge" alt="Cerebras"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License"/>
</p>

<h1 align="center">🌀 Vortex: The Revenue Recovery Engine</h1>

<p align="center">
  <strong>AI-Powered Cart Abandonment Recovery Platform</strong><br/>
  <em>Real-time streaming • LLM personalization • Semantic search • A/B testing</em>
</p>

<p align="center">
  <a href="https://vortex-the-revenue-recovery-engine.streamlit.app/">
    <img src="https://img.shields.io/badge/▶_TRY_LIVE_DEMO-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Live Demo"/>
  </a>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-skills-demonstrated">Skills</a> •
  <a href="#-quick-start">Quick Start</a>
</p>

---

## 🎯 Problem Statement

With average cart abandonment rates at ~70%, e-commerce businesses lose the majority of potential sales.

**Vortex solves this by:**
| Challenge | Solution |
|-----------|----------|
| Late detection | ⚡ Real-time event streaming via Azure Event Hub |
| Generic messages | 🧠 AI-personalized recovery using Cerebras LLaMA 3.1 |
| No optimization | 🧪 A/B testing with statistical significance |
| Hard to find patterns | 🔍 Semantic search with Voyage AI embeddings |

---

## 🚀 Live Demo

<p align="center">
  <a href="https://vortex-the-revenue-recovery-engine.streamlit.app/">
    <strong>👉 https://vortex-the-revenue-recovery-engine.streamlit.app/</strong>
  </a>
</p>

**The demo runs on generated sample data (1000 events) to showcase the platform's capabilities:**
- 📊 Dashboard with KPIs and interactive charts
- 🤖 AI message generation (Cerebras LLaMA 3.1-8B)
- 🔍 Semantic session search (Voyage AI)
- 🧪 A/B testing framework with z-score analysis
- 🎮 Interactive cart abandonment simulator

---

## ✨ Features

### 📊 Executive Dashboard
KPI dashboard with dark theme and CSS animations. Uses generated sample data for demo.

| Metric | Description |
|--------|-------------|
| 💰 Revenue at Risk | Total value from abandoned carts |
| 🎯 Recoverable | Projected recovery at optimal timing |
| 📈 Conversion Rate | Checkout success percentage |
| 🔮 6-Hour Forecast | Predicted at-risk carts using trend analysis |

### 🧪 A/B Testing Engine
Experiment framework for recovery messages (demo with simulated variants):
- **3 Experiments**: Urgency vs Friendly, Discount vs Free Shipping, SMS vs Email
- **Statistical Significance**: Z-score with 95% confidence intervals
- **Revenue Impact**: Projected lift from winning variants

### 🤖 AI Recovery Messages
Personalized outreach powered by **Cerebras Cloud (LLaMA 3.1-8B)**:
- Customer archetype detection (Bargain Hunter, Premium Shopper, etc.)
- Context-aware tone and urgency matching
- Multi-channel support (SMS, Email, Push)
- Webhook delivery simulation with animated console

### 🔍 Semantic Search
Find similar sessions using **Voyage AI embeddings**:
- Natural language queries ("high-value electronics abandonments")
- Cosine similarity scoring with color-coded results
- Session analytics with conversion breakdown
- Fallback keyword matching when API unavailable

### ⏱️ Recovery Analytics
Deep-dive timing analysis with ROI modeling:
- **5-min vs 24-hour recovery windows**
- Channel effectiveness comparison (SMS, Push, Email)
- Interactive ROI calculator
- Priority explainability with scoring breakdown

### 🎮 Interactive Simulator
Test the recovery engine yourself:
- Build a shopping cart with real products
- Simulate abandonment scenarios
- Watch AI generate personalized recovery in real-time
- Track session journey with webhook simulation

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DATA INGESTION                              │
├─────────────────────────────────────────────────────────────────────┤
│  E-commerce Events → Azure Event Hub → Delta Live Tables             │
│  (page_view, add_to_cart, checkout_success, cart_abandoned)          │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MEDALLION ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────┤
│  Databricks + Delta Lake + dbt Core                                  │
│  ├── 🥉 Bronze: Raw event ingestion                                  │
│  ├── 🥈 Silver: Cleaned, validated, sessionized                      │
│  └── 🥇 Gold: Aggregated metrics + recovery candidates               │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AI SERVICES                                  │
├─────────────────────────────────────────────────────────────────────┤
│  Cerebras Cloud (LLaMA 3.1-8B)  →  Recovery message generation       │
│  Voyage AI (voyage-2)           →  Semantic embeddings + search      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       PRESENTATION LAYER                             │
├─────────────────────────────────────────────────────────────────────┤
│  Streamlit Dashboard (7 Interactive Tabs)                            │
│  ├── Dashboard       │  Recovery Analytics  │  A/B Testing           │
│  ├── Try It Yourself │  Recovery Queue      │  Semantic Search       │
│  └── Architecture                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Data Engineering
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Streaming** | Azure Event Hub | Real-time event ingestion |
| **Lakehouse** | Databricks + Delta Lake | ACID transactions, time travel |
| **Transformation** | dbt Core | SQL-based data modeling |
| **Orchestration** | Databricks Workflows | Pipeline scheduling |
| **Architecture** | Medallion (Bronze/Silver/Gold) | Data quality layers |

### AI/ML
| Component | Technology | Purpose |
|-----------|------------|---------|
| **LLM** | Cerebras Cloud (LLaMA 3.1-8B) | Recovery message generation |
| **Embeddings** | Voyage AI (voyage-2) | Semantic search vectors |
| **Similarity** | Cosine Distance | Session matching |
| **Statistics** | Z-Score Testing | A/B experiment significance |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | Streamlit 1.31+ | Interactive dashboard |
| **Visualization** | Plotly Express | Charts and graphs |
| **Styling** | Custom CSS | Animations, dark theme |
| **State** | Streamlit Session State | Cross-component data |

### DevOps & Infrastructure
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Hosting** | Streamlit Cloud | App deployment |
| **CI/CD** | GitHub Actions | Linting and deploy |
| **Version Control** | Git + GitHub | Code management |
| **Secrets** | Streamlit Secrets / .env | Credential management |

---

## 📈 Skills Demonstrated

### Data Engineering
- ✅ Real-time event streaming (Azure Event Hub)
- ✅ Lakehouse architecture (Databricks + Delta Lake)
- ✅ Medallion pattern (Bronze → Silver → Gold)
- ✅ SQL transformations with dbt Core
- ✅ Delta Lake features (ACID, time travel, schema evolution)
- ✅ Data quality validation and sessionization

### Analytics & Statistics
- ✅ KPI dashboard development
- ✅ A/B testing with statistical significance (z-score, 95% CI)
- ✅ Conversion funnel analysis
- ✅ Cohort analysis by customer archetype
- ✅ Time-series forecasting (trend extrapolation)
- ✅ ROI modeling and revenue attribution

### AI/ML Engineering
- ✅ LLM integration (Cerebras Cloud API)
- ✅ Prompt engineering for personalization
- ✅ Vector embeddings (Voyage AI)
- ✅ Semantic similarity search
- ✅ Graceful fallback handling
- ✅ Customer archetype classification

### Full-Stack Development
- ✅ Interactive web application (Streamlit)
- ✅ Data visualization (Plotly)
- ✅ Custom CSS animations and theming
- ✅ Session state management
- ✅ Responsive UI design
- ✅ Real-time data simulation

### DevOps & Best Practices
- ✅ CI/CD pipeline (GitHub Actions — lint + deploy)
- ✅ Environment variable management
- ✅ Secure credential handling
- ✅ Git version control
- ✅ Clean code organization
- ✅ Comprehensive documentation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- (Optional) Cerebras API key for AI messages
- (Optional) Voyage AI key for semantic search

### Installation

```bash
# Clone the repository
git clone https://github.com/Mohith-akash/Vortex-The-Revenue-Recovery-Engine.git
cd Vortex-The-Revenue-Recovery-Engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
cd streamlit_app
streamlit run app.py
```

### Environment Variables (Optional)

Create a `.env` file in the root directory:

```env
# AI Services (optional - app works without these)
CEREBRAS_API_KEY=your_cerebras_key
VOYAGE_API_KEY=your_voyage_key

# Azure Event Hub (for production streaming)
AZURE_CONNECTION_STRING=your_connection_string
EVENT_HUB_NAME=vortex-events

# Databricks (for production data)
DBT_DATABRICKS_HOST=your_workspace.cloud.databricks.com
DBT_DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your_warehouse
DBT_DATABRICKS_TOKEN=your_token
```

> **Note**: The app works without any API keys using sample data and template-based message generation.

---

## 📁 Project Structure

```
Vortex-The-Revenue-Recovery-Engine/
├── .github/workflows/          # CI/CD pipeline
│   └── ci.yml                  # GitHub Actions workflow
├── databricks/                 # Databricks configuration
│   └── databricks.yml          # Asset bundle config
├── notebooks/                  # Databricks notebooks
│   ├── 01_dlt_pipeline.py      # Delta Live Tables
│   ├── 02_recovery_orchestration.py
│   ├── 03_time_travel_demo.py
│   ├── 04_dashboard_queries.sql
│   ├── 05_streaming_pipeline.py
│   └── 06_sample_data_setup.py
├── scripts/                    # Utility scripts
│   ├── traffic_generator.py    # Event simulation
│   ├── recovery_tracker.py     # Recovery monitoring
│   ├── databricks_consumer.py  # Event consumer
│   └── heartbeat.py            # Health check
├── streamlit_app/              # Main application
│   ├── app.py                  # Dashboard (1100+ lines)
│   ├── ai_recovery.py          # Cerebras integration
│   ├── semantic_search.py      # Voyage AI search
│   ├── data_generator.py       # Sample data
│   └── requirements.txt        # App dependencies
├── vortex_analytics/           # dbt project
│   ├── dbt_project.yml         # dbt configuration
│   ├── models/                 # SQL models
│   └── profiles.yml            # Connection profiles
├── pyproject.toml              # Python project config
├── requirements.txt            # Root dependencies
├── LICENSE                     # MIT License
└── README.md                   # This file
```

---

## 📊 Key Metrics (Demo Data)

| Metric | Value |
|--------|-------|
| Sample Events | 1,000+ |
| Abandoned Carts | ~300 |
| Recovery Rate | 32% (at 5-min response) |
| A/B Test Confidence | 95% |
| Customer Archetypes | 5 types |
| Product Categories | 7 categories |

---

## 🔐 Security

- ✅ API keys stored in environment variables
- ✅ `.env` file excluded from git
- ✅ Streamlit secrets for cloud deployment
- ✅ No hardcoded credentials in source code
- ✅ Databricks secret scopes for production

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Mohith Akash**

[![GitHub](https://img.shields.io/badge/GitHub-@Mohith--akash-181717?style=flat&logo=github)](https://github.com/Mohith-akash)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Mohith_Akash-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/mohith-akash)

---

<p align="center">
  <a href="https://vortex-the-revenue-recovery-engine.streamlit.app/">
    <img src="https://img.shields.io/badge/🌀_TRY_VORTEX_NOW-7c3aed?style=for-the-badge" alt="Try Vortex"/>
  </a>
</p>

<p align="center">
  <strong>⭐ Star this repo if you found it useful!</strong>
</p>