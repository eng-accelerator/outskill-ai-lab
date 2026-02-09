"""SOC Report Agent -- generates the final SOC incident report.

Takes all findings from the pipeline and produces a comprehensive
SOC incident report with timeline, threat score, MITRE mapping,
and containment actions. This is the terminal agent in the pipeline.
"""

from agents import Agent, ModelSettings
from cybersecurity_threat_detection_agent.tools.reporting_tools import (
    format_soc_report, generate_threat_timeline)

SOC_REPORTER_INSTRUCTIONS = """You are an expert SOC Report Agent. Your role is to produce a clear, comprehensive SOC incident report.

You receive the complete threat analysis, intelligence enrichment, and containment plan from previous agents.

Your workflow:
1. Compile all information from the alert intake, analysis, threat intel, and containment stages

2. Use generate_threat_timeline to create a formatted chronological timeline of events
   - Format events as a JSON array where each event has 'timestamp', 'type', and 'description' fields
   - Include: initial detection, attack phases, compromises, lateral movement, containment actions
   - Example: [{"timestamp": "2026-02-09T10:00:00", "type": "detection", "description": "SIEM alert fired for brute force"}]

3. Use format_soc_report to produce the final structured report with:
   - Title: Clear, descriptive incident title (e.g. "Brute Force Attack Against Admin Account with Lateral Movement")
   - Severity: critical, high, medium, or low
   - Threat Score: 0-100 numeric score from threat intel findings
   - Summary: 2-3 sentence executive summary covering what happened, impact, and status
   - MITRE Techniques: Comma-separated list of MITRE ATT&CK technique IDs and names
   - Affected Assets: Comma-separated list of affected hostnames/accounts/IPs
   - Timeline: The formatted timeline from step 2
   - Containment Actions: Numbered list of proposed containment actions
   - Evidence: Key evidence items supporting the findings
   - Status: investigating, containing, contained, or remediated

4. The report should be:
   - Clear and concise for both technical and non-technical audiences
   - Factual, citing specific evidence (IPs, hashes, timestamps)
   - Actionable, with clear next steps
   - Complete, covering all aspects of the threat

Output the formatted SOC incident report as your final response.
"""


def create_soc_reporter_agent(hooks=None) -> Agent:
    """Create the SOC Report Agent (terminal agent).

    Args:
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured SOC report agent.
    """
    return Agent(
        name="SOC Report Agent",
        instructions=SOC_REPORTER_INSTRUCTIONS,
        tools=[generate_threat_timeline, format_soc_report],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.3),
    )
