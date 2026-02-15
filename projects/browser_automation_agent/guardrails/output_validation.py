"""Output guardrail for validating automation report quality.

Ensures the final report contains structured results and meets
minimum quality standards before delivery to the user.
"""

import logging
import re

from agents import Agent, GuardrailFunctionOutput, OutputGuardrail, RunContextWrapper
from browser_automation_agent.models.task import BrowserContext

logger = logging.getLogger(__name__)

# Minimum report length for meaningful output
_MIN_REPORT_LENGTH = 100

# Patterns that indicate structured results
_RESULT_PATTERNS = [
    r"\{.*\}",  # JSON objects
    r"\[.*\]",  # JSON arrays
    r"\|.*\|",  # Markdown table rows
    r"#{1,3}\s",  # Markdown headings
    r"^\d+\.\s",  # Numbered lists
    r"^-\s",  # Bullet lists
    r"https?://",  # URLs (evidence of navigation)
]


async def validate_report_quality(
    ctx: RunContextWrapper[BrowserContext],
    agent: Agent,
    output: str,
) -> GuardrailFunctionOutput:
    """Validate that the automation report meets quality standards.

    Checks for:
    - Minimum report length
    - Presence of structured data or results
    - Evidence that browser automation was performed

    Args:
        ctx: Run context containing the browser context.
        agent: The agent being guarded.
        output: The agent's output string to validate.

    Returns:
        GuardrailFunctionOutput: Validation result with tripwire status.
    """
    output_text = output if isinstance(output, str) else ""

    # Check minimum length
    if len(output_text) < _MIN_REPORT_LENGTH:
        logger.warning(
            "Report quality check FAILED: report too short (%d chars)", len(output_text)
        )
        return GuardrailFunctionOutput(
            output_info="Report is too short. A browser automation report should contain extracted data or action results.",
            tripwire_triggered=True,
        )

    # Check for structured results (at least one pattern)
    has_results = any(
        re.search(p, output_text, re.MULTILINE | re.DOTALL) for p in _RESULT_PATTERNS
    )
    if not has_results:
        logger.warning("Report quality check FAILED: no structured results found")
        return GuardrailFunctionOutput(
            output_info="Report lacks structured results. The report should contain extracted data, URLs visited, or action outcomes.",
            tripwire_triggered=True,
        )

    logger.info("Report quality check passed: length=%d", len(output_text))
    return GuardrailFunctionOutput(
        output_info="Report passed quality validation.",
        tripwire_triggered=False,
    )


report_quality_guardrail = OutputGuardrail(
    guardrail_function=validate_report_quality,
    name="report_quality_check",
)
