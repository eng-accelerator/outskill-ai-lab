"""Input guardrail for validating research queries.

Ensures the research query is substantive and appropriate before
the agent pipeline processes it.
"""

import logging

from agents import Agent, GuardrailFunctionOutput, InputGuardrail, RunContextWrapper

from deep_research_agent.models.research import ResearchContext

logger = logging.getLogger(__name__)

# Minimum query length for a meaningful research request
_MIN_QUERY_LENGTH = 10


async def validate_research_input(
    ctx: RunContextWrapper[ResearchContext],
    agent: Agent,
    input_data: str | list,
) -> GuardrailFunctionOutput:
    """Validate that the research query is substantive and processable.

    Checks that:
    - The query is not empty or trivially short
    - The context has been properly initialized with config

    Args:
        ctx: Run context containing the research context.
        agent: The agent being guarded.
        input_data: The input string or message list.

    Returns:
        GuardrailFunctionOutput: Validation result with tripwire status.
    """
    research_ctx = ctx.context

    # Check for valid query
    if not research_ctx.query or len(research_ctx.query.strip()) < _MIN_QUERY_LENGTH:
        logger.warning("Input validation failed: query too short or empty")
        return GuardrailFunctionOutput(
            output_info="Research query is empty or too short. Please provide a substantive research question.",
            tripwire_triggered=True,
        )

    # Check config is populated
    if not research_ctx.config:
        logger.warning("Input validation failed: no config available")
        return GuardrailFunctionOutput(
            output_info="Configuration not loaded. Cannot proceed without API keys.",
            tripwire_triggered=True,
        )

    logger.info(
        "Input validation passed: query_len=%d",
        len(research_ctx.query),
    )
    return GuardrailFunctionOutput(
        output_info="Research query validated successfully.",
        tripwire_triggered=False,
    )


research_input_guardrail = InputGuardrail(
    guardrail_function=validate_research_input,
    name="research_input_validation",
)
