"""Input guardrail for validating incident alert data.

Ensures the incident input contains valid, actionable information
before the agent pipeline processes it.
"""

import logging

from agents import Agent, GuardrailFunctionOutput, InputGuardrail, RunContextWrapper

from aiops_incident_response_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


async def validate_incident_input(
    ctx: RunContextWrapper[ScenarioData],
    agent: Agent,
    input_data: str | list,
) -> GuardrailFunctionOutput:
    """Validate that the incident input is actionable.

    Checks that the scenario data has been loaded and contains
    at least some alerts or service health data to analyze.

    Args:
        ctx: Run context containing the scenario data.
        agent: The agent being guarded.
        input_data: The input string or message list.

    Returns:
        GuardrailFunctionOutput: Validation result with tripwire status.
    """
    scenario = ctx.context

    has_alerts = len(scenario.alerts) > 0
    has_health = len(scenario.service_health) > 0
    has_logs = len(scenario.logs) > 0

    if not has_alerts and not has_health and not has_logs:
        logger.warning("Input validation failed: no observability data available")
        return GuardrailFunctionOutput(
            output_info="No observability data available. Cannot proceed with incident analysis.",
            tripwire_triggered=True,
        )

    logger.info(
        "Input validation passed: alerts=%d, health=%d, logs=%d",
        len(scenario.alerts), len(scenario.service_health), len(scenario.logs),
    )
    return GuardrailFunctionOutput(
        output_info="Incident data validated successfully.",
        tripwire_triggered=False,
    )


incident_input_guardrail = InputGuardrail(
    guardrail_function=validate_incident_input,
    name="incident_input_validation",
)
