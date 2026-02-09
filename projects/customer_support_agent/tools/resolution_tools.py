"""Tools for generating resolution summaries and predicting CSAT scores.

These tools are used by the Resolution & CSAT Agent to compile
the final resolution report and predict customer satisfaction.
"""

import json
import logging
from datetime import datetime, timezone

from agents import RunContextWrapper, function_tool
from customer_support_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


@function_tool
def generate_resolution_summary(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Generate a comprehensive resolution summary for the support interaction.

    Compiles all actions taken, findings, and outcomes into a structured
    resolution report. This is used for internal tracking and quality assurance.

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string with the resolution summary.
    """
    scenario = ctx.context
    logger.info(
        "Generating resolution summary for ticket: %s",
        scenario.ticket.ticket_id if scenario.ticket else "N/A",
    )

    ticket = scenario.ticket

    summary = {
        "ticket_id": ticket.ticket_id if ticket else "N/A",
        "customer_id": scenario.customer.customer_id,
        "customer_name": scenario.customer.name,
        "customer_tier": scenario.customer.tier,
        "scenario_type": scenario.scenario_type,
        "category": ticket.category if ticket else "unknown",
        "priority": ticket.priority if ticket else "medium",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "interaction_context": {
            "original_query": (
                scenario.customer_query[:200] + "..."
                if len(scenario.customer_query) > 200
                else scenario.customer_query
            ),
            "orders_reviewed": len(scenario.orders),
            "returns_processed": len(scenario.returns),
            "billing_items_reviewed": len(scenario.invoices) + len(scenario.payments),
            "kb_articles_available": len(scenario.knowledge_base),
        },
        "resolution_template": {
            "status": "pending_agent_input",
            "note": "The agent should fill in the actions taken and resolution details based on the interaction.",
        },
    }

    logger.info("Resolution summary generated for %s", summary["ticket_id"])
    return json.dumps(summary, indent=2)


@function_tool
def predict_csat_score(
    ctx: RunContextWrapper[ScenarioData],
    resolution_quality: str,
    response_time: str,
    issue_resolved: bool,
    escalated: bool,
) -> str:
    """Predict the customer satisfaction (CSAT) score for the interaction.

    Uses the customer profile, issue type, resolution quality, and
    response metrics to predict the likely CSAT score (1-5 scale).

    Args:
        ctx: Run context containing the scenario data.
        resolution_quality: Quality assessment ('excellent', 'good', 'fair', 'poor').
        response_time: Response time assessment ('fast', 'acceptable', 'slow').
        issue_resolved: Whether the issue was fully resolved.
        escalated: Whether the case was escalated to a human.

    Returns:
        str: JSON string with predicted CSAT score and contributing factors.
    """
    scenario = ctx.context
    logger.info(
        "Predicting CSAT: quality=%s, time=%s, resolved=%s, escalated=%s",
        resolution_quality,
        response_time,
        issue_resolved,
        escalated,
    )

    base_score = 3.0
    factors: list[str] = []

    # Resolution quality impact
    quality_impact = {
        "excellent": 1.5,
        "good": 0.8,
        "fair": 0.0,
        "poor": -1.5,
    }
    quality_delta = quality_impact.get(resolution_quality, 0.0)
    base_score += quality_delta
    factors.append(f"Resolution quality ({resolution_quality}): {quality_delta:+.1f}")

    # Response time impact
    time_impact = {
        "fast": 0.5,
        "acceptable": 0.0,
        "slow": -0.8,
    }
    time_delta = time_impact.get(response_time, 0.0)
    base_score += time_delta
    factors.append(f"Response time ({response_time}): {time_delta:+.1f}")

    # Resolution impact
    if issue_resolved:
        base_score += 0.5
        factors.append("Issue fully resolved: +0.5")
    else:
        base_score -= 1.0
        factors.append("Issue not fully resolved: -1.0")

    # Escalation impact (slight negative - customer preferred AI resolution)
    if escalated:
        base_score -= 0.3
        factors.append("Required escalation to human: -0.3")

    # Customer tier impact (higher tier = higher expectations)
    tier_adjustment = {
        "platinum": -0.3,
        "gold": -0.1,
        "silver": 0.0,
        "bronze": 0.2,
    }
    tier_delta = tier_adjustment.get(scenario.customer.tier, 0.0)
    base_score += tier_delta
    factors.append(
        f"Customer tier ({scenario.customer.tier}) expectation adjustment: {tier_delta:+.1f}"
    )

    # Clamp to 1-5
    final_score = max(1, min(5, round(base_score)))

    # Satisfaction label
    satisfaction_labels = {
        1: "Very Dissatisfied",
        2: "Dissatisfied",
        3: "Neutral",
        4: "Satisfied",
        5: "Very Satisfied",
    }

    result = {
        "predicted_score": final_score,
        "raw_score": round(base_score, 2),
        "predicted_satisfaction": satisfaction_labels[final_score],
        "factors": factors,
        "customer_id": scenario.customer.customer_id,
        "customer_tier": scenario.customer.tier,
        "recommendation": _get_follow_up_recommendation(
            final_score, scenario.customer.tier
        ),
    }

    logger.info(
        "CSAT prediction: score=%d (%s)", final_score, satisfaction_labels[final_score]
    )
    return json.dumps(result, indent=2)


def _get_follow_up_recommendation(score: int, tier: str) -> str:
    """Get a follow-up recommendation based on CSAT score and tier.

    Args:
        score: Predicted CSAT score (1-5).
        tier: Customer loyalty tier.

    Returns:
        str: Recommended follow-up action.
    """
    is_premium = tier in ("platinum", "gold")

    if score <= 2:
        if is_premium:
            return "URGENT: Schedule follow-up call with account manager within 24 hours. Consider compensation or loyalty credit."
        return "Schedule follow-up email within 48 hours. Offer discount code for next purchase."

    if score == 3:
        if is_premium:
            return "Send personalized follow-up email within 24 hours. Check if additional assistance needed."
        return "Send automated satisfaction survey in 24 hours."

    return "No immediate follow-up needed. Include in weekly satisfaction report."
