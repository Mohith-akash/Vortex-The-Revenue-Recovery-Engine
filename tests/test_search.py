from data_generator import generate_sample_data
from semantic_search import MAX_EMBEDDED_SESSIONS, SemanticSearchEngine


class FakeVoyage:
    """Stands in for voyageai.Client; records how many texts each embed call sends."""

    def __init__(self):
        self.calls = []

    def embed(self, texts, model, input_type):
        self.calls.append(len(texts))
        vector = [1.0, 0.0] if input_type == "query" else [0.9, 0.1]
        return type("Result", (), {"embeddings": [vector for _ in texts]})()


def test_keyword_search_works_without_an_api_key(monkeypatch):
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    engine = SemanticSearchEngine()
    assert engine.index_sessions(generate_sample_data(50)) == 0
    assert engine.search("window shoppers who left", top_k=5)
    assert engine.last_method == "keyword"


def test_embeds_a_slice_that_fits_the_free_tier():
    engine = SemanticSearchEngine(api_key="test")
    engine.client = FakeVoyage()
    events = generate_sample_data(1000)
    embedded = engine.index_sessions(events)
    assert embedded == MAX_EMBEDDED_SESSIONS
    assert engine.client.calls == [MAX_EMBEDDED_SESSIONS]
    # keyword fallback still covers every session
    assert len(engine.session_data) > MAX_EMBEDDED_SESSIONS
    assert engine.search("high value electronics", top_k=3)
    assert engine.last_method == "embeddings"
