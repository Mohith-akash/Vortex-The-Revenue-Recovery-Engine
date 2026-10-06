"""
Vortex - The Revenue Recovery Engine
Vibrant dashboard with recovery timing analytics.
"""

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

from ai_recovery import AIRecoveryEngine  # noqa: E402
from data_generator import generate_sample_data  # noqa: E402
from semantic_search import SemanticSearchEngine  # noqa: E402
from styles import inject_css  # noqa: E402
from views.ab_testing import render_ab_testing  # noqa: E402
from views.architecture import render_architecture  # noqa: E402
from views.dashboard import render_dashboard  # noqa: E402
from views.recovery_analytics import render_recovery_analytics  # noqa: E402
from views.recovery_queue import render_recovery_queue  # noqa: E402
from views.search import render_search  # noqa: E402
from views.try_it import render_try_it  # noqa: E402

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
