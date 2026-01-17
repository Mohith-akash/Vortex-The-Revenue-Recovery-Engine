"""
Recovery Tracker - Handles cart abandonment detection and recovery actions.

This module processes abandonment events and coordinates recovery efforts.
In production, this would integrate with email/SMS services and an AI agent
for personalized messaging.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Cerebras API config - will be used for AI-powered recovery messages
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")


@dataclass
class RecoveryAction:
    """Represents a recovery attempt for an abandoned cart."""

    action_id: str
    session_id: str
    user_id: str
    cart_total: float
    cart_items: list[dict[str, Any]]
    priority: str
    channel: str  # email, sms, push, or ai_chat
    message: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: str = "pending"  # pending, sent, delivered, clicked, converted


def calculate_recovery_priority(cart_total: float, archetype: str, is_returning: bool) -> str:
    """
    Determine how aggressively we should pursue this recovery.

    High-value carts and returning customers get priority treatment.
    Window shoppers are less likely to convert, so lower priority.
    """
    score = 0

    # Cart value is the biggest factor
    if cart_total >= 500:
        score += 3
    elif cart_total >= 200:
        score += 2
    elif cart_total >= 50:
        score += 1

    # Returning customers are worth more effort
    if is_returning:
        score += 2

    # Some archetypes are more likely to convert with a nudge
    if archetype in ["CommittedBuyer", "ImpulseBuyer"]:
        score += 1
    elif archetype == "WindowShopper":
        score -= 1

    if score >= 4:
        return "critical"
    elif score >= 2:
        return "high"
    elif score >= 1:
        return "medium"
    return "low"


def select_recovery_channel(priority: str, cart_total: float) -> str:
    """
    Pick the best channel for reaching this customer.

    Higher priority = more immediate channels.
    High-value carts might warrant a phone call.
    """
    if priority == "critical":
        return "ai_chat" if cart_total >= 500 else "sms"
    elif priority == "high":
        return "push"
    elif priority == "medium":
        return "email"
    return "email"  # Default to email for low priority


def generate_recovery_message(
    cart_items: list[dict[str, Any]], cart_total: float, discount_used: str | None, archetype: str
) -> str:
    """
    Create a personalized recovery message.

    This is the basic template version. When Cerebras API is configured,
    we'll use AI to generate more compelling personalized messages.
    """
    # Get the main item in the cart
    main_item = cart_items[0]["name"] if cart_items else "your items"
    item_count = len(cart_items)

    # Different messaging strategies based on archetype
    if archetype == "PriceChecker":
        # They're price sensitive, lead with savings
        if discount_used:
            return f"Your {main_item} is still waiting! Your {discount_used} code is about to expire. Complete your order: ${cart_total:.2f}"
        return f"Still thinking about {main_item}? We found a 10% discount for you! New total: ${cart_total * 0.9:.2f}"

    elif archetype == "WindowShopper":
        # They got cold feet at shipping - address that concern
        return f"Free shipping on your {main_item}! Complete your ${cart_total:.2f} order today and we'll cover delivery."

    elif archetype in ["ImpulseBuyer", "CommittedBuyer"]:
        # These folks just need a reminder
        if item_count > 1:
            return (
                f"You left {item_count} items in your cart (${cart_total:.2f}). Ready to check out?"
            )
        return f"Your {main_item} is still in your cart! Complete your purchase: ${cart_total:.2f}"

    # Generic fallback
    return f"Don't forget about your cart! {main_item} and {item_count - 1} other items are waiting for you."


async def generate_ai_recovery_message(
    cart_items: list[dict[str, Any]], cart_total: float, user_context: dict[str, Any]
) -> str:
    """
    Use Cerebras AI to generate a hyper-personalized recovery message.

    Only called for high-value carts where the extra effort is worth it.
    Falls back to template if API is not configured.
    """
    if not CEREBRAS_API_KEY:
        # No API key configured, use template version
        return generate_recovery_message(
            cart_items,
            cart_total,
            user_context.get("discount_code"),
            user_context.get("archetype", "unknown"),
        )

    # Build context for the AI
    items_desc = ", ".join([item["name"] for item in cart_items[:3]])
    if len(cart_items) > 3:
        items_desc += f" and {len(cart_items) - 3} more items"

    prompt = f"""Generate a friendly, conversational cart recovery message.

