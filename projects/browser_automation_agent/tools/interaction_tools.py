"""Interaction tools for performing browser actions.

Wraps Stagehand's session.act method as an OpenAI Agents SDK
function tool for clicking, typing, submitting forms, and
other browser interactions.
"""

import json
import logging
from datetime import datetime, timezone

from agents import RunContextWrapper, function_tool
from browser_automation_agent.models.page import ActionRecord
from browser_automation_agent.models.task import BrowserContext

logger = logging.getLogger(__name__)


@function_tool
async def perform_action(
    ctx: RunContextWrapper[BrowserContext],
    instruction: str,
) -> str:
    """Perform a browser action described in natural language.

    Uses Stagehand's session.act to execute browser interactions such as
    clicking buttons, typing text, pressing keys, scrolling, and submitting
    forms. Stagehand's AI identifies the correct element and performs the action.

    Args:
        ctx: Run context containing the browser session.
        instruction: Natural language description of the action to perform
            (e.g. "click the Login button", "type 'hello' in the search box",
            "press Enter", "scroll down").

    Returns:
        str: JSON string with action result (success, message, description).
    """
    session = ctx.context.session
    assert session is not None, "Browser session not initialized"

    logger.info("Performing action: instruction=%s", instruction)

    response = await session.act(input=instruction)

    result = response.data.result
    action_record = ActionRecord(
        action_type="act",
        instruction=instruction,
        success=result.success,
        message=result.message,
    )
    ctx.context.action_log.append(action_record)

    output = {
        "success": result.success,
        "message": result.message,
        "action_description": result.action_description,
        "instruction": instruction,
        "acted_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Action complete: instruction=%s, success=%s, message=%s",
        instruction,
        result.success,
        result.message,
    )
    return json.dumps(output, indent=2)
