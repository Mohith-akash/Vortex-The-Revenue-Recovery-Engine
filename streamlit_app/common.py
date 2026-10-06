"""Helpers shared by the dashboard tabs."""

import pandas as pd
import streamlit as st


def get_df():
    return pd.DataFrame(st.session_state.events)


def chart_theme():
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#a5a5c0", "size": 12},
        "margin": {"l": 50, "r": 30, "t": 40, "b": 50},
        "xaxis": {"gridcolor": "rgba(124,58,237,0.1)", "tickfont": {"color": "#8b8ba7"}},
        "yaxis": {"gridcolor": "rgba(124,58,237,0.1)", "tickfont": {"color": "#8b8ba7"}},
    }
