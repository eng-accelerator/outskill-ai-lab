"""Deep Research Agent -- Entry Point.

Orchestrates a multi-agent research pipeline using OpenAI Agents SDK
with OpenRouter as the LLM provider. Conducts real web searches,
academic lookups, news retrieval, and content extraction to produce
comprehensive research reports with citations.

Usage:
    uv run python -m deep_research_agent.main
"""

import asyncio
import logging

from agents import (AgentHooks, AsyncOpenAI, ModelSettings,
                    OpenAIChatCompletionsModel, RunConfig, Runner,
                    set_tracing_disabled)
from deep_research_agent.agents.academic_researcher import \
    create_academic_researcher_agent
from deep_research_agent.agents.content_extractor import \
    create_content_extractor_agent
from deep_research_agent.agents.news_researcher import \
    create_news_researcher_agent
from deep_research_agent.agents.report_writer import create_report_writer_agent
from deep_research_agent.agents.research_planner import \
    create_research_planner_agent
from deep_research_agent.agents.synthesizer import create_synthesizer_agent
from deep_research_agent.agents.web_researcher import \
    create_web_researcher_agent
from deep_research_agent.models.research import ResearchContext
from deep_research_agent.utils.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class DeepResearchHooks(AgentHooks):
    """Lifecycle hooks for observability during agent execution."""

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


def create_openrouter_model() -> OpenAIChatCompletionsModel:
    """Create an OpenRouter-backed model using Chat Completions API.

    Reads OPENROUTER_API_KEY from environment and creates an
    OpenAIChatCompletionsModel pointing to OpenRouter's endpoint.

    Returns:
        OpenAIChatCompletionsModel: Model instance configured for OpenRouter.

    Raises:
        AssertionError: If OPENROUTER_API_KEY is not set.
    """
    config = load_config()
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

    # Disable tracing since we're not using OpenAI's tracing backend
    set_tracing_disabled(True)

    model = OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=client,
    )

    logger.info(
        "OpenRouter model configured: base_url=%s, model=%s", base_url, model_name
    )
    return model


def build_agent_pipeline(model: OpenAIChatCompletionsModel, hooks: AgentHooks):
    """Build the complete agent pipeline with handoff chain.

    Constructs agents in reverse order (terminal first) to wire handoffs.

    Pipeline:
        Research Planner -> [Web Researcher | Academic Researcher | News Researcher]
        All Researchers -> Content Extractor -> Synthesizer -> Report Writer (terminal)

    Args:
        model: The OpenRouter-backed model instance.
        hooks: AgentHooks instance for lifecycle callbacks.

    Returns:
        Agent: The research planner agent (entry point of the pipeline).
    """
    # Build from terminal agent backwards
    report_writer = create_report_writer_agent(hooks=hooks)
    synthesizer = create_synthesizer_agent(report_writer, hooks=hooks)
    content_extractor = create_content_extractor_agent(synthesizer, hooks=hooks)
    web_researcher = create_web_researcher_agent(content_extractor, hooks=hooks)
    academic_researcher = create_academic_researcher_agent(
        content_extractor, hooks=hooks
    )
    news_researcher = create_news_researcher_agent(content_extractor, hooks=hooks)
    research_planner = create_research_planner_agent(
        web_researcher,
        academic_researcher,
        news_researcher,
        hooks=hooks,
    )

    # Set model on all agents to use OpenRouter via Chat Completions
    all_agents = [
        research_planner,
        web_researcher,
        academic_researcher,
        news_researcher,
        content_extractor,
        synthesizer,
        report_writer,
    ]
    for agent in all_agents:
        agent.model = model

    logger.info(
        "Agent pipeline built: Planner -> [Web/Academic/News] -> Extractor -> Synthesizer -> Writer"
    )
    return research_planner


async def run_deep_research(query: str) -> str:
    """Run the full deep research pipeline on a user query.

    Creates the research context, builds the agent pipeline, and
    executes the multi-agent workflow from planning through to
    report generation.

    Args:
        query: The user's research question.

    Returns:
        str: The final research report.
    """
    # Setup
    config = load_config()
    model = create_openrouter_model()
    hooks = DeepResearchHooks()

    # Create research context
    research_context = ResearchContext(
        query=query,
        config=config,
    )

    # Build agent pipeline
    planner_agent = build_agent_pipeline(model, hooks)

    # Compose the research input
    research_input = (
        f"DEEP RESEARCH REQUEST\n"
        f"Query: {query}\n\n"
        f"Please conduct comprehensive research on this topic. "
        f"Decompose the query into sub-questions, search multiple sources, "
        f"extract relevant content, cross-reference findings, and produce "
        f"a detailed research report with citations and confidence assessment."
    )

    print("\n" + "=" * 60)
    print("  STARTING DEEP RESEARCH PIPELINE")
    print("=" * 60)
    print(f"\nQuery: {query}\n")

    # Run the agent pipeline
    run_config = RunConfig(
        workflow_name="deep_research",
        tracing_disabled=True,
    )

    result = await Runner.run(
        starting_agent=planner_agent,
        input=research_input,
        context=research_context,
        max_turns=50,
        run_config=run_config,
    )

    return result.final_output


async def main():
    """Main entry point for the Deep Research Agent."""
    print("\n" + "=" * 60)
    print("  DEEP RESEARCH AGENT")
    print("=" * 60)
    print("\nEnter your research question below.")
    print("The agent will search the web, academic databases, news,")
    print("and community sources to produce a comprehensive report.\n")

    query = input("Research query: ").strip()
    if not query:
        print("No query provided. Exiting.")
        return

    report = await run_deep_research(query)

    print("\n" + "=" * 60)
    print("  FINAL RESEARCH REPORT")
    print("=" * 60)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
