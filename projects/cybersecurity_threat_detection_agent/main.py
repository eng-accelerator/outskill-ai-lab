"""Cybersecurity Threat Detection Agent -- Entry Point.

Orchestrates a multi-agent threat detection pipeline using OpenAI Agents SDK
with OpenRouter as the LLM provider. Simulates realistic cybersecurity
threat scenarios and runs them through specialized agents for alert intake,
auth analysis, network analysis, threat intelligence, containment, and reporting.

Usage:
    uv run python -m cybersecurity_threat_detection_agent.main
"""

import asyncio
import logging

from agents import (
    AgentHooks,
    AsyncOpenAI,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    set_tracing_disabled,
)

from cybersecurity_threat_detection_agent.agents.alert_intake import create_alert_intake_agent
from cybersecurity_threat_detection_agent.agents.auth_analyzer import create_auth_analyzer_agent
from cybersecurity_threat_detection_agent.agents.containment import create_containment_agent
from cybersecurity_threat_detection_agent.agents.network_analyzer import create_network_analyzer_agent
from cybersecurity_threat_detection_agent.agents.soc_reporter import create_soc_reporter_agent
from cybersecurity_threat_detection_agent.agents.threat_intel import create_threat_intel_agent
from cybersecurity_threat_detection_agent.simulators.scenario_engine import (
    ScenarioType,
    generate_scenario,
    list_scenarios,
)
from cybersecurity_threat_detection_agent.utils.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class ThreatDetectionHooks(AgentHooks):
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
        Agent: The alert intake agent (entry point of the pipeline).
    """
    # Build from terminal agent backwards
    soc_reporter = create_soc_reporter_agent(hooks=hooks)
    containment = create_containment_agent(soc_reporter, hooks=hooks)
    threat_intel = create_threat_intel_agent(containment, hooks=hooks)
    auth_analyzer = create_auth_analyzer_agent(threat_intel, hooks=hooks)
    network_analyzer = create_network_analyzer_agent(threat_intel, hooks=hooks)
    alert_intake = create_alert_intake_agent(auth_analyzer, network_analyzer, hooks=hooks)

    # Set model on all agents to use OpenRouter via Chat Completions
    for agent in [alert_intake, auth_analyzer, network_analyzer, threat_intel, containment, soc_reporter]:
        agent.model = model

    logger.info("Agent pipeline built: Alert Intake -> [Auth/Network Analyzer] -> Threat Intel -> Containment -> SOC Reporter")
    return alert_intake


def select_scenario() -> ScenarioType:
    """Interactive scenario selection.

    Presents available scenarios to the user and returns their choice.

    Returns:
        ScenarioType: The selected scenario type.
    """
    scenarios = list_scenarios()

    print("\n" + "=" * 60)
    print("  CYBERSECURITY THREAT DETECTION AGENT")
    print("=" * 60)
    print("\nAvailable threat scenarios:\n")

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


async def run_threat_detection(scenario_type: ScenarioType) -> str:
    """Run the full threat detection pipeline on a simulated scenario.

    Generates scenario data, builds the agent pipeline, and executes
    the multi-agent workflow from alert intake through to SOC reporting.

    Args:
        scenario_type: The type of threat scenario to simulate.

    Returns:
        str: The final SOC incident report.
    """
    # Setup
    model = create_openrouter_model()
    hooks = ThreatDetectionHooks()

    # Generate scenario data
    print(f"\nGenerating scenario: {scenario_type}...")
    scenario_data = generate_scenario(scenario_type)
    print(f"Generated: {len(scenario_data.auth_logs)} auth logs, "
          f"{len(scenario_data.network_logs)} network logs, "
          f"{len(scenario_data.api_access_logs)} API logs, "
          f"{len(scenario_data.endpoint_events)} endpoint events, "
          f"{len(scenario_data.cloud_audit_logs)} cloud audit entries, "
          f"{len(scenario_data.alerts)} alerts")

    # Build agent pipeline
    alert_intake_agent = build_agent_pipeline(model, hooks)

    # Compose the initial security alert message
    alert_summary = "\n".join(
        f"- [{a.severity.upper()}] [{a.source}] {a.category}: {a.message}"
        for a in scenario_data.alerts
    )
    threat_input = (
        f"SECURITY THREAT DETECTED\n"
        f"Scenario: {scenario_data.description}\n\n"
        f"Active Security Alerts:\n{alert_summary}\n\n"
        f"Please analyze this threat, enrich with threat intelligence, "
        f"propose containment actions, and generate a complete SOC incident report."
    )

    print("\n" + "=" * 60)
    print("  STARTING THREAT DETECTION PIPELINE")
    print("=" * 60)
    print(f"\nInput:\n{threat_input}\n")

    # Run the agent pipeline
    run_config = RunConfig(
        workflow_name="cybersecurity_threat_detection",
        tracing_disabled=True,
    )

    result = await Runner.run(
        starting_agent=alert_intake_agent,
        input=threat_input,
        context=scenario_data,
        max_turns=40,
        run_config=run_config,
    )

    return result.final_output


async def main():
    """Main entry point for the Cybersecurity Threat Detection Agent."""
    scenario_type = select_scenario()

    report = await run_threat_detection(scenario_type)

    print("\n" + "=" * 60)
    print("  FINAL SOC INCIDENT REPORT")
    print("=" * 60)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
