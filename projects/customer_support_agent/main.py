"""Customer Support Agent -- Entry Point.

Orchestrates a multi-agent customer support pipeline using OpenAI Agents SDK
with OpenRouter as the LLM provider. Simulates realistic customer support
scenarios and runs them through specialized agents for intake, order support,
billing support, technical support, escalation, and resolution.

Usage:
    uv run python -m customer_support_agent.main
"""

import asyncio
import logging

from agents import (AgentHooks, AsyncOpenAI, ModelSettings,
                    OpenAIChatCompletionsModel, RunConfig, Runner,
                    set_tracing_disabled)
from customer_support_agent.agents.billing_support import \
    create_billing_support_agent
from customer_support_agent.agents.escalation import create_escalation_agent
from customer_support_agent.agents.intake_router import \
    create_intake_router_agent
from customer_support_agent.agents.order_support import \
    create_order_support_agent
from customer_support_agent.agents.resolution import create_resolution_agent
from customer_support_agent.agents.technical_support import \
    create_technical_support_agent
from customer_support_agent.simulators.scenario_engine import (
    ScenarioType, generate_scenario, list_scenarios)
from customer_support_agent.utils.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class CustomerSupportHooks(AgentHooks):
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
        Intake & Router -> [Order Support | Billing Support | Technical Support | Escalation]
        Order/Billing/Technical -> [Escalation | Resolution]
        Escalation -> Resolution (terminal)

    Args:
        model: The OpenRouter-backed model instance.
        hooks: AgentHooks instance for lifecycle callbacks.

    Returns:
        Agent: The intake & router agent (entry point of the pipeline).
    """
    # Build from terminal agent backwards
    resolution = create_resolution_agent(hooks=hooks)
    escalation = create_escalation_agent(resolution, hooks=hooks)
    order_support = create_order_support_agent(escalation, resolution, hooks=hooks)
    billing_support = create_billing_support_agent(escalation, resolution, hooks=hooks)
    technical_support = create_technical_support_agent(
        escalation, resolution, hooks=hooks
    )
    intake_router = create_intake_router_agent(
        order_support,
        billing_support,
        technical_support,
        escalation,
        hooks=hooks,
    )

    # Set model on all agents to use OpenRouter via Chat Completions
    all_agents = [
        intake_router,
        order_support,
        billing_support,
        technical_support,
        escalation,
        resolution,
    ]
    for agent in all_agents:
        agent.model = model

    logger.info(
        "Agent pipeline built: Intake -> [Order/Billing/Technical/Escalation] -> Resolution"
    )
    return intake_router


def select_scenario() -> ScenarioType:
    """Interactive scenario selection.

    Presents available scenarios to the user and returns their choice.

    Returns:
        ScenarioType: The selected scenario type.
    """
    scenarios = list_scenarios()

    print("\n" + "=" * 60)
    print("  CUSTOMER SUPPORT AGENT")
    print("=" * 60)
    print("\nAvailable support scenarios:\n")

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


async def run_customer_support(scenario_type: ScenarioType) -> str:
    """Run the full customer support pipeline on a simulated scenario.

    Generates scenario data, builds the agent pipeline, and executes
    the multi-agent workflow from intake through to resolution.

    Args:
        scenario_type: The type of support scenario to simulate.

    Returns:
        str: The final resolution report.
    """
    # Setup
    model = create_openrouter_model()
    hooks = CustomerSupportHooks()

    # Generate scenario data
    print(f"\nGenerating scenario: {scenario_type}...")
    scenario_data = generate_scenario(scenario_type)
    print(
        f"Generated: Customer={scenario_data.customer.name} ({scenario_data.customer.tier}), "
        f"{len(scenario_data.orders)} orders, {len(scenario_data.returns)} returns, "
        f"{len(scenario_data.subscriptions)} subscriptions, {len(scenario_data.invoices)} invoices, "
        f"{len(scenario_data.knowledge_base)} KB articles"
    )

    # Build agent pipeline
    intake_agent = build_agent_pipeline(model, hooks)

    # Compose the initial support request
    ticket_info = ""
    if scenario_data.ticket:
        ticket_info = (
            f"\nSupport Ticket: {scenario_data.ticket.ticket_id}\n"
            f"Category: {scenario_data.ticket.category}\n"
            f"Priority: {scenario_data.ticket.priority}\n"
            f"Subject: {scenario_data.ticket.subject}\n"
        )

    support_input = (
        f"CUSTOMER SUPPORT REQUEST\n"
        f"Customer ID: {scenario_data.customer.customer_id}\n"
        f"Customer: {scenario_data.customer.name} ({scenario_data.customer.tier} tier)\n"
        f"{ticket_info}\n"
        f"Customer Message:\n{scenario_data.customer_query}\n\n"
        f"Please help this customer by investigating their issue, taking appropriate actions, "
        f"and providing a complete resolution."
    )

    print("\n" + "=" * 60)
    print("  STARTING CUSTOMER SUPPORT PIPELINE")
    print("=" * 60)
    print(f"\nInput:\n{support_input}\n")

    # Run the agent pipeline
    run_config = RunConfig(
        workflow_name="customer_support",
        tracing_disabled=True,
    )

    result = await Runner.run(
        starting_agent=intake_agent,
        input=support_input,
        context=scenario_data,
        max_turns=40,
        run_config=run_config,
    )

    return result.final_output


async def main():
    """Main entry point for the Customer Support Agent."""
    scenario_type = select_scenario()

    report = await run_customer_support(scenario_type)

    print("\n" + "=" * 60)
    print("  FINAL RESOLUTION REPORT")
    print("=" * 60)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
