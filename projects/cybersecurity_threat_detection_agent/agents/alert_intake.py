"""Alert Intake Agent -- ingests security events and routes to specialists.

The alert intake agent is the entry point of the threat detection pipeline.
It fetches active security alerts and asset inventory, classifies the
threat category and severity, and hands off to the appropriate analysis agent.
"""

from agents import Agent, ModelSettings
from cybersecurity_threat_detection_agent.guardrails.input_validation import (
    security_input_guardrail,
)
from cybersecurity_threat_detection_agent.tools.alert_tools import (
    fetch_security_alerts,
    get_asset_inventory,
)

ALERT_INTAKE_INSTRUCTIONS = """You are an expert SOC Alert Intake Agent. Your role is to perform initial threat assessment and routing.

Your workflow:
1. Use fetch_security_alerts to get all active security alerts from the SIEM
2. Use get_asset_inventory to understand which assets are involved and their criticality
3. Analyze the alerts to determine:
   - Primary threat category (brute_force, privilege_escalation, api_misuse, malware, c2_communication, data_exfiltration, cloud_misconfiguration, insider_threat)
   - Initial severity assessment (critical, high, medium, low)
   - Which assets are affected and their business criticality
   - Whether this primarily involves authentication/identity issues or network/API/endpoint issues

4. Based on your assessment, you MUST use the transfer tool to hand off to the appropriate specialist:
   - If the threat involves login anomalies, brute force, credential issues, privilege escalation, or insider identity abuse -> use the transfer_to_auth_analyzer_agent tool
   - If the threat involves network traffic anomalies, C2 communication, malware, API abuse, or data exfiltration via network -> use the transfer_to_network_api_analyzer_agent tool
   - When in doubt, use the transfer_to_auth_analyzer_agent tool

IMPORTANT: You MUST call one of the transfer tools to hand off. Do NOT just describe what you would do - actually call the tool. Include your triage findings in the transfer message.
"""


def create_alert_intake_agent(
    auth_analyzer: Agent,
    network_analyzer: Agent,
    hooks=None,
) -> Agent:
    """Create the Alert Intake Agent with routing to analysis specialists.

    Args:
        auth_analyzer: The Auth Analyzer agent to hand off to for identity-related threats.
        network_analyzer: The Network/API Analyzer agent to hand off to for network-related threats.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured alert intake agent.
    """
    return Agent(
        name="Alert Intake Agent",
        instructions=ALERT_INTAKE_INSTRUCTIONS,
        tools=[fetch_security_alerts, get_asset_inventory],
        handoffs=[auth_analyzer, network_analyzer],
        input_guardrails=[security_input_guardrail],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.2),
    )
