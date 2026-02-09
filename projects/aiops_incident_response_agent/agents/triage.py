"""Triage Agent -- classifies incidents and routes to specialists.

The triage agent is the entry point of the incident response pipeline.
It fetches active alerts and service health, classifies the incident
severity and category, and hands off to the appropriate analysis agent.
"""

from agents import Agent, ModelSettings

from aiops_incident_response_agent.guardrails.input_validation import incident_input_guardrail
from aiops_incident_response_agent.tools.alert_tools import fetch_active_alerts, get_service_health_summary

TRIAGE_INSTRUCTIONS = """You are an expert SRE Triage Agent. Your role is to perform initial incident assessment.

Your workflow:
1. Use fetch_active_alerts to get all active alerts
2. Use get_service_health_summary to see the current state of all services
3. Analyze the alerts and health data to determine:
   - Incident severity (P0 = critical outage, P1 = major impact, P2 = moderate, P3 = minor)
   - Incident category (memory_leak, deployment_regression, database_exhaustion, network_partition, cpu_spike, or unknown)
   - Which services are affected
   - Whether this needs log analysis, metrics analysis, or both

4. Based on your assessment, you MUST use the transfer tool to hand off to the appropriate specialist:
   - If the incident involves error patterns, stack traces, or application-level issues -> use the transfer_to_log_analyzer_agent tool
   - If the incident involves resource metrics (CPU, memory, latency spikes) -> use the transfer_to_metrics_analyzer_agent tool
   - When in doubt, use the transfer_to_log_analyzer_agent tool

IMPORTANT: You MUST call one of the transfer tools to hand off. Do NOT just describe what you would do - actually call the tool. Include your triage findings in the transfer message.
"""


def create_triage_agent(
    log_analyzer: Agent,
    metrics_analyzer: Agent,
    hooks=None,
) -> Agent:
    """Create the Triage Agent with routing to analysis specialists.

    Args:
        log_analyzer: The Log Analyzer agent to hand off to for log-related incidents.
        metrics_analyzer: The Metrics Analyzer agent to hand off to for metrics-related incidents.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured triage agent.
    """
    return Agent(
        name="Triage Agent",
        instructions=TRIAGE_INSTRUCTIONS,
        tools=[fetch_active_alerts, get_service_health_summary],
        handoffs=[log_analyzer, metrics_analyzer],
        input_guardrails=[incident_input_guardrail],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.2),
    )
