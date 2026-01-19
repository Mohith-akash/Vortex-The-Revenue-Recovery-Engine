"""
AI Recovery Module - Uses Cerebras LLM for personalized cart recovery messages.
Uses Llama 3.1 8B (cheapest model at $0.10/M tokens) to conserve tokens.
Falls back to templates if API is unavailable.
"""

import os
from typing import Optional
from dataclasses import dataclass

# Try to import Cerebras SDK
try:
    from cerebras.cloud.sdk import Cerebras
    CEREBRAS_AVAILABLE = True
except ImportError:
    CEREBRAS_AVAILABLE = False
    Cerebras = None


@dataclass
class RecoveryContext:
    """Context for generating a recovery message."""
    customer_name: str
    customer_archetype: str
    product_name: str
    product_category: str
    cart_total: float
    abandonment_stage: str
    is_returning: bool
    discount_code: Optional[str]
    utm_source: str
    session_duration: int
    page_views: int


# Archetype-specific prompts
ARCHETYPE_PERSONAS = {
    "ImpulseBuyer": "They respond to urgency and FOMO. Create excitement and scarcity.",
    "WindowShopper": "They need reassurance and low commitment. Emphasize no-pressure and free returns.",
    "PriceChecker": "They want the best deal. Highlight value, price matching, and discounts.",
    "CommittedBuyer": "They were ready to buy. Just remind them gently and make checkout easy.",
    "QuickBrowser": "They're mobile and time-poor. Keep it ultra-short and offer quick checkout.",
}

# Fallback templates when AI is not available
FALLBACK_TEMPLATES = {
    "ImpulseBuyer": "🔥 {name}, your {product} is selling fast! Only a few left. Complete your ${total:.2f} order now before it's gone!",
    "WindowShopper": "Hey {name}! Your {product} is saved in your cart. No rush - take your time. Free returns if you change your mind! 💚",
    "PriceChecker": "💰 {name}, we've got a deal for you! Get {discount} off your {product}. That's ${total:.2f} → ${discounted:.2f}!",
    "CommittedBuyer": "Hi {name}, you're just one click away! Your {product} is waiting at checkout. Let's finish up? 🛒",
    "QuickBrowser": "⚡ {name} - Quick checkout for your {product}: ${total:.2f}. Tap to complete →",
}