Customer context:
- Items in cart: {items_desc}
- Cart value: ${cart_total:.2f}
- Device: {user_context.get("device", "unknown")}
- Region: {user_context.get("geo_region", "unknown")}
- Traffic source: {user_context.get("utm_source", "unknown")}
- Returning customer: {user_context.get("is_returning_user", False)}

Write a short, warm message (max 2 sentences) that:
1. Mentions the main product by name
2. Creates gentle urgency without being pushy
3. Sounds like a helpful friend, not a salesperson

Message:"""

    try:
        # Cerebras API call would go here
        # For now, return placeholder until API is wired up
        from cerebras.cloud.sdk import Cerebras

        client = Cerebras(api_key=CEREBRAS_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b", messages=[{"role": "user", "content": prompt}], max_tokens=100
        )
        return response.choices[0].message.content.strip()

    except ImportError:
        # Cerebras SDK not installed
        return generate_recovery_message(
            cart_items,
            cart_total,
            user_context.get("discount_code"),
            user_context.get("archetype", "unknown"),
        )
    except Exception as e:
        print(f"AI message generation failed: {e}")
        return generate_recovery_message(
            cart_items,
            cart_total,
            user_context.get("discount_code"),
            user_context.get("archetype", "unknown"),
        )


def process_abandonment_event(event: dict[str, Any]) -> RecoveryAction | None:
    """
    Take an abandonment event and create a recovery action.

    This is the main entry point - called when we receive a cart_abandoned event.
    """
    if event.get("event_type") != "cart_abandoned":
        return None

    cart_total = event.get("cart_total", 0)
    cart_items = event.get("cart_items", [])

    # Skip empty or tiny carts - not worth the effort
    if not cart_items or cart_total < 10:
        return None

    # Calculate priority based on multiple factors
    priority = calculate_recovery_priority(
        cart_total, event.get("user_archetype", "unknown"), event.get("is_returning_user", False)
    )

    # Pick the best channel for this customer
    channel = select_recovery_channel(priority, cart_total)

    # Generate the message
    message = generate_recovery_message(
        cart_items,
        cart_total,
        event.get("discount_code_used"),
        event.get("user_archetype", "unknown"),
    )

    import uuid

    return RecoveryAction(
        action_id=str(uuid.uuid4()),
        session_id=event.get("session_id", ""),
        user_id=event.get("user_id", ""),
        cart_total=cart_total,
        cart_items=cart_items,
        priority=priority,
        channel=channel,
        message=message,
    )


def log_recovery_action(action: RecoveryAction) -> dict[str, Any]:
    """
    Convert recovery action to a loggable format.

    This would be written to Delta Lake for tracking
    recovery performance over time.
    """
    return {
        "action_id": action.action_id,
        "session_id": action.session_id,
        "user_id": action.user_id,
        "cart_total": action.cart_total,
        "item_count": len(action.cart_items),
        "priority": action.priority,
        "channel": action.channel,
        "message_preview": action.message[:100],
        "status": action.status,
        "created_at": action.created_at.isoformat(),
    }


# Quick test
if __name__ == "__main__":
    # Simulate an abandonment event
    test_event = {
        "event_type": "cart_abandoned",
        "session_id": "test-session-123",
        "user_id": "user_42",
        "user_archetype": "WindowShopper",
        "cart_total": 349.00,
        "cart_items": [{"id": "p_004", "name": "Sony WH-1000XM5", "price": 349.00}],
        "is_returning_user": True,
        "discount_code_used": None,
        "geo_region": "NA",
        "utm_source": "google",
        "device": "mobile",
    }

    action = process_abandonment_event(test_event)
    if action:
        print("Recovery Action Created:")
        print(json.dumps(log_recovery_action(action), indent=2))
