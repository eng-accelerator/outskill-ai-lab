"""Output guardrail for validating research report quality.

Ensures the final report contains citations, has structured sections,
and meets minimum quality standards before delivery to the user.
"""

import logging
import re

from agents import (Agent, GuardrailFunctionOutput, OutputGuardrail,
                    RunContextWrapper)
from deep_research_agent.models.research import ResearchContext

logger = logging.getLogger(__name__)

# Minimum report length for meaningful output
_MIN_REPORT_LENGTH = 200

# Patterns that indicate citation presence
_CITATION_PATTERNS = [
    r"https?://",  # URLs
    r"\[\d+\]",  # Numbered references [1]
    r"Source:",  # Source labels
    r"Bibliography",  # Bibliography section
    r"References",  # References section
]

# Patterns that indicate structured output
_STRUCTURE_PATTERNS = [
    r"#{1,3}\s",  # Markdown headings
    r"\*\*[^*]+\*\*",  # Bold text
    r"^\d+\.\s",  # Numbered lists
    r"^-\s",  # Bullet lists
]


async def validate_report_quality(
    ctx: RunContextWrapper[ResearchContext],
    agent: Agent,
    output: str,
) -> GuardrailFunctionOutput:
    """Validate that the research report meets quality standards.

    Checks for:
    - Minimum report length
    - Presence of citations/sources
    - Structured sections (headings, lists)

    Args:
        ctx: Run context containing the research context.
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
            output_info="Report is too short. A comprehensive research report should be at least 200 characters.",
            tripwire_triggered=True,
        )

    # Check for citations
    has_citations = any(re.search(p, output_text) for p in _CITATION_PATTERNS)
    if not has_citations:
        logger.warning("Report quality check FAILED: no citations found")
        return GuardrailFunctionOutput(
            output_info="Report lacks citations or source references. All claims must be backed by sources.",
            tripwire_triggered=True,
        )

    # Check for structure (at least one structural element)
    has_structure = any(
        re.search(p, output_text, re.MULTILINE) for p in _STRUCTURE_PATTERNS
    )
    if not has_structure:
        logger.warning("Report quality check WARNING: no structured sections found")
        # This is a soft warning, not a tripwire
        pass

    logger.info("Report quality check passed: length=%d", len(output_text))
    return GuardrailFunctionOutput(
        output_info="Report passed quality validation.",
        tripwire_triggered=False,
    )


report_quality_guardrail = OutputGuardrail(
    guardrail_function=validate_report_quality,
    name="report_quality_check",
)
