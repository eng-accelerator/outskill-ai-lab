"""Tools for fetching alerts and service health data.

These tools are used by the Triage Agent to assess the current
state of the system and classify incidents.
"""

import json
import logging
from dataclasses import asdict

from agents import RunContextWrapper, function_tool

from aiops_incident_response_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


@function_tool
def fetch_active_alerts(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Fetch all currently active alerts from the monitoring system.

    Returns a JSON list of active alerts with their severity, service,
    message, timestamp, and labels. Use this to understand what alerts
    have fired and their severity levels.

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string of active alerts.
    """
    scenario = ctx.context
    logger.info("Fetching %d active alerts", len(scenario.alerts))
    alerts_data = [asdict(a) for a in scenario.alerts]
    return json.dumps(alerts_data, indent=2)


@function_tool
def get_service_health_summary(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Get the current health summary for all services.

    Returns a JSON list of service health records including status,
    CPU/memory usage, error rates, latency, and active alert counts.
    Use this to identify which services are degraded or critical.

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string of service health records.
    """
    scenario = ctx.context
    logger.info("Fetching health summary for %d services", len(scenario.service_health))
    health_data = [asdict(h) for h in scenario.service_health]
    return json.dumps(health_data, indent=2)
