"""Tools for knowledge base search, system status, and diagnostics.

These tools are used by the Technical Support Agent to find solutions,
check system health, and diagnose customer account issues.
"""

import json
import logging
from dataclasses import asdict

from agents import RunContextWrapper, function_tool
from customer_support_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


@function_tool
def search_knowledge_base(ctx: RunContextWrapper[ScenarioData], query: str) -> str:
    """Search the knowledge base for relevant articles and documentation.

    Performs keyword-based search across FAQ entries and technical documentation
    to find solutions for customer issues. Returns the most relevant articles.

    Args:
        ctx: Run context containing the scenario data.
        query: The search query (e.g., 'login issues', 'refund policy').

    Returns:
        str: JSON string with matching knowledge base articles.
    """
    scenario = ctx.context
    logger.info("Searching knowledge base for: %s", query)

    query_lower = query.lower()
    query_words = set(query_lower.split())

    scored_articles: list[tuple[float, dict]] = []

    for article in scenario.knowledge_base:
        score = 0.0

        # Check title match
        title_lower = article.title.lower()
        for word in query_words:
            if word in title_lower:
                score += 3.0

        # Check tag match
        for tag in article.tags:
            tag_lower = tag.lower()
            for word in query_words:
                if word in tag_lower or tag_lower in query_lower:
                    score += 2.0

        # Check content match
        content_lower = article.content.lower()
        for word in query_words:
            if len(word) > 3 and word in content_lower:
                score += 1.0

        # Boost by helpfulness
        score += article.helpful_count / 1000.0

        if score > 0:
            scored_articles.append((score, asdict(article)))

    # Sort by score descending, take top 3
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    top_articles = [article for _, article in scored_articles[:3]]

    result = {
        "query": query,
        "results_count": len(top_articles),
        "articles": top_articles,
    }

    logger.info(
        "Knowledge base search returned %d results for '%s'", len(top_articles), query
    )
    return json.dumps(result, indent=2)


@function_tool
def get_system_status(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Check the current system status and known issues.

    Returns the current operational status of all services including
    any active incidents, degraded performance, or scheduled maintenance.

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string with system status information.
    """
    logger.info("Checking system status")

    # Simulated system status
    status = {
        "overall_status": "partial_outage",
        "last_updated": "2024-12-15T10:30:00Z",
        "services": {
            "web_application": {
                "status": "operational",
                "uptime_30d": "99.95%",
            },
            "api_gateway": {
                "status": "degraded",
                "uptime_30d": "99.2%",
                "note": "Intermittent 401 errors for some API keys. Engineering investigating.",
            },
            "authentication_service": {
                "status": "degraded",
                "uptime_30d": "99.5%",
                "note": "Password reset emails delayed up to 30 minutes due to email provider issues.",
            },
            "payment_processing": {
                "status": "operational",
                "uptime_30d": "99.99%",
            },
            "order_management": {
                "status": "operational",
                "uptime_30d": "99.97%",
            },
            "notification_service": {
                "status": "degraded",
                "uptime_30d": "98.5%",
                "note": "Email notifications delayed. SMS notifications unaffected.",
            },
        },
        "active_incidents": [
            {
                "incident_id": "INC-2024-0089",
                "title": "API Authentication Intermittent Failures",
                "severity": "medium",
                "started_at": "2024-12-15T08:00:00Z",
                "description": "Some API keys experiencing intermittent 401 errors. Root cause identified as a caching issue. Fix being deployed.",
                "eta_resolution": "2024-12-15T14:00:00Z",
            },
            {
                "incident_id": "INC-2024-0090",
                "title": "Password Reset Email Delays",
                "severity": "low",
                "started_at": "2024-12-15T06:00:00Z",
                "description": "Password reset emails are delayed by up to 30 minutes due to our email provider experiencing high volume.",
                "eta_resolution": "2024-12-15T12:00:00Z",
            },
        ],
        "scheduled_maintenance": [],
    }

    logger.info("System status: %s", status["overall_status"])
    return json.dumps(status, indent=2)


@function_tool
def run_diagnostics(ctx: RunContextWrapper[ScenarioData], customer_id: str) -> str:
    """Run account diagnostics for a customer.

    Performs automated checks on the customer's account including
    authentication status, API key validity, subscription status,
    and recent activity patterns.

    Args:
        ctx: Run context containing the scenario data.
        customer_id: The customer ID to diagnose.

    Returns:
        str: JSON string with diagnostic results.
    """
    scenario = ctx.context
    logger.info("Running diagnostics for customer: %s", customer_id)

    # Find customer
    customer = None
    if scenario.customer.customer_id == customer_id:
        customer = scenario.customer
    else:
        for c in scenario.all_customers:
            if c.customer_id == customer_id:
                customer = c
                break

    if customer is None:
        return json.dumps({"error": f"Customer {customer_id} not found"})

    # Simulate diagnostics based on scenario
    diagnostics = {
        "customer_id": customer_id,
        "account_status": "active",
        "checks": {
            "authentication": {
                "status": "warning",
                "details": "Last successful login: 2 days ago. 3 failed login attempts in last 24 hours.",
                "recommendation": "Account may be locked after 5 failed attempts. Consider manual unlock.",
            },
            "api_keys": {
                "status": (
                    "warning" if scenario.scenario_type == "technical_issue" else "ok"
                ),
                "details": (
                    (
                        "API key last used: 24 hours ago. Current API gateway status: DEGRADED. "
                        "Known issue: intermittent 401 errors affecting some keys."
                    )
                    if scenario.scenario_type == "technical_issue"
                    else "API key active and functioning normally."
                ),
                "recommendation": (
                    "Wait for API gateway fix (ETA: 4 hours) or regenerate API key."
                    if scenario.scenario_type == "technical_issue"
                    else "No action needed."
                ),
            },
            "subscription": {
                "status": "ok",
                "details": f"Active {scenario.subscriptions[0].plan if scenario.subscriptions else 'free'} plan.",
            },
            "email_delivery": {
                "status": "warning",
                "details": "Email service experiencing delays (up to 30 min). Password reset emails affected.",
                "recommendation": "Check spam folder. If not received in 30 minutes, try again or use alternative recovery.",
            },
            "recent_activity": {
                "status": "ok",
                "details": f"Last order: {scenario.orders[0].order_id if scenario.orders else 'None'}. Account in good standing.",
            },
        },
        "overall_health": "needs_attention",
        "summary": (
            "Account is active but experiencing issues related to known system incidents. "
            "API authentication and email delivery are currently degraded system-wide."
        ),
    }

    logger.info(
        "Diagnostics complete for %s: overall=%s",
        customer_id,
        diagnostics["overall_health"],
    )
    return json.dumps(diagnostics, indent=2)
