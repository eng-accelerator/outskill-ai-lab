"""Tools for fetching customer profiles and analyzing sentiment.

These tools are used by the Intake & Router Agent to understand
the customer context and emotional state of the interaction.
"""

import json
import logging
from dataclasses import asdict

from agents import RunContextWrapper, function_tool
from customer_support_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)

# Simple keyword-based sentiment indicators
_NEGATIVE_INDICATORS = [
    "frustrated",
    "angry",
    "disappointed",
    "terrible",
    "awful",
    "unacceptable",
    "worst",
    "horrible",
    "furious",
    "disgusted",
    "ridiculous",
    "outrageous",
    "scam",
    "rip off",
    "waste",
]

_VERY_NEGATIVE_INDICATORS = [
    "extremely frustrated",
    "absolutely furious",
    "cancelling everything",
    "legal action",
    "lawsuit",
    "bbb complaint",
    "never again",
    "demand",
    "immediately",
    "now",
]

_POSITIVE_INDICATORS = [
    "thank",
    "appreciate",
    "great",
    "excellent",
    "wonderful",
    "helpful",
    "amazing",
    "love",
    "fantastic",
    "pleased",
]


@function_tool
def fetch_customer_profile(
    ctx: RunContextWrapper[ScenarioData], customer_id: str
) -> str:
    """Fetch a customer profile from the CRM system.

    Retrieves the full customer profile including tier, spending history,
    account age, and internal notes. Use this to understand the customer's
    value and history with the company.

    Args:
        ctx: Run context containing the scenario data.
        customer_id: The customer ID to look up.

    Returns:
        str: JSON string of the customer profile, or error message if not found.
    """
    scenario = ctx.context
    logger.info("Fetching customer profile: %s", customer_id)

    # Check primary customer first
    if scenario.customer.customer_id == customer_id:
        return json.dumps(asdict(scenario.customer), indent=2)

    # Search all customers
    for cust in scenario.all_customers:
        if cust.customer_id == customer_id:
            return json.dumps(asdict(cust), indent=2)

    logger.warning("Customer not found: %s", customer_id)
    return json.dumps({"error": f"Customer {customer_id} not found"})


@function_tool
def analyze_sentiment(ctx: RunContextWrapper[ScenarioData], message: str) -> str:
    """Analyze the sentiment of a customer message.

    Performs keyword-based sentiment analysis on the customer's message
    to determine their emotional state. Returns a sentiment score and
    the key indicators that contributed to the assessment.

    Args:
        ctx: Run context containing the scenario data.
        message: The customer message to analyze.

    Returns:
        str: JSON string with sentiment level, score, and indicators.
    """
    logger.info("Analyzing sentiment for message of length %d", len(message))
    message_lower = message.lower()

    found_indicators: list[str] = []
    score = 0.0

    # Check for very negative indicators first
    for indicator in _VERY_NEGATIVE_INDICATORS:
        if indicator in message_lower:
            found_indicators.append(f"very_negative: '{indicator}'")
            score -= 0.3

    # Check negative indicators
    for indicator in _NEGATIVE_INDICATORS:
        if indicator in message_lower:
            found_indicators.append(f"negative: '{indicator}'")
            score -= 0.15

    # Check positive indicators
    for indicator in _POSITIVE_INDICATORS:
        if indicator in message_lower:
            found_indicators.append(f"positive: '{indicator}'")
            score += 0.2

    # Clamp score
    score = max(-1.0, min(1.0, score))

    # Determine level
    if score <= -0.6:
        level = "very_negative"
    elif score <= -0.2:
        level = "negative"
    elif score <= 0.2:
        level = "neutral"
    elif score <= 0.6:
        level = "positive"
    else:
        level = "very_positive"

    # Check for urgency markers
    urgency_words = ["urgent", "asap", "immediately", "right now", "blocking"]
    for word in urgency_words:
        if word in message_lower:
            found_indicators.append(f"urgency: '{word}'")

    result = {
        "level": level,
        "score": round(score, 2),
        "indicators": found_indicators,
    }

    logger.info("Sentiment analysis result: level=%s, score=%.2f", level, score)
    return json.dumps(result, indent=2)
