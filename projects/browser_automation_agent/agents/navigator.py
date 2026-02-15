"""Navigator Agent -- handles page navigation.

Navigates the browser to the target URL(s) specified in the task plan.
Hands off to the Interactor for page interactions.
"""

from agents import Agent, ModelSettings
from browser_automation_agent.tools.navigation_tools import navigate_to_url

NAVIGATOR_INSTRUCTIONS = """You are the Navigator Agent. You navigate the browser to the target URL(s) for the automation task, then IMMEDIATELY hand off to the Interactor Agent.

## Your Responsibilities

1. Identify the target URL(s) from the task plan provided by the Task Planner.
2. Use navigate_to_url to load the target page.
3. After successful navigation, IMMEDIATELY call transfer_to_interactor_agent.

## URL Selection

- For scraping tasks: Navigate directly to the page containing the target data.
- For form automation tasks: Navigate to the page containing the form or search interface.

## Common URLs
- Hacker News: https://news.ycombinator.com
- Google: https://www.google.com
- GitHub: https://github.com

## CRITICAL RULES
- You MUST navigate to at least one URL before handing off.
- After navigation, you MUST call transfer_to_interactor_agent.
- Do NOT produce a final answer. You are NOT the terminal agent.
- If navigation fails, report the error in the handoff message.
"""


def create_navigator_agent(interactor: Agent, hooks=None) -> Agent:
    """Create the Navigator Agent.

    Args:
        interactor: The Interactor agent to hand off to.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured navigator agent.
    """
    return Agent(
        name="Navigator Agent",
        instructions=NAVIGATOR_INSTRUCTIONS,
        tools=[navigate_to_url],
        handoffs=[interactor],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.1),
    )
