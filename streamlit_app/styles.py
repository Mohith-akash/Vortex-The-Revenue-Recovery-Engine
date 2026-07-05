"""CSS theme for the Vortex dashboard."""

import streamlit as st

_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }

    /* Background with subtle animation */
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
        animation: gradientShift 20s ease infinite;
        background-size: 200% 200%;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .main .block-container { padding: 1.5rem 2.5rem; max-width: 1500px; }
    [data-testid="stSidebar"] { display: none !important; }

    /* Tabs with slide animation */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background: rgba(255,255,255,0.03); padding: 8px; border-radius: 16px; }
    .stTabs [data-baseweb="tab"] {
        background: transparent; border-radius: 12px; padding: 12px 24px; color: #8b8ba7; font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stTabs [data-baseweb="tab"]:hover { color: #c4b5fd; transform: translateY(-2px); }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%) !important;
        color: white !important;
        box-shadow: 0 8px 24px rgba(124, 58, 237, 0.4);
        transform: scale(1.02);
    }

    /* Metrics with pop-in animation */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.05) 100%);
        border: 1px solid rgba(124, 58, 237, 0.2);
        border-radius: 16px;
        padding: 24px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fadeInUp 0.5s ease-out;
    }
    [data-testid="stMetric"]:hover { transform: translateY(-4px) scale(1.02); box-shadow: 0 12px 32px rgba(124, 58, 237, 0.3); }
    [data-testid="stMetric"] label { color: #a5a5c0 !important; font-size: 0.8rem !important; text-transform: uppercase; letter-spacing: 1px; font-weight: 600 !important; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { color: #fff !important; font-size: 2rem !important; font-weight: 800 !important; }

    /* Button animations */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
        border: none; border-radius: 12px; padding: 12px 24px; font-weight: 600; color: white;
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stButton > button:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 12px 36px rgba(124, 58, 237, 0.5); }
    .stButton > button:active { transform: translateY(0) scale(0.98); }

    /* Input animations */
    .stTextInput input, .stSelectbox > div > div {
        background: rgba(30, 30, 66, 0.8) !important;
        border: 1px solid rgba(124, 58, 237, 0.3) !important;
        border-radius: 12px !important;
        color: #fff !important;
        transition: all 0.3s ease;
    }
    .stTextInput input:focus, .stSelectbox > div > div:focus-within {
        border-color: rgba(124, 58, 237, 0.8) !important;
        box-shadow: 0 0 20px rgba(124, 58, 237, 0.2) !important;
    }

    h1, h2, h3 { color: #fff !important; font-weight: 700 !important; }
    hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, rgba(124,58,237,0.3), transparent); margin: 2rem 0; }

    /* Alert box animations */
    .stSuccess, .stInfo, .stWarning { animation: slideInLeft 0.4s ease-out; }
    .stSuccess { background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%) !important; border: 1px solid rgba(16, 185, 129, 0.3) !important; border-radius: 12px !important; }
    .stInfo { background: linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(236, 72, 153, 0.1) 100%) !important; border: 1px solid rgba(124, 58, 237, 0.3) !important; border-radius: 12px !important; }
    .stWarning { background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%) !important; border: 1px solid rgba(245, 158, 11, 0.3) !important; border-radius: 12px !important; }

    /* Dataframe animation */
    .stDataFrame { animation: fadeIn 0.6s ease-out; }

    /* Chart container animation */
    .stPlotlyChart { animation: fadeInUp 0.5s ease-out; }

    /* Keyframes */
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Loading spinner enhancement */
    .stSpinner > div { animation: pulse 1.5s ease-in-out infinite; }

    /* Expander animation */
    .streamlit-expanderHeader { transition: all 0.3s ease; }
    .streamlit-expanderHeader:hover { background: rgba(124, 58, 237, 0.1); border-radius: 8px; }
</style>
"""


def inject_css():
    """Apply the Vortex dark theme to the current Streamlit page."""
    st.markdown(_CSS, unsafe_allow_html=True)
