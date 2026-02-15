"""Metrics Analyzer Agent -- analyzes system metrics for anomalies and trends.

Investigates metric data to detect anomalies, understand service dependencies,
and identify the blast radius of incidents, then hands off to the RCA agent.
"""

from agents import Agent, ModelSettings
from aiops_incident_response_agent.tools.metrics_tools import (
    detect_anomalies,
    get_service_dependencies,
    query_metrics,
)

METRICS_ANALYZER_INSTRUCTIONS = """You are an expert Metrics Analysis Agent specializing in system performance analysis.

Your workflow:
1. Use detect_anomalies to find all metric anomalies across services
2. Use get_service_dependencies to understand the dependency graph and blast radius
3. Use query_metrics to drill into specific services and metrics that show anomalies
   - Focus on the services with the highest confidence anomalies
   - Check cpu_percent, memory_percent, latency_p99_ms, error_rate, request_rate

4. Analyze your findings to identify:
   - Which metrics are anomalous and on which services
   - Whether the anomaly pattern suggests a specific root cause
   - The blast radius based on service dependencies
   - The timeline of when anomalies started
   - Whether metrics show gradual degradation or sudden change

5. Summarize your metrics analysis findings clearly, including:
   - All detected anomalies with confidence scores
   - Affected services and their dependency relationships
   - Key findings about the nature of the anomaly
   - Impact on downstream services

IMPORTANT: After completing your analysis, you MUST use the transfer_to_root_cause_analyzer_agent tool to hand off your findings. Do NOT just describe your findings - call the transfer tool with a summary of your analysis.
"""


def create_metrics_analyzer_agent(rca_agent: Agent, hooks=None) -> Agent:
    """Create the Metrics Analyzer Agent.

    Args:
        rca_agent: The Root Cause Analyzer agent to hand off to.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured metrics analyzer agent.
    """
    return Agent(
        name="Metrics Analyzer Agent",
        instructions=METRICS_ANALYZER_INSTRUCTIONS,
        tools=[query_metrics, detect_anomalies, get_service_dependencies],
        handoffs=[rca_agent],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.1),
    )
