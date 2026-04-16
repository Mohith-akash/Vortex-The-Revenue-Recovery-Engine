"""
Vortex Traffic Generator - Simulates realistic e-commerce user behavior.

Generates streaming events for cart additions, checkouts, and abandonments.
Sends data to Azure Event Hub for real-time processing in Databricks.
"""

import io
import json
import os
import random
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from azure.eventhub import EventData, EventHubProducerClient
from dotenv import load_dotenv
from faker import Faker

# Fix Windows terminal encoding for emoji support
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

fake = Faker()

# Set True for local testing (prints to console), False for Azure streaming
# NOTE: Defaulting to True to avoid Azure Event Hub costs while trial ends
TEST_MODE = True

load_dotenv()
CONNECTION_STR = os.getenv("AZURE_CONNECTION_STRING")
EVENT_HUB_NAME = os.getenv("EVENT_HUB_NAME")

if not TEST_MODE:
    if not CONNECTION_STR or not EVENT_HUB_NAME:
        print("❌ ERROR: Missing Azure credentials in .env file")
        print("Cannot run in Live Mode without AZURE_CONNECTION_STRING and EVENT_HUB_NAME")
        sys.exit(1)


# Regional weights based on global e-commerce distribution (2025 data)
GEO_REGIONS: dict[str, float] = {
    "NA": 0.30,  # North America
    "EU": 0.25,  # Europe
    "APAC": 0.35,  # Asia Pacific - largest e-commerce market
    "LATAM": 0.10,  # Latin America
}

# Traffic source distribution mirrors real marketing channel performance
UTM_SOURCES: dict[str, float] = {
    "google": 0.35,
    "direct": 0.25,
    "facebook": 0.15,
    "instagram": 0.10,
    "email": 0.10,
    "tiktok": 0.05,
}

# Browser market share (2025 stats)
BROWSERS: list[str] = ["Chrome", "Safari", "Edge", "Firefox", "Samsung Internet"]

# Discount codes with varying appeal - affects conversion rates
DISCOUNT_CODES: list[str | None] = [None, None, None, "SAVE10", "WELCOME20", "FLASH30", "VIP50"]


@dataclass
class Product:
    """Represents an item in the product catalog."""

    id: str
    name: str
    category: str
    price: float
    popularity: float = 1.0  # Higher = more likely to be added to cart


# Realistic price points and popularity weights for streaming simulation.
#
# NOTE: There is a second product catalog in streamlit_app/data_generator.py
# (25 items, dict shape). This one is intentionally separate:
#   - This catalog (Product dataclass) feeds the Azure Event Hub streaming
#     simulator and is tuned for weighted sampling.
#   - The data_generator catalog backs the Streamlit demo UI (product dropdown,
#     charts) and needs more variety.
# Shapes differ (dataclass vs dict), so they are not trivially interchangeable.
# If you consolidate, pick one representation and update both consumers.
PRODUCT_CATALOG: list[Product] = [
    Product("p_001", "MacBook Pro 16", "Electronics", 2499.00, 0.8),
    Product("p_002", "Nike Air Jordan 1", "Fashion", 180.00, 1.5),
    Product("p_003", "Dyson V15 Vacuum", "Home", 649.00, 0.9),
    Product("p_004", "Sony WH-1000XM5", "Electronics", 349.00, 1.3),
    Product("p_005", "Protein Powder 5lb", "Sports", 64.99, 1.1),
    Product("p_006", "iPad Air", "Electronics", 599.00, 1.2),
    Product("p_007", "Lululemon Align Leggings", "Fashion", 98.00, 1.4),
    Product("p_008", "Instant Pot Duo", "Home", 89.00, 1.0),
    Product("p_009", "Oura Ring Gen 3", "Electronics", 299.00, 0.7),
    Product("p_010", "Stanley Tumbler 40oz", "Home", 45.00, 1.8),
]


@dataclass
class ArchetypeConfig:
    """Defines behavior patterns for each customer type."""

    weight: float
    avg_session_duration: tuple[int, int]  # min, max seconds
    avg_page_views: tuple[int, int]  # min, max pages before cart


# Customer archetypes based on real behavioral research
ARCHETYPES: dict[str, ArchetypeConfig] = {
    "ImpulseBuyer": ArchetypeConfig(0.15, (30, 120), (1, 3)),
    "WindowShopper": ArchetypeConfig(0.35, (180, 400), (5, 12)),
    "PriceChecker": ArchetypeConfig(0.25, (120, 300), (4, 8)),
    "CommittedBuyer": ArchetypeConfig(0.15, (90, 200), (3, 6)),
    "QuickBrowser": ArchetypeConfig(0.10, (15, 60), (1, 2)),
}


def weighted_choice(options: dict[str, float]) -> str:
    """Pick a random option based on weight distribution."""
    items = list(options.keys())
    weights = list(options.values())
    return random.choices(items, weights=weights, k=1)[0]


