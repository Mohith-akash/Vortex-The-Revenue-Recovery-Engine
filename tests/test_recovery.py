import math

import pytest
from ai_recovery import AIRecoveryEngine, RecoveryContext, create_recovery_context_from_event
from data_generator import ARCHETYPES, generate_sample_data


def ctx(**overrides):
    base = dict(
        customer_name="Anna Schmidt",
        customer_archetype="WindowShopper",
        product_name="Desk Lamp",
        product_category="Home",
        cart_total=80.0,
        abandonment_stage="cart",
        is_returning=False,
        discount_code=None,
        utm_source="demo",
        session_duration=120,
        page_views=4,
    )
    base.update(overrides)
    return RecoveryContext(**base)


@pytest.fixture
def offline_engine(monkeypatch):
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    return AIRecoveryEngine(api_key=None)


def test_template_fallback_without_api_key(offline_engine):
    result = offline_engine.generate_message(ctx())
    assert result["is_ai_generated"] is False
    assert result["model"] == "template"
    assert "Anna" in result["message"] and "Schmidt" not in result["message"]
    assert "Desk Lamp" in result["message"]


@pytest.mark.parametrize(
    "overrides, channel",
    [
        ({"cart_total": 650.0}, "sms"),
        ({"customer_archetype": "QuickBrowser"}, "push"),
        ({"is_returning": True}, "email"),
        ({}, "push"),
    ],
)
def test_channel_rules(offline_engine, overrides, channel):
    assert offline_engine._select_channel(ctx(**overrides)) == channel


def test_nan_discount_code_does_not_crash(offline_engine):
    # dataframe rows hand over a missing discount as float NaN (bug fixed in july)
    event = {"user_name": "Lena", "user_archetype": "PriceChecker", "discount_code_used": math.nan}
    context = create_recovery_context_from_event(event)
    assert context.discount_code is None
    assert "Lena" in offline_engine.generate_message(context)["message"]


def test_every_archetype_has_a_template(offline_engine):
    for archetype in ARCHETYPES:
        message = offline_engine.generate_message(ctx(customer_archetype=archetype))["message"]
        assert "Anna" in message


def test_each_session_ends_in_one_outcome():
    events = generate_sample_data(50)
    outcomes = [e for e in events if e["event_type"] in ("checkout_success", "cart_abandoned")]
    assert len(outcomes) == 50
    assert {e["user_archetype"] for e in events} <= set(ARCHETYPES)
    for e in events:
        if e["event_type"] == "cart_abandoned":
            assert e["is_abandonment"] and e["recovery_priority"] is not None
        else:
            assert e["recovery_priority"] is None
