import sys
from pathlib import Path

# the app imports its modules as top-level names (from ai_recovery import ...)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "streamlit_app"))
