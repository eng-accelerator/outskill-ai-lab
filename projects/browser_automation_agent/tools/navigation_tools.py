"""Navigation tools for browser page navigation.

Wraps Stagehand's session.navigate method as an OpenAI Agents SDK
function tool for navigating to URLs.
"""

import json
import logging
from datetime import datetime, timezone

from agents import RunContextWrapper, function_tool
from browser_automation_agent.models.page import ActionRecord
from browser_automation_agent.models.task import BrowserContext

logger = logging.getLogger(__name__)


@function_tool
async def navigate_to_url(
    ctx: RunContextWrapper[BrowserContext],
    url: str,
) -> str:
    """Navigate the browser to the specified URL.

    Uses Stagehand's session.navigate to load a web page.
    Updates the browser context with the current URL and
    records the navigation in the action log.

    Args:
        ctx: Run context containing the browser session.
        url: The URL to navigate to.

    Returns:
        str: JSON string with navigation result (success, url).
    """
    session = ctx.context.session
    assert session is not None, "Browser session not initialized"

    logger.info("Navigating to: %s", url)

    response = await session.navigate(url=url)

    ctx.context.current_url = url
    ctx.context.action_log.append(
        ActionRecord(
            action_type="navigate",
            instruction=f"Navigate to {url}",
            success=response.success,
            message=f"Successfully navigated to {url}",
        )
    )

    output = {
        "success": response.success,
        "url": url,
        "navigated_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Navigation complete: url=%s, success=%s", url, response.success)
    return json.dumps(output, indent=2)
