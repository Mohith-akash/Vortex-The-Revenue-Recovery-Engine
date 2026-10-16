"""
Semantic Search Module - Uses Voyage AI for embedding-based session analysis.
Enables finding similar user sessions and behavior patterns.
"""

import json
import os

# Try to import Voyage AI SDK
try:
    import voyageai

    VOYAGE_AVAILABLE = True
except ImportError:
    VOYAGE_AVAILABLE = False
    voyageai = None

# Voyage's free tier allows 10K tokens a minute. All 1,000 demo sessions came to
# ~65K tokens, so the embed call was rejected on every page load and search
# silently fell back to keywords. At ~55 tokens a session, 120 sessions (~6.7K)
# fit with room for queries; keyword search still covers every session.
MAX_EMBEDDED_SESSIONS = 120


class SemanticSearchEngine:
    """Semantic search for user sessions using Voyage AI embeddings."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        self.client = None
        self.session_embeddings = {}  # Cache: session_id -> embedding
        self.session_data = {}  # Cache: session_id -> session info
        self.last_method = "keyword"  # how the latest search was ranked

        if self.api_key and VOYAGE_AVAILABLE:
            try:
                self.client = voyageai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Failed to initialize Voyage AI: {e}")
                self.client = None

    def create_session_text(self, event: dict) -> str:
        """Convert a session event to searchable text."""
        text = f"""
        Customer: {event.get("user_name", "Unknown")} ({event.get("user_archetype", "Unknown")})
        Product: {event.get("product_name", "Unknown")} in {event.get("product_category", "Unknown")} for ${event.get("cart_total", 0):.2f}
        Behavior: Viewed {event.get("page_views_before_cart", 0)} pages over {event.get("session_duration_seconds", 0)} seconds
        Device: {event.get("device", "Unknown")} via {event.get("utm_source", "Unknown")}
        Outcome: {"Abandoned" if event.get("is_abandonment") else "Purchased" if event.get("is_conversion") else "Browsing"}
        {"Abandonment stage: " + event.get("abandonment_stage", "") if event.get("is_abandonment") else ""}
        {"Priority: " + event.get("recovery_priority", "") if event.get("is_abandonment") else ""}
        """
        # drop the source indentation and empty lines: ~15% of the tokens were whitespace
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())

    def index_sessions(self, events: list) -> int:
        """Index events for search. Returns how many sessions got embeddings."""
        # Get unique sessions (take the last event per session)
        sessions = {}
        for event in events:
            session_id = event.get("session_id")
            if session_id:
                sessions[session_id] = event

        # keyword search works on every session, with or without Voyage
        self.session_data.update(sessions)

        if not self.client or not sessions:
            return 0

        session_ids = list(sessions)[:MAX_EMBEDDED_SESSIONS]
        texts = [self.create_session_text(sessions[s]) for s in session_ids]

        try:
            result = self.client.embed(texts, model="voyage-3.5-lite", input_type="document")
            for session_id, embedding in zip(session_ids, result.embeddings, strict=True):
                self.session_embeddings[session_id] = embedding

            return len(session_ids)

        except Exception as e:
            print(f"Failed to index sessions: {e}")
            return 0

    def search(self, query: str, top_k: int = 5) -> list:
        """Search for sessions matching a natural language query."""
        if not self.client or not self.session_embeddings:
            return self._fallback_search(query, top_k)

        try:
            # Embed the query
            result = self.client.embed([query], model="voyage-3.5-lite", input_type="query")
            query_embedding = result.embeddings[0]

            # Calculate similarities
            similarities = []
            for session_id, embedding in self.session_embeddings.items():
                similarity = self._cosine_similarity(query_embedding, embedding)
                similarities.append((session_id, similarity))

            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)

            self.last_method = "embeddings"

            # Return top K results with session data
            results = []
            for session_id, score in similarities[:top_k]:
                if session_id in self.session_data:
                    results.append(
                        {
                            "session_id": session_id,
                            "similarity": round(score, 3),
                            "data": self.session_data[session_id],
                        }
                    )

            return results

        except Exception as e:
            print(f"Search failed: {e}")
            return self._fallback_search(query, top_k)

    def _fallback_search(self, query: str, top_k: int) -> list:
        """Keyword-based fallback when Voyage AI is unavailable."""
        self.last_method = "keyword"
        query_lower = query.lower()
        results = []

        # Synonym mapping
        synonyms = {
            "window": "windowshopper",
            "shoppers": "windowshopper",
            "window shoppers": "windowshopper",
            "left": "abandoned",
            "abandoned": "abandoned",
            "high value": "critical",
            "expensive": "high",
            "cheap": "low",
            "impulse": "impulsive",
            "mobile": "mobile",
            "desktop": "desktop",
            "electronics": "electronics",
            "fashion": "fashion",
        }

        # Expand query with synonyms
        expanded_terms = set(query_lower.split())
        for term in list(expanded_terms):
            if term in synonyms:
                expanded_terms.add(synonyms[term])

        for session_id, event in self.session_data.items():
            # Build searchable string from all fields
            searchable = " ".join(
                [
                    str(event.get("user_name", "")),
                    str(event.get("user_archetype", "")),
                    str(event.get("product_name", "")),
                    str(event.get("product_category", "")),
                    str(event.get("geo_region", "")),
                    str(event.get("device", "")),
                    str(event.get("recovery_priority", "")),
                    "abandoned"
                    if event.get("is_abandonment") or event.get("event_type") == "cart_abandoned"
                    else "",
                    "converted"
                    if event.get("is_conversion") or event.get("event_type") == "checkout_success"
                    else "",
                    f"${event.get('cart_total', 0):.0f}",
                ]
            ).lower()

            # Score based on matches
            score = 0
            for term in expanded_terms:
                if term in searchable:
                    score += 1

            if score > 0:
                results.append(
                    {
                        "session_id": session_id,
                        "similarity": score / len(expanded_terms),
                        "data": event,
                    }
                )

        # Sort by match score
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, a: list, b: list) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def analyze_patterns(self) -> dict:
        """Analyze patterns in indexed sessions."""
        if not self.session_data:
            return {}

        patterns = {
            "total_sessions": len(self.session_data),
            "by_archetype": {},
            "by_outcome": {"abandoned": 0, "converted": 0, "browsing": 0},
            "by_category": {},
            "high_value_abandonments": [],
        }

        for session_id, event in self.session_data.items():
            # By archetype
            archetype = event.get("user_archetype", "Unknown")
            if archetype not in patterns["by_archetype"]:
                patterns["by_archetype"][archetype] = {"count": 0, "total_value": 0}
            patterns["by_archetype"][archetype]["count"] += 1
            patterns["by_archetype"][archetype]["total_value"] += event.get("cart_total", 0)

            # By outcome
            if event.get("is_abandonment"):
                patterns["by_outcome"]["abandoned"] += 1
            elif event.get("is_conversion"):
                patterns["by_outcome"]["converted"] += 1
            else:
                patterns["by_outcome"]["browsing"] += 1

            # By category
            category = event.get("product_category", "Unknown")
            if category not in patterns["by_category"]:
                patterns["by_category"][category] = 0
            patterns["by_category"][category] += 1

            # High value abandonments
            if event.get("is_abandonment") and event.get("cart_total", 0) >= 200:
                patterns["high_value_abandonments"].append(
                    {
                        "session_id": session_id,
                        "customer": event.get("user_name"),
                        "product": event.get("product_name"),
                        "value": event.get("cart_total"),
                        "priority": event.get("recovery_priority"),
                    }
                )

        return patterns


if __name__ == "__main__":
    # Test the search engine
    from data_generator import generate_sample_data

    engine = SemanticSearchEngine()
    events = generate_sample_data(20)

    # Index sessions
    indexed = engine.index_sessions(events)
    print(f"Indexed {indexed} sessions")

    # Test search
    results = engine.search("users who abandoned expensive electronics")
    print("\nSearch results:")
    for r in results:
        print(
            f"  - {r['data'].get('user_name')}: {r['data'].get('product_name')} (Score: {r['similarity']})"
        )

    # Analyze patterns
    patterns = engine.analyze_patterns()
    print(f"\nPatterns: {json.dumps(patterns, indent=2, default=str)}")
