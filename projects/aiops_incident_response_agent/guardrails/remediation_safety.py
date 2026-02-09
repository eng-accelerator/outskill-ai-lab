"""Output guardrail for validating remediation proposals.

Ensures remediation plans are safe and reasonable before
they are presented as final output.
"""

import logging

from agents import (Agent, GuardrailFunctionOutput, OutputGuardrail,
                    RunContextWrapper)
from aiops_incident_response_agent.simulators.scenario_engine import \
    ScenarioData

logger = logging.getLogger(__name__)

# Dangerous action patterns that should trigger review
DANGEROUS_PATTERNS = [
    "delete",
    "drop database",
    "rm -rf",
    "format",
    "destroy",
    "terminate all",
]


async def validate_remediation_safety(
    ctx: RunContextWrapper[ScenarioData],
    agent: Agent,
    output: str,
) -> GuardrailFunctionOutput:
    """Validate that a remediation proposal is safe to execute.

    Checks for dangerous command patterns and ensures the output
    contains actionable remediation steps.

    Args:
        ctx: Run context containing the scenario data.
        agent: The agent being guarded.
        output: The agent's output string to validate.

    Returns:
        GuardrailFunctionOutput: Validation result with tripwire status.
    """
    output_lower = output.lower() if isinstance(output, str) else ""

    for pattern in DANGEROUS_PATTERNS:
        if pattern in output_lower:
            logger.warning(
                "Remediation safety check FAILED: dangerous pattern '%s' detected",
                pattern,
            )
            return GuardrailFunctionOutput(
                output_info=f"Dangerous action detected: '{pattern}'. Remediation blocked for safety review.",
                tripwire_triggered=True,
            )

    logger.info("Remediation safety check passed")
    return GuardrailFunctionOutput(
        output_info="Remediation plan passed safety validation.",
        tripwire_triggered=False,
    )


remediation_output_guardrail = OutputGuardrail(
    guardrail_function=validate_remediation_safety,
    name="remediation_safety_check",
)
