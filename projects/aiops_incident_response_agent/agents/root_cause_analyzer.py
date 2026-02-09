"""Root Cause Analyzer Agent -- correlates signals and determines root cause.

Takes findings from log and metrics analysis, correlates them with traces
and deployment records, and produces a root cause determination.
"""

from agents import Agent, ModelSettings

from aiops_incident_response_agent.tools.trace_tools import (
    correlate_signals,
    get_recent_deployments,
    query_traces,
)

RCA_INSTRUCTIONS = """You are an expert Root Cause Analysis Agent. Your role is to determine the root cause of incidents.

You receive analysis findings from the Log Analyzer and/or Metrics Analyzer agents.

Your workflow:
1. Review the findings passed to you from previous agents
2. Use correlate_signals to get a cross-signal correlation summary
3. Use query_traces to examine distributed traces for error patterns
   - Look for traces with status "error" or "timeout"
   - Check trace durations for latency anomalies
4. Use get_recent_deployments to check if a recent deployment may have caused the issue

5. Synthesize all evidence to determine:
   - The root cause of the incident
   - Your confidence level (0.0 to 1.0)
   - Contributing factors
   - The full list of affected services
   - A chronological timeline of the incident
   - The incident category (memory_leak, deployment_regression, database_exhaustion, network_partition, cpu_spike)

6. Build your case with specific evidence:
   - Cite specific log patterns, metric anomalies, trace errors
   - Note temporal correlations (what happened when)
   - Identify the originating service vs. cascading effects

IMPORTANT: After completing your analysis, you MUST use the transfer_to_remediation_agent tool to hand off your RCA findings. Do NOT just describe your findings - call the transfer tool with your complete root cause analysis.
"""


def create_rca_agent(remediation_agent: Agent, hooks=None) -> Agent:
    """Create the Root Cause Analyzer Agent.

    Args:
        remediation_agent: The Remediation agent to hand off to.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured RCA agent.
    """
    return Agent(
        name="Root Cause Analyzer Agent",
        instructions=RCA_INSTRUCTIONS,
        tools=[correlate_signals, query_traces, get_recent_deployments],
        handoffs=[remediation_agent],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.1),
    )
