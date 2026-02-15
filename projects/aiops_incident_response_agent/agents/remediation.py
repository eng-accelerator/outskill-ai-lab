"""Remediation Agent -- proposes fixes based on root cause analysis.

Takes the RCA findings and proposes specific remediation actions
using runbooks and action proposals, then hands off to the reporter.
"""

from agents import Agent, ModelSettings
from aiops_incident_response_agent.guardrails.remediation_safety import (
    remediation_output_guardrail,
)
from aiops_incident_response_agent.tools.remediation_tools import (
    lookup_runbook,
    propose_config_change,
    propose_rollback,
    propose_scaling_action,
)

REMEDIATION_INSTRUCTIONS = """You are an expert Remediation Agent. Your role is to propose safe, effective fixes for incidents.

You receive root cause analysis findings from the RCA Agent.

Your workflow:
1. Review the RCA findings to understand the root cause and category
2. Use lookup_runbook with the incident category to get standard remediation steps
3. Based on the root cause, propose specific actions:
   - For deployment regressions: use propose_rollback
   - For resource exhaustion (CPU/memory): use propose_scaling_action
   - For configuration issues: use propose_config_change
   - You may propose multiple actions if needed

4. For each proposed action, consider:
   - Risk level (low, medium, high, critical)
   - Whether human approval is required
   - Expected impact and resolution time
   - Rollback plan if the fix doesn't work

5. Compile a complete remediation plan including:
   - Summary of the incident and root cause
   - Ordered list of remediation actions
   - Estimated resolution time
   - Rollback plan
   - Whether stakeholder communication is needed
   - Post-incident tasks (monitoring, follow-up tickets)

SAFETY RULES:
- Never propose destructive actions (delete, drop, rm -rf)
- Always flag high-risk actions as requiring approval
- Prefer reversible actions (rollback, scaling) over irreversible ones
- Include monitoring steps after each remediation action

IMPORTANT: After completing your remediation plan, you MUST use the transfer_to_incident_reporter_agent tool to hand off. Do NOT just describe the plan - call the transfer tool with your complete remediation plan.
"""


def create_remediation_agent(reporter_agent: Agent, hooks=None) -> Agent:
    """Create the Remediation Agent.

    Args:
        reporter_agent: The Incident Reporter agent to hand off to.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured remediation agent.
    """
    return Agent(
        name="Remediation Agent",
        instructions=REMEDIATION_INSTRUCTIONS,
        tools=[
            lookup_runbook,
            propose_scaling_action,
            propose_rollback,
            propose_config_change,
        ],
        handoffs=[reporter_agent],
        output_guardrails=[remediation_output_guardrail],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.2),
    )
