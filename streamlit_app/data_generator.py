"""
Data generator for Vortex - creates realistic e-commerce sample data.
Uses Faker for customer names and generates diverse product catalog.
"""

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from faker import Faker

fake = Faker()

# Expanded product catalog with 25+ items.
#
# NOTE: There is a second, smaller product catalog in scripts/traffic_generator.py
# (10 products, different IDs/prices). They are intentionally separate:
#   - This catalog (dicts) backs the Streamlit demo UI and needs variety for the
#     product dropdown and charts.
#   - The traffic_generator catalog (Product dataclass) drives the Azure Event
#     Hub streaming simulation and is tuned for weighted sampling.
# The shapes differ (dict vs dataclass), so they are not trivially interchangeable.
# If you consolidate, pick one representation and update both consumers.
PRODUCTS = [
    # Electronics
    {
        "id": "ELEC001",
        "name": "MacBook Pro 16 M3",
        "price": 2499.00,
        "category": "Electronics",
        "popularity": 0.15,
    },
    {
        "id": "ELEC002",
        "name": "iPhone 15 Pro Max",
        "price": 1199.00,
        "category": "Electronics",
        "popularity": 0.18,
    },
    {
        "id": "ELEC003",
        "name": "Sony WH-1000XM5 Headphones",
        "price": 349.00,
        "category": "Electronics",
        "popularity": 0.12,
    },
    {
        "id": "ELEC004",
        "name": "iPad Air M2",
        "price": 599.00,
        "category": "Electronics",
        "popularity": 0.10,
    },
    {
        "id": "ELEC005",
        "name": 'Samsung 65" OLED TV',
        "price": 1799.00,
        "category": "Electronics",
        "popularity": 0.06,
    },
    {
        "id": "ELEC006",
        "name": "Apple Watch Ultra 2",
        "price": 799.00,
        "category": "Electronics",
        "popularity": 0.08,
    },
    {
        "id": "ELEC007",
        "name": "AirPods Pro 2",
        "price": 249.00,
        "category": "Electronics",
        "popularity": 0.14,
    },
    {
        "id": "ELEC008",
        "name": "PlayStation 5",
        "price": 499.00,
        "category": "Electronics",
        "popularity": 0.09,
    },
    # Fashion
    {
        "id": "FASH001",
        "name": "Nike Air Jordan 1 Retro",
        "price": 180.00,
        "category": "Fashion",
        "popularity": 0.16,
    },
    {
        "id": "FASH002",
        "name": "Lululemon Align Leggings",
        "price": 98.00,
        "category": "Fashion",
        "popularity": 0.11,
    },
    {
        "id": "FASH003",
        "name": "Ray-Ban Aviator Classic",
        "price": 161.00,
        "category": "Fashion",
        "popularity": 0.08,
    },
    {
        "id": "FASH004",
        "name": "Canada Goose Expedition Parka",
        "price": 1295.00,
        "category": "Fashion",
        "popularity": 0.04,
    },
    {
        "id": "FASH005",
        "name": "Adidas Ultraboost 23",
        "price": 190.00,
        "category": "Fashion",
        "popularity": 0.10,
    },
    {
        "id": "FASH006",
        "name": "Gucci GG Marmont Bag",
        "price": 2300.00,
        "category": "Fashion",
        "popularity": 0.03,
    },
    # Home & Kitchen
    {
        "id": "HOME001",
        "name": "Dyson V15 Detect Vacuum",
        "price": 649.00,
        "category": "Home",
        "popularity": 0.09,
    },
    {
        "id": "HOME002",
        "name": "Vitamix A3500 Blender",
        "price": 649.00,
        "category": "Home",
        "popularity": 0.05,
    },
    {
        "id": "HOME003",
        "name": "Nespresso Vertuo Plus",
        "price": 179.00,
        "category": "Home",
        "popularity": 0.12,
    },
    {
        "id": "HOME004",
        "name": "KitchenAid Stand Mixer",
        "price": 379.00,
        "category": "Home",
        "popularity": 0.07,
    },
    {
        "id": "HOME005",
        "name": "Instant Pot Duo Plus",
        "price": 89.00,
        "category": "Home",
        "popularity": 0.13,
    },
    {
        "id": "HOME006",
        "name": "Roomba j7+ Robot Vacuum",
        "price": 799.00,
        "category": "Home",
        "popularity": 0.06,
    },
    # Sports & Fitness
    {
        "id": "SPRT001",
        "name": "Peloton Bike+",
        "price": 2495.00,
        "category": "Sports",
        "popularity": 0.04,
    },
    {
        "id": "SPRT002",
        "name": "Optimum Nutrition Protein 5lb",
        "price": 64.99,
        "category": "Sports",
        "popularity": 0.15,
    },
    {
        "id": "SPRT003",
        "name": "Theragun Pro",
        "price": 449.00,
        "category": "Sports",
        "popularity": 0.06,
    },
    {
        "id": "SPRT004",
        "name": "Yeti Rambler 30oz",
        "price": 38.00,
        "category": "Sports",
        "popularity": 0.17,
    },
    {
        "id": "SPRT005",
        "name": "Hydro Flask 32oz",
        "price": 44.95,
        "category": "Sports",
        "popularity": 0.14,
    },
]

