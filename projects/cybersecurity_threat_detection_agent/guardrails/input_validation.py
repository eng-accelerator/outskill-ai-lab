"""Input guardrail for validating security event data.

Ensures the security event input contains valid, actionable information
before the agent pipeline processes it.
"""

import logging

from agents import Agent, GuardrailFunctionOutput, InputGuardrail, RunContextWrapper

from cybersecurity_threat_detection_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


async def validate_security_input(
    ctx: RunContextWrapper[ScenarioData],
    agent: Agent,
    input_data: str | list,
) -> GuardrailFunctionOutput:
    """Validate that the security event input is actionable.

    Checks that the scenario data has been loaded and contains
    at least some security events (alerts, auth logs, or network logs).

    Args:
        ctx: Run context containing the scenario data.
        agent: The agent being guarded.
        input_data: The input string or message list.

    Returns:
        GuardrailFunctionOutput: Validation result with tripwire status.
    """
    scenario = ctx.context

    has_alerts = len(scenario.alerts) > 0
    has_auth = len(scenario.auth_logs) > 0
    has_network = len(scenario.network_logs) > 0

    if not has_alerts and not has_auth and not has_network:
        logger.warning("Input validation failed: no security event data available")
        return GuardrailFunctionOutput(
            output_info="No security event data available. Cannot proceed with threat analysis.",
            tripwire_triggered=True,
        )

    logger.info(
        "Input validation passed: alerts=%d, auth_logs=%d, network_logs=%d",
        len(scenario.alerts), len(scenario.auth_logs), len(scenario.network_logs),
    )
    return GuardrailFunctionOutput(
        output_info="Security event data validated successfully.",
        tripwire_triggered=False,
    )


security_input_guardrail = InputGuardrail(
    guardrail_function=validate_security_input,
    name="security_input_validation",
)
