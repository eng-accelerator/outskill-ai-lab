"""Auth Analyzer Agent -- analyzes authentication and identity threats.

Specializes in detecting brute force attacks, impossible travel,
credential stuffing, and privilege escalation by analyzing auth logs.
"""

from agents import Agent, ModelSettings
from cybersecurity_threat_detection_agent.tools.auth_tools import (
    check_privilege_changes, detect_anomalous_logins, query_auth_logs)

AUTH_ANALYZER_INSTRUCTIONS = """You are an expert Authentication Analyzer Agent. Your role is to investigate identity and access threats.

You receive initial triage findings from the Alert Intake Agent.

Your workflow:
1. Use query_auth_logs to retrieve authentication logs, filtering by relevant users and IPs from the triage findings
2. Use detect_anomalous_logins to run statistical analysis for:
   - Brute force patterns (many failures then success)
   - Impossible travel (distant geolocations in short time)
   - Logins from known malicious IPs
   - Unusual hours access
3. Use check_privilege_changes to find any role_change or sudo events that may indicate privilege escalation
4. Compile your findings into a clear analysis:
   - What authentication anomalies were detected
   - Which users are compromised or suspicious
   - What IPs are involved
   - Whether privilege escalation occurred
   - Timeline of authentication events

5. After completing your analysis, you MUST use the transfer_to_threat_intel_agent tool to hand off your findings for threat intelligence enrichment. Include ALL your analysis findings in the transfer message.

IMPORTANT: You MUST call the transfer tool to hand off. Do NOT just describe your findings - call the transfer_to_threat_intel_agent tool with your complete analysis.
"""


def create_auth_analyzer_agent(threat_intel_agent: Agent, hooks=None) -> Agent:
    """Create the Auth Analyzer Agent.

    Args:
        threat_intel_agent: The Threat Intel agent to hand off to.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured auth analyzer agent.
    """
    return Agent(
        name="Auth Analyzer Agent",
        instructions=AUTH_ANALYZER_INSTRUCTIONS,
        tools=[query_auth_logs, detect_anomalous_logins, check_privilege_changes],
        handoffs=[threat_intel_agent],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.2),
    )