# Customer archetypes with behavior patterns
ARCHETYPES = {
    "ImpulseBuyer": {
        "description": "Quick decisions, responds to urgency",
        "abandon_rate": 0.25,
        "avg_session_seconds": 120,
        "page_views": (1, 4),
        "recovery_response": "high",
        "trigger_words": ["limited time", "selling fast", "only X left"],
    },
    "WindowShopper": {
        "description": "Browses a lot, rarely buys",
        "abandon_rate": 0.70,
        "avg_session_seconds": 480,
        "page_views": (8, 20),
        "recovery_response": "low",
        "trigger_words": ["free shipping", "no commitment", "save for later"],
    },
    "PriceChecker": {
        "description": "Compares prices, waits for deals",
        "abandon_rate": 0.55,
        "avg_session_seconds": 300,
        "page_views": (5, 12),
        "recovery_response": "medium",
        "trigger_words": ["price match", "discount", "best price"],
    },
    "CommittedBuyer": {
        "description": "Knows what they want, high conversion",
        "abandon_rate": 0.10,
        "avg_session_seconds": 180,
        "page_views": (2, 5),
        "recovery_response": "very_high",
        "trigger_words": ["complete your order", "finish checkout", "reserved for you"],
    },
    "QuickBrowser": {
        "description": "Fast in and out, mobile-first",
        "abandon_rate": 0.45,
        "avg_session_seconds": 60,
        "page_views": (1, 3),
        "recovery_response": "medium",
        "trigger_words": ["quick checkout", "one-click", "mobile exclusive"],
    },
}

GEO_REGIONS = ["NA", "EU", "APAC", "LATAM"]
UTM_SOURCES = ["google", "facebook", "instagram", "tiktok", "email", "direct", "affiliate"]
DEVICES = ["mobile", "desktop", "tablet"]
BROWSERS = ["Chrome", "Safari", "Firefox", "Edge", "Samsung Internet"]
DISCOUNT_CODES = [None, None, None, "SAVE10", "WELCOME20", "FLASH30", "VIP15", "FREESHIP"]


@dataclass
class Customer:
    """Represents a customer with realistic attributes."""

    id: str
    name: str
    email: str
    archetype: str
    is_returning: bool
    geo_region: str
    device: str
    browser: str

    @classmethod
    def generate(cls, archetype: str | None = None, name: str | None = None):
        """Create a new customer with optional overrides."""
        customer_name = name or fake.name()
        arch = archetype or random.choice(list(ARCHETYPES.keys()))

        return cls(
            id=f"cust_{uuid.uuid4().hex[:8]}",
            name=customer_name,
            email=fake.email(),
            archetype=arch,
            is_returning=random.random() < 0.35,
            geo_region=random.choice(GEO_REGIONS),
            device=random.choice(DEVICES),
            browser=random.choice(BROWSERS),
        )


