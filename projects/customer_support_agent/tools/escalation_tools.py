"""Tools for escalation management and human agent handoff.

These tools are used by the Escalation Agent to create escalation
tickets, check agent availability, and route complex cases to humans.
"""

import json
import logging
from datetime import datetime, timezone

from agents import RunContextWrapper, function_tool

from customer_support_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


@function_tool
def escalate_to_human(
    ctx: RunContextWrapper[ScenarioData],
    reason: str,
    priority: str,
) -> str:
    """Create a human escalation request for complex or unresolved issues.

    Routes the case to a human support agent with full context.
    Use this when the AI agent cannot fully resolve the issue or
    the customer explicitly requests a human agent.

    Args:
        ctx: Run context containing the scenario data.
        reason: Detailed reason for escalation.
        priority: Escalation priority ('low', 'medium', 'high', 'urgent').

    Returns:
        str: JSON string with escalation request details.
    """
    scenario = ctx.context
    logger.info("Escalating to human: priority=%s, reason=%s", priority, reason)

    valid_priorities = {"low", "medium", "high", "urgent"}
    if priority not in valid_priorities:
        priority = "medium"

    # Determine assigned team based on ticket category
    ticket_category = scenario.ticket.category if scenario.ticket else "general_inquiry"
    team_map = {
        "order_issue": "Order Fulfillment Team",
        "billing_issue": "Billing & Finance Team",
        "technical_issue": "Technical Support L2",
        "complaint": "Customer Success Team",
        "general_inquiry": "General Support",
        "feedback": "Product Team",
    }
    assigned_team = team_map.get(ticket_category, "General Support")

    # For complex multi-issue cases, route to Customer Success
    if scenario.scenario_type == "complex_escalation":
        assigned_team = "Customer Success Team (Senior)"

    escalation_id = f"ESC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"

    result = {
        "escalation_id": escalation_id,
        "ticket_id": scenario.ticket.ticket_id if scenario.ticket else "N/A",
        "customer_id": scenario.customer.customer_id,
        "customer_tier": scenario.customer.tier,
        "priority": priority,
        "assigned_team": assigned_team,
        "reason": reason,
        "status": "queued",
        "estimated_response_time": _estimate_response_time(priority, scenario.customer.tier),
        "message": (
            f"Escalation {escalation_id} created. Case assigned to {assigned_team}. "
            f"A human agent will review this case within the estimated response time."
        ),
    }

    logger.info("Escalation created: %s -> %s", escalation_id, assigned_team)
    return json.dumps(result, indent=2)


def _estimate_response_time(priority: str, customer_tier: str) -> str:
    """Estimate response time based on priority and customer tier.

    Args:
        priority: Escalation priority level.
        customer_tier: Customer loyalty tier.

    Returns:
        str: Estimated response time as a human-readable string.
    """
    # Platinum/gold customers get faster response
    is_premium = customer_tier in ("platinum", "gold")

    match priority:
        case "urgent":
            return "15 minutes" if is_premium else "30 minutes"
        case "high":
            return "30 minutes" if is_premium else "1 hour"
        case "medium":
            return "1 hour" if is_premium else "2 hours"
        case _:
            return "2 hours" if is_premium else "4 hours"


@function_tool
def get_agent_availability(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Check human agent availability across support teams.

    Returns the current availability of human support agents
    organized by team, useful for setting customer expectations.

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string with agent availability information.
    """
    logger.info("Checking agent availability")

    # Simulated availability
    availability = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "teams": {
            "General Support": {
                "agents_online": 5,
                "agents_busy": 3,
                "agents_available": 2,
                "avg_wait_time": "8 minutes",
                "queue_length": 4,
            },
            "Order Fulfillment Team": {
                "agents_online": 3,
                "agents_busy": 2,
                "agents_available": 1,
                "avg_wait_time": "12 minutes",
                "queue_length": 6,
            },
            "Billing & Finance Team": {
                "agents_online": 2,
                "agents_busy": 2,
                "agents_available": 0,
                "avg_wait_time": "20 minutes",
                "queue_length": 8,
            },
            "Technical Support L2": {
                "agents_online": 4,
                "agents_busy": 3,
                "agents_available": 1,
                "avg_wait_time": "10 minutes",
                "queue_length": 3,
            },
            "Customer Success Team": {
                "agents_online": 2,
                "agents_busy": 1,
                "agents_available": 1,
                "avg_wait_time": "5 minutes",
                "queue_length": 1,
            },
            "Customer Success Team (Senior)": {
                "agents_online": 1,
                "agents_busy": 0,
                "agents_available": 1,
                "avg_wait_time": "3 minutes",
                "queue_length": 0,
            },
        },
        "overall_status": "normal",
    }

    logger.info("Agent availability checked: overall=%s", availability["overall_status"])
    return json.dumps(availability, indent=2)


@function_tool
def create_escalation_ticket(
    ctx: RunContextWrapper[ScenarioData],
    reason: str,
    priority: str,
    assigned_team: str,
    notes: str,
) -> str:
    """Create a formal escalation ticket in the ticketing system.

    Creates a detailed escalation ticket with all context needed for
    the human agent to pick up the case efficiently.

    Args:
        ctx: Run context containing the scenario data.
        reason: Detailed reason for escalation.
        priority: Ticket priority ('low', 'medium', 'high', 'urgent').
        assigned_team: Team to assign the escalation to.
        notes: Additional context and notes for the human agent.

    Returns:
        str: JSON string with escalation ticket details.
    """
    scenario = ctx.context
    logger.info("Creating escalation ticket: team=%s, priority=%s", assigned_team, priority)

    ticket_id = f"ESCTKT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    result = {
        "escalation_ticket_id": ticket_id,
        "original_ticket_id": scenario.ticket.ticket_id if scenario.ticket else "N/A",
        "customer_id": scenario.customer.customer_id,
        "customer_name": scenario.customer.name,
        "customer_tier": scenario.customer.tier,
        "priority": priority,
        "assigned_team": assigned_team,
        "reason": reason,
        "notes": notes,
        "status": "created",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "context": {
            "scenario_type": scenario.scenario_type,
            "orders_count": len(scenario.orders),
            "returns_count": len(scenario.returns),
            "active_subscriptions": len(scenario.subscriptions),
        },
        "message": f"Escalation ticket {ticket_id} created and assigned to {assigned_team}.",
    }

    logger.info("Escalation ticket created: %s", ticket_id)
    return json.dumps(result, indent=2)
