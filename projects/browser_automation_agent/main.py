"""Browser Automation Agent -- Entry Point.

Orchestrates a multi-agent browser automation pipeline using
Stagehand as the browser backend and OpenAI Agents SDK with
OpenRouter for LLM orchestration. Supports web scraping and
form automation scenarios.

Usage:
    uv run python -m browser_automation_agent.main
"""

import asyncio
import logging

from agents import (AgentHooks, AsyncOpenAI, OpenAIChatCompletionsModel,
                    RunConfig, Runner, set_tracing_disabled)
from browser_automation_agent.agents.extractor import create_extractor_agent
from browser_automation_agent.agents.interactor import create_interactor_agent
from browser_automation_agent.agents.navigator import create_navigator_agent
from browser_automation_agent.agents.reporter import create_reporter_agent
from browser_automation_agent.agents.task_planner import \
    create_task_planner_agent
from browser_automation_agent.agents.validator import create_validator_agent
from browser_automation_agent.models.task import BrowserContext
from browser_automation_agent.utils.config import load_config
from stagehand import AsyncStagehand

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------
# Predefined scenarios
# -----------------------------------------------------------------

SCENARIOS = {
    "1": {
        "name": "Web Scraping — Hacker News",
        "task": (
            "Extract the top 10 posts from Hacker News including "
            "title, URL, and points for each post."
        ),
    },
    "2": {
        "name": "Form Automation — Google Search",
        "task": (
            "Go to Google, search for 'Python browser automation', "
            "and extract the first 5 search results with title and URL."
        ),
    },
}


# -----------------------------------------------------------------
# Lifecycle hooks for observability
# -----------------------------------------------------------------


class BrowserAutomationHooks(AgentHooks):
    """Lifecycle hooks for observability during browser automation."""

    async def on_start(self, context, agent):
        """Log when an agent starts processing.

        Args:
            context: The run context.
            agent: The agent that is starting.
        """
        print(f"\n{'='*60}")
        print(f"  AGENT: {agent.name}")
        print(f"{'='*60}")

    async def on_end(self, context, agent, output):
        """Log when an agent completes processing.

        Args:
            context: The run context.
            agent: The agent that completed.
            output: The agent's output.
        """
        print(f"\n  [{agent.name}] completed.")

    async def on_tool_start(self, context, agent, tool):
        """Log when a tool is invoked.

        Args:
            context: The run context.
            agent: The agent invoking the tool.
            tool: The tool being invoked.
        """
        print(f"  [{agent.name}] calling tool: {tool.name}")

    async def on_tool_end(self, context, agent, tool, result):
        """Log when a tool completes.

        Args:
            context: The run context.
            agent: The agent that invoked the tool.
            tool: The tool that completed.
            result: The tool's result.
        """
        print(f"  [{agent.name}] tool {tool.name} completed.")

    async def on_handoff(self, context, agent, source):
        """Log when a handoff occurs between agents.

        Args:
            context: The run context.
            agent: The target agent receiving the handoff.
            source: The source agent performing the handoff.
        """
        print(f"\n  >> Handoff: {source.name} -> {agent.name}")


# -----------------------------------------------------------------
# Model + session factories
# -----------------------------------------------------------------


def create_openrouter_model(config: dict[str, str | None]) -> OpenAIChatCompletionsModel:
    """Create an OpenRouter-backed model using Chat Completions API.

    Args:
        config: Configuration dict from load_config().

    Returns:
        OpenAIChatCompletionsModel: Configured for OpenRouter.

    Raises:
        AssertionError: If required API keys are missing.
    """
    api_key = config["openrouter_api_key"]
    assert api_key, (
        "OPENROUTER_API_KEY not set. "
        "Add it to your .env file: OPENROUTER_API_KEY=your_key_here"
    )

    base_url = config["openrouter_base_url"]
    model_name = config["model_name"]

    client = AsyncOpenAI(
        base_url=base_url,
        api_key=api_key,
    )

    set_tracing_disabled(True)

    model = OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=client,
    )

    logger.info("OpenRouter model configured: base_url=%s, model=%s", base_url, model_name)
    return model