def pick_product() -> Product:
    """Select a product weighted by popularity."""
    weights = [p.popularity for p in PRODUCT_CATALOG]
    return random.choices(PRODUCT_CATALOG, weights=weights, k=1)[0]


@dataclass
class UserSession:
    """
    Tracks a single user's journey through the site.

    Each session follows a state machine based on the user's archetype,
    simulating realistic browsing, cart, and checkout behavior.
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = field(default_factory=lambda: f"user_{random.randint(10000, 99999)}")

    # Device and context
    device: str = field(default_factory=lambda: random.choice(["mobile", "desktop", "tablet"]))
    browser: str = field(default_factory=lambda: random.choice(BROWSERS))
    geo_region: str = field(default_factory=lambda: weighted_choice(GEO_REGIONS))
    utm_source: str = field(default_factory=lambda: weighted_choice(UTM_SOURCES))

    # Session metadata
    is_returning_user: bool = field(default_factory=lambda: random.random() < 0.35)
    discount_code: str | None = field(default_factory=lambda: random.choice(DISCOUNT_CODES))
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))

    # These get set in __post_init__ based on archetype
    archetype: str = field(default="")
    session_duration: int = field(default=0)
    page_views: int = field(default=0)

    # State tracking
    cart: list[Product] = field(default_factory=list)
    is_active: bool = field(default=True)
    state: str = field(default="browse")
    events_generated: int = field(default=0)

    def __post_init__(self) -> None:
        """Set archetype and derived values after initialization."""
        if not self.archetype:
            self.archetype = weighted_choice({k: v.weight for k, v in ARCHETYPES.items()})

        config = ARCHETYPES[self.archetype]
        self.session_duration = random.randint(*config.avg_session_duration)
        self.page_views = random.randint(*config.avg_page_views)

    def next_action(self) -> str | None:
        """
        Determine the next action based on current state and archetype.
        Returns None when session should end.
        """
        if not self.is_active:
            return None

        # Each archetype follows its own purchase funnel
        match self.archetype:
            case "ImpulseBuyer":
                # See it, want it, buy it
                if self.state == "browse":
                    self.state = "add_to_cart"
                    return "add_to_cart"
                elif self.state == "add_to_cart":
                    self.state = "checkout_success"
                    self.is_active = False
                    return "checkout_success"

            case "WindowShopper":
                # Browses a lot, adds to cart, but bails at checkout
                if self.state == "browse":
                    self.state = "add_to_cart"
                    return "add_to_cart"
                elif self.state == "add_to_cart":
                    self.state = "view_shipping"
                    return "page_view"
                elif self.state == "view_shipping":
                    # This is where most abandonments happen - shipping costs shock
                    self.is_active = False
                    return None

            case "PriceChecker":
                # Adds to cart to "save for later", never comes back
                if self.state == "browse":
                    self.state = "add_to_cart"
                    return "add_to_cart"
                elif self.state == "add_to_cart":
                    self.is_active = False
                    return None

            case "CommittedBuyer":
                # The dream customer - goes through the whole flow
                if self.state == "browse":
                    self.state = "add_to_cart"
                    return "add_to_cart"
                elif self.state == "add_to_cart":
                    self.state = "checkout_start"
                    return "checkout_start"
                elif self.state == "checkout_start":
                    self.state = "checkout_success"
                    self.is_active = False
                    return "checkout_success"

            case "QuickBrowser":
                # Just looking around, leaves without doing much
                if self.state == "browse":
                    if random.random() < 0.3:
                        self.state = "add_to_cart"
                        return "add_to_cart"
                    else:
                        self.is_active = False
                        return None
                elif self.state == "add_to_cart":
                    self.is_active = False
                    return None

        self.is_active = False
        return None

    def generate_event(self) -> dict[str, Any] | None:
        """
        Create the next event for this session.
        Returns None if session has ended.
        """
        action = self.next_action()
        if not action:
            return None

        product = pick_product()
        if action == "add_to_cart":
            self.cart.append(product)

        cart_total = sum(item.price for item in self.cart)
        self.events_generated += 1

        # Build the event payload with all the juicy analytics data
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": action,
            "timestamp": datetime.now(UTC).isoformat(),
            # User identifiers
            "user_id": self.user_id,
            "session_id": self.session_id,
            "user_archetype": self.archetype,
            # Product info (only for cart/purchase actions)
            "product_id": product.id if action in ["add_to_cart", "checkout_success"] else None,
            "product_name": product.name if action in ["add_to_cart", "checkout_success"] else None,
            "product_category": product.category
            if action in ["add_to_cart", "checkout_success"]
            else None,
            "amount": product.price if action in ["add_to_cart", "checkout_success"] else 0,
            # Cart state
            "cart_total": round(cart_total, 2),
            "cart_item_count": len(self.cart),
            # Session context - this is gold for analytics
            "device": self.device,
            "browser": self.browser,
            "geo_region": self.geo_region,
            "utm_source": self.utm_source,
            # Behavioral signals
            "session_duration_seconds": self.session_duration,
            "page_views_before_cart": self.page_views,
            "is_returning_user": self.is_returning_user,
            "discount_code_used": self.discount_code,
        }

        return event

    def generate_abandonment_event(self) -> dict[str, Any] | None:
        """
        Create a special event when user abandons cart.
        This is what triggers recovery workflows.
        """
        if not self.cart or self.state == "checkout_success":
            return None

        cart_total = sum(item.price for item in self.cart)

        return {
            "event_id": str(uuid.uuid4()),
            "event_type": "cart_abandoned",
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "user_archetype": self.archetype,
            "cart_total": round(cart_total, 2),
            "cart_item_count": len(self.cart),
            "cart_items": [{"id": p.id, "name": p.name, "price": p.price} for p in self.cart],
            "abandonment_stage": self.state,
            "geo_region": self.geo_region,
            "utm_source": self.utm_source,
            "device": self.device,
            "is_returning_user": self.is_returning_user,
            "discount_code_used": self.discount_code,
            "session_duration_seconds": self.session_duration,
            "recovery_priority": "high"
            if cart_total > 200
            else "medium"
            if cart_total > 50
            else "low",
        }


def send_to_azure(event: dict[str, Any], producer: EventHubProducerClient) -> None:
    """Push an event to Azure Event Hub."""
    try:
        batch = producer.create_batch()
        batch.add(EventData(json.dumps(event)))
        producer.send_batch(batch)

        event_type = event.get("event_type", "unknown")
        cart_total = event.get("cart_total", 0)
        archetype = event.get("user_archetype", "N/A")

        print(f"☁️  Sent: {event_type:<16} | {archetype:<14} | ${cart_total:>8.2f}")
    except Exception as e:
        print(f"❌ Failed to send event: {e}")


def main() -> None:
    """Main loop - generates events until stopped with Ctrl+C."""
    mode_display = "TEST (Console Only)" if TEST_MODE else "LIVE (Streaming to Azure)"
    print(f"⚡ VORTEX GENERATOR v2.0 | MODE: {mode_display}")
    print("-" * 65)

    sessions: list[UserSession] = []
    producer: EventHubProducerClient | None = None

    if not TEST_MODE:
        try:
            print(f"🔌 Connecting to Event Hub: {EVENT_HUB_NAME}...")
            producer = EventHubProducerClient.from_connection_string(
                conn_str=CONNECTION_STR, eventhub_name=EVENT_HUB_NAME
            )
            print("✓ Connected to Azure Event Hub")
            print("-" * 65)
        except Exception as e:
            print(f"❌ Failed to connect to Azure: {e}")
            sys.exit(1)

    # Test mode creates a fixed set of sessions for predictable output
    if TEST_MODE:
        for _ in range(3):
            sessions.append(UserSession(archetype="ImpulseBuyer"))
        for _ in range(4):
            sessions.append(UserSession(archetype="WindowShopper"))
        for _ in range(3):
            sessions.append(UserSession(archetype="CommittedBuyer"))
        print("Created 10 test sessions across 3 archetypes")
        print("-" * 65)

    stats = {"events": 0, "abandonments": 0, "purchases": 0, "revenue": 0.0}

    try:
        while True:
            # Keep a pool of active sessions going
            if not TEST_MODE and len(sessions) < 25:
                sessions.append(UserSession())

            # Wrap up when test sessions are done
            if TEST_MODE and not sessions:
                print("-" * 65)
                print("✓ Test complete!")
                print(
                    f"   Events: {stats['events']} | Purchases: {stats['purchases']} | Abandonments: {stats['abandonments']}"
                )
                print(f"   Revenue: ${stats['revenue']:.2f}")
                break

            if not sessions:
                time.sleep(0.5)
                continue

            session = random.choice(sessions)
            event = session.generate_event()

            if event:
                stats["events"] += 1

                if event["event_type"] == "checkout_success":
                    stats["purchases"] += 1
                    stats["revenue"] += event["cart_total"]

                if TEST_MODE:
                    print(json.dumps(event, indent=2))
                    time.sleep(0.2)
                else:
                    send_to_azure(event, producer)
                    time.sleep(random.uniform(0.3, 1.5))
            else:
                # Session ended - check for abandoned cart
                abandonment = session.generate_abandonment_event()
                if abandonment:
                    stats["abandonments"] += 1

                    if TEST_MODE:
                        cart_val = abandonment["cart_total"]
                        priority = abandonment["recovery_priority"]
                        print(
                            f">> [ABANDONED] {session.archetype} left ${cart_val:.2f} in cart [{priority} priority]"
                        )
                    else:
                        send_to_azure(abandonment, producer)

                sessions.remove(session)

            if not TEST_MODE:
                time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n" + "-" * 65)
        print("🛑 Stopping generator...")
        print(f"   Final stats - Events: {stats['events']} | Revenue: ${stats['revenue']:.2f}")

    finally:
        if producer:
            print("🔌 Closing Azure connection...")
            producer.close()
            print("✓ Connection closed")

        if TEST_MODE:
            input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
