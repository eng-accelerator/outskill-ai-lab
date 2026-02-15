"""Tools for fetching security alerts and asset inventory.

These tools are used by the Alert Intake Agent to assess the current
security posture and classify incoming threats.
"""

import json
import logging
from dataclasses import asdict

from agents import RunContextWrapper, function_tool
from cybersecurity_threat_detection_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


@function_tool
def fetch_security_alerts(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Fetch all active security alerts from the SIEM.

    Returns a JSON list of active security alerts with their severity,
    category, message, indicators, and source system. Use this to
    understand what threats have been detected.

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string of active security alerts.
    """
    scenario = ctx.context
    logger.info("Fetching %d security alerts", len(scenario.alerts))
    alerts_data = [asdict(a) for a in scenario.alerts]
    return json.dumps(alerts_data, indent=2)


@function_tool
def get_asset_inventory(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Get the asset inventory for the environment.

    Returns a JSON list of assets with their hostname, IP address,
    type, owner, and criticality level. Use this to understand which
    assets are involved and their business importance.

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string of asset information.
    """
    scenario = ctx.context
    logger.info("Fetching asset inventory: %d assets", len(scenario.assets))
    assets_data = [asdict(a) for a in scenario.assets]
    return json.dumps(assets_data, indent=2)
