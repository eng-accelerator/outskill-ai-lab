"""Observation tools for discovering actionable page elements.

Wraps Stagehand's session.observe method as an OpenAI Agents SDK
function tool for finding interactive elements on web pages.
"""

import json
import logging
from datetime import datetime, timezone

from agents import RunContextWrapper, function_tool
from browser_automation_agent.models.page import PageObservation
from browser_automation_agent.models.task import BrowserContext

logger = logging.getLogger(__name__)


@function_tool
async def observe_page(
    ctx: RunContextWrapper[BrowserContext],
    instruction: str,
) -> str:
    """Observe the current page to find actionable elements matching an instruction.

    Uses Stagehand's session.observe to identify interactive elements
    (buttons, links, inputs, etc.) on the page that match the given
    natural language instruction. Returns a list of possible actions
    with descriptions and selectors.

    Args:
        ctx: Run context containing the browser session.
        instruction: Natural language description of what to look for
            (e.g. "find the search input", "find the submit button").

    Returns:
        str: JSON string with list of available actions (description, selector).
    """
    session = ctx.context.session
    assert session is not None, "Browser session not initialized"

    logger.info("Observing page: instruction=%s", instruction)

    response = await session.observe(instruction=instruction)

    actions = []
    for result in response.data.result:
        actions.append({
            "description": result.description,
            "selector": result.selector,
            "method": result.method,
            "arguments": result.arguments,
        })

    # Record observation in context
    raw = json.dumps(actions, indent=2)
    ctx.context.action_log.append(
        PageObservation(
            url=ctx.context.current_url,
            instruction=instruction,
            actions_found=len(actions),
            raw_response=raw,
        )
    )

    output = {
        "success": response.success,
        "instruction": instruction,
        "actions_found": len(actions),
        "actions": actions,
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Observation complete: instruction=%s, actions_found=%d",
        instruction,
        len(actions),
    )
    return json.dumps(output, indent=2)
