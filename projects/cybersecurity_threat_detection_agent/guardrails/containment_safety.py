"""Output guardrail for validating containment action proposals.

Ensures containment actions are safe, proportional, and do not
accidentally lock out the SOC team or disrupt critical infrastructure.
"""

import logging

from agents import Agent, GuardrailFunctionOutput, OutputGuardrail, RunContextWrapper

from cybersecurity_threat_detection_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)

# Dangerous containment patterns that should trigger review
DANGEROUS_PATTERNS = [
    "disable all",
    "block 0.0.0.0/0",
    "block 0.0.0.0",
    "isolate all",
    "revoke all",
    "delete",
    "drop database",
    "rm -rf",
    "format",
    "destroy",
    "terminate all",
    "shutdown all",
]

# SOC team accounts that must never be disabled
SOC_TEAM_ACCOUNTS = {"soc-admin", "soc-analyst", "soc-lead", "svc-monitor"}


async def validate_containment_safety(
    ctx: RunContextWrapper[ScenarioData],
    agent: Agent,
    output: str,
) -> GuardrailFunctionOutput:
    """Validate that containment proposals are safe to execute.

    Checks for:
    - Dangerous mass-action patterns (disable all, block all, etc.)
    - Actions targeting SOC team accounts
    - Overly broad network blocks
    - Destructive commands

    Args:
        ctx: Run context containing the scenario data.
        agent: The agent being guarded.
        output: The agent's output string to validate.

    Returns:
        GuardrailFunctionOutput: Validation result with tripwire status.
    """
    output_lower = output.lower() if isinstance(output, str) else ""

    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern in output_lower:
            logger.warning("Containment safety check FAILED: dangerous pattern '%s' detected", pattern)
            return GuardrailFunctionOutput(
                output_info=f"Dangerous containment action detected: '{pattern}'. Action blocked for safety review.",
                tripwire_triggered=True,
            )

    # Check for SOC team account targeting
    for account in SOC_TEAM_ACCOUNTS:
        if account in output_lower and "disable" in output_lower:
            logger.warning("Containment safety check FAILED: attempt to disable SOC team account '%s'", account)
            return GuardrailFunctionOutput(
                output_info=f"Cannot disable SOC team account '{account}'. This would lock out the security team.",
                tripwire_triggered=True,
            )

    logger.info("Containment safety check passed")
    return GuardrailFunctionOutput(
        output_info="Containment plan passed safety validation.",
        tripwire_triggered=False,
    )


containment_output_guardrail = OutputGuardrail(
    guardrail_function=validate_containment_safety,
    name="containment_safety_check",
)