async def create_stagehand_session(config: dict[str, str | None]):
    """Create and start a Stagehand browser session in local mode.

    Creates an AsyncStagehand client pointing at a local Chrome
    instance and starts a new session.

    Args:
        config: Configuration dict from load_config().

    Returns:
        tuple[AsyncStagehand, AsyncSession]: The client and bound session.

    Raises:
        AssertionError: If MODEL_API_KEY is not set.
    """
    model_api_key = config["model_api_key"]
    assert model_api_key, (
        "MODEL_API_KEY not set. "
        "Add it to your .env file: MODEL_API_KEY=your_key_here"
    )

    logger.info("Creating Stagehand client in local mode...")

    client = AsyncStagehand(
        server="local",
        model_api_key=model_api_key,
        local_headless=True,
    )

    model_name = config.get("model_name") or "openai/gpt-4.1-mini"
    session = await client.sessions.start(model_name=model_name)

    logger.info("Stagehand session started: session_id=%s", session.id)
    return client, session


# -----------------------------------------------------------------
# Pipeline construction
# -----------------------------------------------------------------


def build_agent_pipeline(model: OpenAIChatCompletionsModel, hooks: AgentHooks):
    """Build the complete agent pipeline with handoff chain.

    Constructs agents in reverse order (terminal first) to wire handoffs.

    Pipeline:
        Task Planner -> Navigator -> Interactor -> Extractor -> Validator -> Reporter

    Args:
        model: The OpenRouter-backed model instance.
        hooks: AgentHooks instance for lifecycle callbacks.

    Returns:
        Agent: The task planner agent (entry point of the pipeline).
    """
    # Build from terminal agent backwards
    reporter = create_reporter_agent(hooks=hooks)
    validator = create_validator_agent(reporter, hooks=hooks)
    extractor = create_extractor_agent(validator, hooks=hooks)
    interactor = create_interactor_agent(extractor, hooks=hooks)
    navigator = create_navigator_agent(interactor, hooks=hooks)
    planner = create_task_planner_agent(navigator, hooks=hooks)

    # Set model on all agents to use OpenRouter via Chat Completions
    all_agents = [planner, navigator, interactor, extractor, validator, reporter]
    for agent in all_agents:
        agent.model = model

    logger.info(
        "Agent pipeline built: Planner -> Navigator -> Interactor -> Extractor -> Validator -> Reporter"
    )
    return planner


# -----------------------------------------------------------------
# Run entry
# -----------------------------------------------------------------


async def run_browser_automation(task: str) -> str:
    """Run the full browser automation pipeline for a given task.

    Creates the Stagehand session, builds the agent pipeline, and
    executes the multi-agent workflow from task planning through
    to report generation.

    Args:
        task: The user's browser automation task description.

    Returns:
        str: The final automation report.
    """
    config = load_config()
    model = create_openrouter_model(config)
    hooks = BrowserAutomationHooks()

    # Create browser session
    client, session = await create_stagehand_session(config)

    # Create browser context
    browser_context = BrowserContext(
        task=task,
        config=config,
        session=session,
    )

    # Build agent pipeline
    planner_agent = build_agent_pipeline(model, hooks)

    # Compose input
    automation_input = (
        f"BROWSER AUTOMATION TASK\n"
        f"Task: {task}\n\n"
        f"Please plan the browser automation, navigate to the target page(s), "
        f"interact with elements as needed, extract the requested data, "
        f"validate the results, and produce a structured report."
    )

    print("\n" + "=" * 60)
    print("  STARTING BROWSER AUTOMATION PIPELINE")
    print("=" * 60)
    print(f"\nTask: {task}\n")

    run_config = RunConfig(
        workflow_name="browser_automation",
        tracing_disabled=True,
    )

    result = await Runner.run(
        starting_agent=planner_agent,
        input=automation_input,
        context=browser_context,
        max_turns=30,
        run_config=run_config,
    )

    # End the browser session
    await session.end()
    logger.info("Stagehand session ended.")

    return result.final_output


async def main():
    """Main entry point for the Browser Automation Agent."""
    print("\n" + "=" * 60)
    print("  BROWSER AUTOMATION AGENT")
    print("=" * 60)
    print("\nSelect a predefined scenario or enter a custom task:\n")

    for key, scenario in SCENARIOS.items():
        print(f"  [{key}] {scenario['name']}")
        print(f"      {scenario['task']}\n")
    print("  [3] Enter a custom task\n")

    choice = input("Select (1/2/3): ").strip()

    match choice:
        case "1" | "2":
            task = SCENARIOS[choice]["task"]
        case "3":
            task = input("\nEnter your browser automation task: ").strip()
            if not task:
                print("No task provided. Exiting.")
                return
        case _:
            print("Invalid choice. Exiting.")
            return

    report = await run_browser_automation(task)

    print("\n" + "=" * 60)
    print("  AUTOMATION REPORT")
    print("=" * 60)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
