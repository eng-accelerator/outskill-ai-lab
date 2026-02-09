"""Customer profile and sentiment data models.

Defines customer-related types used throughout the support agent system,
including customer tiers, profiles, and sentiment analysis results.
"""

from dataclasses import dataclass, field
from typing import Literal

# Customer loyalty tiers
CustomerTier = Literal["bronze", "silver", "gold", "platinum"]

# Sentiment levels for customer message analysis
SentimentLevel = Literal[
    "very_negative",
    "negative",
    "neutral",
    "positive",
    "very_positive",
]

# Preferred contact methods
ContactMethod = Literal["email", "phone", "chat", "sms"]


@dataclass(frozen=True)
class CustomerProfile:
    """A customer profile from the CRM system.

    Attributes:
        customer_id: Unique customer identifier.
        name: Full name of the customer.
        email: Email address.
        phone: Phone number.
        tier: Loyalty tier level.
        account_age_days: Number of days since account creation.
        total_orders: Total number of orders placed.
        total_spent: Total amount spent in dollars.
        preferred_contact: Preferred contact method.
        notes: Internal notes about the customer.
    """

    customer_id: str
    name: str
    email: str
    phone: str
    tier: CustomerTier
    account_age_days: int
    total_orders: int
    total_spent: float
    preferred_contact: ContactMethod = "email"
    notes: str = ""


@dataclass(frozen=True)
class SentimentScore:
    """Sentiment analysis result for a customer message.

    Attributes:
        level: Categorical sentiment level.
        score: Numeric sentiment score from -1.0 (very negative) to 1.0 (very positive).
        indicators: Key phrases or signals that contributed to the score.
    """

    level: SentimentLevel
    score: float
    indicators: list[str] = field(default_factory=list)
