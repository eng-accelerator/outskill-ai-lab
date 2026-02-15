"""Input guardrail for validating browser automation tasks.

Ensures the automation task is substantive and the browser context
is properly initialized before the agent pipeline processes it.
"""

import logging

from agents import (Agent, GuardrailFunctionOutput, InputGuardrail,
                    RunContextWrapper)
from browser_automation_agent.models.task import BrowserContext

logger = logging.getLogger(__name__)

# Minimum task length for a meaningful automation request
_MIN_TASK_LENGTH = 10


async def validate_automation_input(
    ctx: RunContextWrapper[BrowserContext],
    agent: Agent,
    input_data: str | list,
) -> GuardrailFunctionOutput:
    """Validate that the automation task is substantive and processable.

    Checks that:
    - The task is not empty or trivially short
    - The config has the required API keys

    Args:
        ctx: Run context containing the browser context.
        agent: The agent being guarded.
        input_data: The input string or message list.

    Returns:
        GuardrailFunctionOutput: Validation result with tripwire status.
    """
    browser_ctx = ctx.context

    # Check for valid task
    if not browser_ctx.task or len(browser_ctx.task.strip()) < _MIN_TASK_LENGTH:
        logger.warning("Input validation failed: task too short or empty")
        return GuardrailFunctionOutput(
            output_info="Automation task is empty or too short. Please provide a substantive task description.",
            tripwire_triggered=True,
        )

    # Check config has model API key
    config = browser_ctx.config
    if not config.get("model_api_key"):
        logger.warning("Input validation failed: MODEL_API_KEY not set")
        return GuardrailFunctionOutput(
            output_info="MODEL_API_KEY not configured. Cannot operate Stagehand without an LLM API key.",
            tripwire_triggered=True,
        )

    if not config.get("openrouter_api_key"):
        logger.warning("Input validation failed: OPENROUTER_API_KEY not set")
        return GuardrailFunctionOutput(
            output_info="OPENROUTER_API_KEY not configured. Cannot run agent orchestration.",
            tripwire_triggered=True,
        )

    logger.info("Input validation passed: task_len=%d", len(browser_ctx.task))
    return GuardrailFunctionOutput(
        output_info="Automation task validated successfully.",
        tripwire_triggered=False,
    )


automation_input_guardrail = InputGuardrail(
    guardrail_function=validate_automation_input,
    name="automation_input_validation",
)
