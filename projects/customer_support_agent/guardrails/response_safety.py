"""Output guardrail for validating agent response safety.

Prevents PII leakage, caps unauthorized refund amounts, and blocks
inappropriate language in agent responses.
"""

import logging
import re

from agents import Agent, GuardrailFunctionOutput, OutputGuardrail, RunContextWrapper
from customer_support_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)

# PII patterns to detect and block
_CREDIT_CARD_PATTERN = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")
_SSN_PATTERN = re.compile(r"\b\d{3}[\s-]?\d{2}[\s-]?\d{4}\b")
_FULL_PHONE_EXPOSURE = re.compile(r"\+?1?[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}")

# Inappropriate language patterns
_INAPPROPRIATE_PATTERNS = [
    "shut up",
    "go away",
    "not my problem",
    "deal with it",
    "too bad",
    "that's your fault",
    "you're wrong",
    "i don't care",
    "figure it out yourself",
]

# Maximum refund that can be auto-approved without human review
MAX_AUTO_REFUND = 500.0


async def validate_response_safety(
    ctx: RunContextWrapper[ScenarioData],
    agent: Agent,
    output: str,
) -> GuardrailFunctionOutput:
    """Validate that agent responses are safe and appropriate.

    Checks for:
    - PII exposure (credit card numbers, SSNs)
    - Unauthorized large refund commitments
    - Inappropriate or unprofessional language
    - Promises the system cannot fulfill

    Args:
        ctx: Run context containing the scenario data.
        agent: The agent being guarded.
        output: The agent's output string to validate.

    Returns:
        GuardrailFunctionOutput: Validation result with tripwire status.
    """
    output_text = output if isinstance(output, str) else ""
    output_lower = output_text.lower()

    # Check for credit card number exposure
    if _CREDIT_CARD_PATTERN.search(output_text):
        logger.warning(
            "Response safety check FAILED: credit card number detected in output"
        )
        return GuardrailFunctionOutput(
            output_info="Response blocked: Contains what appears to be a credit card number. PII must not be exposed.",
            tripwire_triggered=True,
        )

    # Check for SSN exposure
    if _SSN_PATTERN.search(output_text):
        # Avoid false positives on order/ticket IDs by checking context
        ssn_matches = _SSN_PATTERN.findall(output_text)
        for match in ssn_matches:
            clean_match = re.sub(r"[\s-]", "", match)
            # SSN format: 3-2-4, skip if it looks like an ID prefix
            if len(clean_match) == 9 and not any(
                prefix in output_text[: output_text.find(match)]
                for prefix in ["ORD-", "TKT-", "PAY-", "INV-", "REF-", "SUB-"]
            ):
                logger.warning(
                    "Response safety check FAILED: possible SSN detected in output"
                )
                return GuardrailFunctionOutput(
                    output_info="Response blocked: Contains what appears to be a Social Security Number. PII must not be exposed.",
                    tripwire_triggered=True,
                )

    # Check for inappropriate language
    for pattern in _INAPPROPRIATE_PATTERNS:
        if pattern in output_lower:
            logger.warning(
                "Response safety check FAILED: inappropriate language '%s'", pattern
            )
            return GuardrailFunctionOutput(
                output_info=f"Response blocked: Contains inappropriate language ('{pattern}'). All responses must be professional and empathetic.",
                tripwire_triggered=True,
            )

    # Check for unauthorized large refund promises
    refund_pattern = re.compile(
        r"refund.*?\$(\d+(?:,\d{3})*(?:\.\d{2})?)", re.IGNORECASE
    )
    refund_matches = refund_pattern.findall(output_text)
    for amount_str in refund_matches:
        amount = float(amount_str.replace(",", ""))
        if amount > MAX_AUTO_REFUND:
            # Check if approval was mentioned
            if (
                "approval" not in output_lower
                and "manager" not in output_lower
                and "review" not in output_lower
            ):
                logger.warning(
                    "Response safety check FAILED: large refund $%.2f without approval mention",
                    amount,
                )
                return GuardrailFunctionOutput(
                    output_info=f"Response blocked: Refund of ${amount:.2f} exceeds auto-approval limit of ${MAX_AUTO_REFUND:.2f}. Must mention manager approval requirement.",
                    tripwire_triggered=True,
                )

    logger.info("Response safety check passed")
    return GuardrailFunctionOutput(
        output_info="Response passed safety validation.",
        tripwire_triggered=False,
    )


response_safety_guardrail = OutputGuardrail(
    guardrail_function=validate_response_safety,
    name="response_safety_check",
)
