"""AI Ops Incident Response Agent -- Entry Point.

Orchestrates a multi-agent incident response pipeline using OpenAI Agents SDK
with OpenRouter as the LLM provider. Simulates realistic incident scenarios
and runs them through specialized agents for triage, analysis, RCA,
remediation, and reporting.

Usage:
    uv run python -m aiops_incident_response_agent.main
"""

import asyncio
import logging
import os
import sys

from agents import (
    AgentHooks,
    AsyncOpenAI,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    set_tracing_disabled,
)

from aiops_incident_response_agent.agents.incident_reporter import create_incident_reporter_agent
from aiops_incident_response_agent.agents.log_analyzer import create_log_analyzer_agent
from aiops_incident_response_agent.agents.metrics_analyzer import create_metrics_analyzer_agent
from aiops_incident_response_agent.agents.remediation import create_remediation_agent
from aiops_incident_response_agent.agents.root_cause_analyzer import create_rca_agent
from aiops_incident_response_agent.agents.triage import create_triage_agent
from aiops_incident_response_agent.simulators.scenario_engine import (
    ScenarioType,
    generate_scenario,
    list_scenarios,
)
from aiops_incident_response_agent.utils.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class IncidentResponseHooks(AgentHooks):
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

    logger.info("OpenRouter model configured: base_url=%s, model=%s", base_url, model_name)
    return model


def build_agent_pipeline(model: OpenAIChatCompletionsModel, hooks: AgentHooks):
    """Build the complete agent pipeline with handoff chain.

    Constructs agents in reverse order (terminal first) to wire handoffs.

    Args:
        model: The OpenRouter-backed model instance.
        hooks: AgentHooks instance for lifecycle callbacks.

    Returns:
        Agent: The triage agent (entry point of the pipeline).
    """
    # Build from terminal agent backwards
    reporter = create_incident_reporter_agent(hooks=hooks)
    remediation = create_remediation_agent(reporter, hooks=hooks)
    rca = create_rca_agent(remediation, hooks=hooks)
    log_analyzer = create_log_analyzer_agent(rca, hooks=hooks)
    metrics_analyzer = create_metrics_analyzer_agent(rca, hooks=hooks)
    triage = create_triage_agent(log_analyzer, metrics_analyzer, hooks=hooks)

    # Set model on all agents to use OpenRouter via Chat Completions
    for agent in [triage, log_analyzer, metrics_analyzer, rca, remediation, reporter]:
        agent.model = model

    logger.info("Agent pipeline built: Triage -> [Log/Metrics Analyzer] -> RCA -> Remediation -> Reporter")
    return triage


def select_scenario() -> ScenarioType:
    """Interactive scenario selection.

    Presents available scenarios to the user and returns their choice.

    Returns:
        ScenarioType: The selected scenario type.
    """
    scenarios = list_scenarios()

    print("\n" + "=" * 60)
    print("  AI OPS INCIDENT RESPONSE AGENT")
    print("=" * 60)
    print("\nAvailable incident scenarios:\n")

    for i, (scenario_type, description) in enumerate(scenarios, 1):
        print(f"  {i}. {scenario_type}")
        print(f"     {description}\n")

    while True:
        choice = input("Select scenario (1-5): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(scenarios):
            selected = scenarios[int(choice) - 1][0]
            logger.info("Selected scenario: %s", selected)
            return selected
        print("Invalid choice. Please enter a number 1-5.")


async def run_incident_response(scenario_type: ScenarioType) -> str:
    """Run the full incident response pipeline on a simulated scenario.

    Generates scenario data, builds the agent pipeline, and executes
    the multi-agent workflow from triage through to reporting.

    Args:
        scenario_type: The type of incident scenario to simulate.

    Returns:
        str: The final incident report.
    """
    # Setup
    model = create_openrouter_model()
    hooks = IncidentResponseHooks()

    # Generate scenario data
    print(f"\nGenerating scenario: {scenario_type}...")
    scenario_data = generate_scenario(scenario_type)
    print(f"Generated: {len(scenario_data.logs)} logs, {len(scenario_data.metrics)} metrics, "
          f"{len(scenario_data.alerts)} alerts, {len(scenario_data.traces)} traces")

    # Build agent pipeline
    triage_agent = build_agent_pipeline(model, hooks)

    # Compose the initial incident alert message
    alert_summary = "\n".join(
        f"- [{a.severity.upper()}] {a.service}: {a.message}"
        for a in scenario_data.alerts
    )
    incident_input = (
        f"INCIDENT ALERT\n"
        f"Scenario: {scenario_data.description}\n\n"
        f"Active Alerts:\n{alert_summary}\n\n"
        f"Please triage this incident, analyze the root cause, "
        f"propose remediation, and generate a complete incident report."
    )

    print("\n" + "=" * 60)
    print("  STARTING INCIDENT RESPONSE PIPELINE")
    print("=" * 60)
    print(f"\nInput:\n{incident_input}\n")

    # Run the agent pipeline
    run_config = RunConfig(
        workflow_name="aiops_incident_response",
        tracing_disabled=True,
    )

    result = await Runner.run(
        starting_agent=triage_agent,
        input=incident_input,
        context=scenario_data,
        max_turns=40,
        run_config=run_config,
    )

    return result.final_output


async def main():
    """Main entry point for the AI Ops Incident Response Agent."""
    scenario_type = select_scenario()

    report = await run_incident_response(scenario_type)

    print("\n" + "=" * 60)
    print("  FINAL INCIDENT REPORT")
    print("=" * 60)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
