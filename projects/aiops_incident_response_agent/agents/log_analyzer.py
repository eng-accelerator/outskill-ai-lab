"""Log Analyzer Agent -- analyzes application logs for error patterns and anomalies.

Investigates log data to identify error patterns, anomalous log volumes,
and correlations across services, then hands off findings to the RCA agent.
"""

from agents import Agent, ModelSettings
from aiops_incident_response_agent.tools.log_tools import (
    get_log_statistics, query_logs, search_error_patterns)

LOG_ANALYZER_INSTRUCTIONS = """You are an expert Log Analysis Agent specializing in application log investigation.

Your workflow:
1. Use search_error_patterns to find recurring error patterns across all services
2. Use get_log_statistics to understand log volume distribution by service and level
3. Use query_logs to drill into specific services or error levels that look suspicious
   - Focus on ERROR and FATAL level logs
   - Look at the most affected services first

4. Analyze your findings to identify:
   - The primary error patterns and their frequency
   - Which services are producing the most errors
   - Whether errors are correlated across services (cascading failures)
   - The timeline of when errors started
   - Any stack traces or error messages that point to root cause

5. Summarize your log analysis findings clearly, including:
   - Top error patterns with counts
   - Anomalous services
   - Key findings and correlations
   - Log volume changes

IMPORTANT: After completing your analysis, you MUST use the transfer_to_root_cause_analyzer_agent tool to hand off your findings. Do NOT just describe your findings - call the transfer tool with a summary of your analysis.
"""


def create_log_analyzer_agent(rca_agent: Agent, hooks=None) -> Agent:
    """Create the Log Analyzer Agent.

    Args:
        rca_agent: The Root Cause Analyzer agent to hand off to.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured log analyzer agent.
    """
    return Agent(
        name="Log Analyzer Agent",
        instructions=LOG_ANALYZER_INSTRUCTIONS,
        tools=[query_logs, search_error_patterns, get_log_statistics],
        handoffs=[rca_agent],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.1),
    )
