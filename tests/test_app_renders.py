from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "streamlit_app" / "app.py"


def test_every_tab_renders(monkeypatch):
    # without keys the app uses its fallbacks: template messages, keyword search
    monkeypatch.setenv("VOYAGE_API_KEY", "")
    monkeypatch.setenv("CEREBRAS_API_KEY", "")
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not at.exception
    assert len(at.tabs) == 7
    assert len(at.metric) > 20