@dataclass
class ShoppingSession:
    """A shopping session with events."""

    session_id: str
    customer: Customer
    product: dict
    utm_source: str
    discount_code: str | None
    session_duration: int
    page_views: int
    events: list = field(default_factory=list)
    is_abandoned: bool = False
    is_converted: bool = False
    abandonment_stage: str | None = None
    recovery_priority: str | None = None

    @classmethod
    def generate(cls, customer: Customer, product: dict | None = None):
        """Create a new shopping session."""
        archetype_config = ARCHETYPES[customer.archetype]
        product = (
            product or random.choices(PRODUCTS, weights=[p["popularity"] for p in PRODUCTS])[0]
        )

        page_views_range = archetype_config["page_views"]

        return cls(
            session_id=f"sess_{uuid.uuid4().hex[:8]}",
            customer=customer,
            product=product,
            utm_source=random.choice(UTM_SOURCES),
            discount_code=random.choice(DISCOUNT_CODES),
            session_duration=int(
                random.gauss(
                    archetype_config["avg_session_seconds"],
                    archetype_config["avg_session_seconds"] * 0.3,
                )
            ),
            page_views=random.randint(*page_views_range),
        )

    def simulate_journey(self) -> list:
        """Simulate a full shopping journey with events."""
        archetype_config = ARCHETYPES[self.customer.archetype]
        abandon_rate = archetype_config["abandon_rate"]

        timestamp = datetime.now()

        # Always starts with page view
        self._add_event("page_view", timestamp)
        timestamp += timedelta(seconds=random.randint(10, 60))

        # Add to cart
        self._add_event("add_to_cart", timestamp)
        timestamp += timedelta(seconds=random.randint(30, 120))

        # Random chance to start checkout
        if random.random() > 0.3:
            self._add_event("checkout_start", timestamp)
            timestamp += timedelta(seconds=random.randint(60, 180))

            # Will they complete or abandon?
            if random.random() > abandon_rate:
                self._add_event("checkout_success", timestamp)
                self.is_converted = True
            else:
                self._abandon_cart(timestamp, "payment")
        else:
            self._abandon_cart(timestamp, "cart")

        return self.events

    def _abandon_cart(self, timestamp: datetime, stage: str):
        """Handle cart abandonment."""
        self.is_abandoned = True
        self.abandonment_stage = stage
        self.recovery_priority = self._calculate_priority()
        self._add_event("cart_abandoned", timestamp)

    def _calculate_priority(self) -> str:
        """Determine recovery priority based on cart value and customer type."""
        cart_value = self.product["price"]
        archetype_response = ARCHETYPES[self.customer.archetype]["recovery_response"]

        if cart_value >= 500 and archetype_response in ["high", "very_high"]:
            return "critical"
        elif cart_value >= 200 or archetype_response == "very_high":
            return "high"
        elif cart_value >= 50 or archetype_response == "medium":
            return "medium"
        else:
            return "low"

    def _add_event(self, event_type: str, timestamp: datetime):
        """Add an event to the session."""
        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:8]}",
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "user_id": self.customer.id,
            "user_name": self.customer.name,
            "session_id": self.session_id,
            "user_archetype": self.customer.archetype,
            "product_id": self.product["id"],
            "product_name": self.product["name"],
            "product_category": self.product["category"],
            "amount": self.product["price"],
            "cart_total": self.product["price"],
            "cart_item_count": 1,
            "device": self.customer.device,
            "browser": self.customer.browser,
            "geo_region": self.customer.geo_region,
            "utm_source": self.utm_source,
            "session_duration_seconds": self.session_duration,
            "page_views_before_cart": self.page_views,
            "is_returning_user": self.customer.is_returning,
            "discount_code_used": self.discount_code,
            "is_abandonment": event_type == "cart_abandoned",
            "is_conversion": event_type == "checkout_success",
            "abandonment_stage": self.abandonment_stage if event_type == "cart_abandoned" else None,
            "recovery_priority": self.recovery_priority if event_type == "cart_abandoned" else None,
        }
        self.events.append(event)


def generate_sample_data(num_sessions: int = 100) -> list:
    """Generate a batch of sample shopping sessions."""
    all_events = []

    for _ in range(num_sessions):
        customer = Customer.generate()
        session = ShoppingSession.generate(customer)
        events = session.simulate_journey()
        all_events.extend(events)

    return all_events


def generate_user_session(name: str, archetype: str, product_name: str) -> ShoppingSession:
    """Generate a session for a specific user (Try It Yourself mode)."""
    customer = Customer.generate(archetype=archetype, name=name)

    # Find the product by name
    product = next((p for p in PRODUCTS if p["name"] == product_name), PRODUCTS[0])

    session = ShoppingSession.generate(customer, product)
    return session


if __name__ == "__main__":
    # Test data generation
    events = generate_sample_data(10)
    print(f"Generated {len(events)} events")

    # Show sample
    for event in events[:3]:
        print(
            f"  {event['event_type']}: {event['user_name']} - {event['product_name']} (${event['cart_total']})"
        )
