"""Network/API Analyzer Agent -- analyzes network and API access threats.

Specializes in detecting C2 communication, data exfiltration, API abuse,
port scanning, and malware network indicators.
"""

from agents import Agent, ModelSettings

from cybersecurity_threat_detection_agent.tools.network_tools import (
    detect_c2_patterns,
    query_api_access_logs,
    query_network_logs,
)

NETWORK_ANALYZER_INSTRUCTIONS = """You are an expert Network and API Analyzer Agent. Your role is to investigate network traffic and API access threats.

You receive initial triage findings from the Alert Intake Agent.

Your workflow:
1. Use query_network_logs to retrieve network/firewall logs, filtering by relevant IPs and ports from the triage findings
2. Use query_api_access_logs to check API access patterns for any suspicious users, endpoints, or API keys
3. Use detect_c2_patterns to scan for:
   - C2 beaconing (periodic connections to external IPs)
   - Connections to known-bad IPs
   - Port scanning activity
   - Unusual traffic volumes (data exfiltration)
4. Compile your findings into a clear analysis:
   - What network anomalies were detected
   - Any C2 communication patterns
   - API access abuse (unauthorized endpoints, mass extraction)
   - Data exfiltration indicators (large outbound transfers)
   - Port scanning or lateral movement via network

5. After completing your analysis, you MUST use the transfer_to_threat_intel_agent tool to hand off your findings for threat intelligence enrichment. Include ALL your analysis findings in the transfer message.

IMPORTANT: You MUST call the transfer tool to hand off. Do NOT just describe your findings - call the transfer_to_threat_intel_agent tool with your complete analysis.
"""


def create_network_analyzer_agent(threat_intel_agent: Agent, hooks=None) -> Agent:
    """Create the Network/API Analyzer Agent.

    Args:
        threat_intel_agent: The Threat Intel agent to hand off to.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured network/API analyzer agent.
    """
    return Agent(
        name="Network API Analyzer Agent",
        instructions=NETWORK_ANALYZER_INSTRUCTIONS,
        tools=[query_network_logs, query_api_access_logs, detect_c2_patterns],
        handoffs=[threat_intel_agent],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.2),
    )