class AIRecoveryEngine:
    """Generate AI-powered recovery messages using Cerebras Llama 3.1 8B."""
    
    # Use Llama 3.1 8B - cheapest model at $0.10/M tokens
    MODEL = "llama-3.1-8b"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("CEREBRAS_API_KEY")
        self.client = None
        self.is_connected = False
        
        if self.api_key and CEREBRAS_AVAILABLE:
            try:
                self.client = Cerebras(api_key=self.api_key)
                self.is_connected = True
            except Exception:
                self.client = None
    
    def generate_message(self, context: RecoveryContext) -> dict:
        """
        Generate a personalized recovery message.
        Returns dict with 'message', 'channel', and 'is_ai_generated'.
        """
        if self.client:
            return self._generate_ai_message(context)
        else:
            return self._generate_template_message(context)
    
    def _generate_ai_message(self, context: RecoveryContext) -> dict:
        """Use Cerebras LLM to generate personalized message."""
        
        persona = ARCHETYPE_PERSONAS.get(context.customer_archetype, "Be helpful and friendly.")
        
        prompt = f"""Generate ONE cart recovery message for:

Customer: {context.customer_name} ({context.customer_archetype})
Product: {context.product_name} (${context.cart_total:.2f})
{"Discount: " + context.discount_code if context.discount_code else ""}

Style: {persona}

Rules:
- Write ONLY the message text, nothing else
- Max 35 words
- Include their first name
- One clear call-to-action
- Use 1-2 relevant emoji

Output the message only, no quotes, no alternatives, no explanations."""

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "You output ONLY the recovery message text. No commentary, no quotes, no alternatives. Just the message."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=60,
                temperature=0.7,
            )
            
            message = response.choices[0].message.content.strip()
            
            # Clean up the response - remove quotes
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1]
            if message.startswith("'") and message.endswith("'"):
                message = message[1:-1]
            
            # Remove any "Alternatively..." or "Here's..." prefix/suffix
            cutoff_phrases = [
                "Alternatively,", "Here's", "Another option", "Or you could",
                "Note:", "P.S.", "---", "Option 2", "Message:", "Here is"
            ]
            for phrase in cutoff_phrases:
                if phrase in message:
                    message = message.split(phrase)[0].strip()
            
            # Take only the first sentence/paragraph if multiple
            if "\n\n" in message:
                message = message.split("\n\n")[0].strip()
            
            # Remove trailing incomplete sentences
            if message.endswith(("could", "would", "should", "might", "can")):
                message = message.rsplit(".", 1)[0] + "." if "." in message else message
            
            return {
                "message": message,
                "channel": self._select_channel(context),
                "is_ai_generated": True,
                "model": self.MODEL,
            }
            
        except Exception:
            return self._generate_template_message(context)
    
    def _generate_template_message(self, context: RecoveryContext) -> dict:
        """Fallback to template-based messages."""
        
        template = FALLBACK_TEMPLATES.get(
            context.customer_archetype,
            "Hi {name}! Your {product} is waiting. Complete your order: ${total:.2f}"
        )
        
        # Calculate discounted price if applicable
        discount_pct = 0
        if context.discount_code:
            if "10" in context.discount_code:
                discount_pct = 0.10
            elif "15" in context.discount_code:
                discount_pct = 0.15
            elif "20" in context.discount_code:
                discount_pct = 0.20
            elif "30" in context.discount_code:
                discount_pct = 0.30
        
        discounted = context.cart_total * (1 - discount_pct)
        
        message = template.format(
            name=context.customer_name.split()[0],  # First name only
            product=context.product_name,
            total=context.cart_total,
            discount=context.discount_code or "10%",
            discounted=discounted,
        )
        
        return {
            "message": message,
            "channel": self._select_channel(context),
            "is_ai_generated": False,
            "model": "template",
        }
    
    def _select_channel(self, context: RecoveryContext) -> str:
        """Choose the best channel based on priority and cart value."""
        if context.cart_total >= 500:
            return "sms"  # High value = direct channel
        elif context.customer_archetype == "QuickBrowser":
            return "push"  # Mobile-first users
        elif context.is_returning:
            return "email"  # Known customers
        else:
            return "push"  # Default for new visitors


def create_recovery_context_from_event(event: dict) -> RecoveryContext:
    """Create a RecoveryContext from an event dictionary."""
    return RecoveryContext(
        customer_name=event.get("user_name", "Customer"),
        customer_archetype=event.get("user_archetype", "ImpulseBuyer"),
        product_name=event.get("product_name", "your item"),
        product_category=event.get("product_category", "General"),
        cart_total=event.get("cart_total", 0),
        abandonment_stage=event.get("abandonment_stage", "cart"),
        is_returning=event.get("is_returning_user", False),
        discount_code=event.get("discount_code_used"),
        utm_source=event.get("utm_source", "direct"),
        session_duration=event.get("session_duration_seconds", 0),
        page_views=event.get("page_views_before_cart", 0),
    )


# Singleton instance
_engine = None

def get_recovery_engine() -> AIRecoveryEngine:
    """Get or create the recovery engine singleton."""
    global _engine
    if _engine is None:
        _engine = AIRecoveryEngine()
    return _engine


if __name__ == "__main__":
    # Test the recovery engine
    engine = AIRecoveryEngine()
    
    test_context = RecoveryContext(
        customer_name="Sarah Johnson",
        customer_archetype="WindowShopper",
        product_name="Sony WH-1000XM5 Headphones",
        product_category="Electronics",
        cart_total=349.00,
        abandonment_stage="payment",
        is_returning=True,
        discount_code="SAVE10",
        utm_source="google",
        session_duration=480,
        page_views=12,
    )
    
    result = engine.generate_message(test_context)
    print(f"Channel: {result['channel']}")
    print(f"AI Generated: {result['is_ai_generated']}")
    print(f"Message: {result['message']}")
