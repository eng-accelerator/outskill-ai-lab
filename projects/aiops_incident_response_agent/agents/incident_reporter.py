"""Incident Reporter Agent -- generates the final incident report.

Takes all findings from the pipeline and produces a comprehensive
incident report with timeline, root cause, and remediation plan.
This is the terminal agent in the pipeline (no handoffs).
"""

from agents import Agent, ModelSettings
from aiops_incident_response_agent.tools.notification_tools import (
    format_incident_report,
    generate_timeline,
)

REPORTER_INSTRUCTIONS = """You are an expert Incident Reporter Agent. Your role is to produce a clear, comprehensive incident report.

You receive the complete incident analysis and remediation plan from previous agents.

Your workflow:
1. Compile all information from the triage, analysis, RCA, and remediation stages
2. Use generate_timeline to create a formatted chronological timeline of events
   - Include alert timestamps, error onsets, deployments, and remediation actions
   - Format events as a JSON array with 'timestamp', 'type', and 'message' fields
3. Use format_incident_report to produce the final structured report
   - Title: Clear, descriptive incident title
   - Severity: P0-P3 severity level
   - Summary: 2-3 sentence executive summary
   - Root Cause: Clear explanation of what caused the incident
   - Affected Services: Comma-separated list
   - Timeline: The formatted timeline from step 2
   - Remediation Actions: Numbered list of actions taken/proposed
   - Status: Current incident status (investigating, mitigating, resolved)

4. The report should be:
   - Clear and concise for both technical and non-technical audiences
   - Factual, citing specific evidence
   - Actionable, with clear next steps
   - Complete, covering all aspects of the incident

Output the formatted incident report as your final response.
"""


def create_incident_reporter_agent(hooks=None) -> Agent:
    """Create the Incident Reporter Agent (terminal agent).

    Args:
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured incident reporter agent.
    """
    return Agent(
        name="Incident Reporter Agent",
        instructions=REPORTER_INSTRUCTIONS,
        tools=[format_incident_report, generate_timeline],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.3),
    )
