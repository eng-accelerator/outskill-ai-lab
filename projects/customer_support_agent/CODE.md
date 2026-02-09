# Customer Support Agent — Code Guide

This document covers the AI agent concepts, OpenAI Agents SDK constructs, and implementation patterns used in the Customer Support Agent system.

## AI Agent Concepts

### What Is an Agent?

An agent is an AI system that can:
1. **Perceive** — Observe its environment through tools and context
2. **Plan** — Decide what actions to take based on its instructions and observations
3. **Act** — Execute actions through tool calls
4. **Reflect** — Evaluate outcomes and decide next steps (handoff or continue)

In this system, each agent is a specialized customer support function with its own tools, instructions, and handoff targets.

### Multi-Agent Architecture

Instead of one monolithic agent, the system uses **6 specialized agents** that collaborate through handoffs. This follows the **Single Responsibility Principle** — each agent is an expert in one domain:

- **Intake & Router** — Classification and routing expert
- **Order Support** — Order management expert
- **Billing Support** — Financial operations expert
- **Technical Support** — Product and system diagnostics expert
- **Escalation** — Human coordination expert
- **Resolution & CSAT** — Quality assurance and reporting expert

### Handoff Pattern

Agents transfer control to other agents using **handoffs**. When an agent hands off:
1. The current agent's conversation context is passed to the target agent
2. The target agent receives the full history plus the handoff message
3. The source agent stops processing; the target agent takes over

This creates a **pipeline** where each agent adds value and passes enriched context forward.

## OpenAI Agents SDK Constructs

### Agent

The core building block. An `Agent` has:

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Billing Support Agent",       # Display name
    instructions="You are an expert...", # System prompt
    tools=[get_billing_info, ...],       # Available tools
    handoffs=[escalation, resolution],   # Agents it can transfer to
    input_guardrails=[...],              # Input validators
    output_guardrails=[...],             # Output validators
    hooks=hooks,                         # Lifecycle callbacks
    model_settings=ModelSettings(        # LLM configuration
        temperature=0.2
    ),
)
```

Key properties:
- `instructions` — The system prompt that defines the agent's role, workflow, and constraints
- `tools` — Functions the agent can call to interact with external systems
- `handoffs` — Other agents this agent can transfer control to
- `model_settings` — Controls LLM behavior (temperature, etc.)

### function_tool

Decorates a Python function to make it callable by an agent:

```python
from agents import RunContextWrapper, function_tool

@function_tool
def lookup_order(ctx: RunContextWrapper[ScenarioData], order_id: str) -> str:
    """Look up full order details including items, status, and shipment info.

    Args:
        ctx: Run context containing the scenario data.
        order_id: The order ID to look up.

    Returns:
        str: JSON string of the order details.
    """
    scenario = ctx.context
    # ... implementation
    return json.dumps(order_data, indent=2)
```

Key points:
- The **docstring** is sent to the LLM as the tool description — it must be clear and accurate
- The **first parameter** `ctx: RunContextWrapper[ScenarioData]` provides access to the shared scenario data
- Additional parameters become the tool's input schema (the LLM generates these)
- Return value must be a **string** (typically JSON)

### RunContextWrapper

Provides typed access to shared context across all agents and tools:

```python
@function_tool
def fetch_customer_profile(ctx: RunContextWrapper[ScenarioData], customer_id: str) -> str:
    scenario = ctx.context  # Access the ScenarioData object
    # scenario.customer, scenario.orders, scenario.invoices, etc.
```

The context type parameter `[ScenarioData]` ensures type safety. All tools in the system share the same `ScenarioData` context, which contains:
- Customer profiles
- Orders, returns
- Subscriptions, invoices, payments, refunds
- Knowledge base articles
- Support ticket metadata

### Handoffs

Agents specify which other agents they can transfer to:

```python
# Order Support can hand off to Escalation or Resolution
order_support = Agent(
    name="Order Support Agent",
    handoffs=[escalation_agent, resolution_agent],
    ...
)
```

The SDK automatically creates transfer tools named `transfer_to_<agent_name>`. The agent's instructions tell it when to use each transfer:

```
- If resolved -> use transfer_to_resolution___csat_agent
- If complex -> use transfer_to_escalation_agent
```

### InputGuardrail

Validates input before an agent processes it:

```python
from agents import InputGuardrail, GuardrailFunctionOutput, RunContextWrapper

async def validate_support_input(
    ctx: RunContextWrapper[ScenarioData],
    agent: Agent,
    input_data: str | list,
) -> GuardrailFunctionOutput:
    scenario = ctx.context

    if scenario.customer is None:
        return GuardrailFunctionOutput(
            output_info="No customer profile available.",
            tripwire_triggered=True,  # Blocks execution
        )

    return GuardrailFunctionOutput(
        output_info="Validated successfully.",
        tripwire_triggered=False,  # Allows execution
    )

support_input_guardrail = InputGuardrail(
    guardrail_function=validate_support_input,
    name="support_input_validation",
)
```

When `tripwire_triggered=True`, the pipeline stops with the `output_info` message.

### OutputGuardrail

Validates agent output before it's returned:

```python
from agents import OutputGuardrail, GuardrailFunctionOutput

async def validate_response_safety(
    ctx: RunContextWrapper[ScenarioData],
    agent: Agent,
    output: str,
) -> GuardrailFunctionOutput:
    # Check for PII, inappropriate language, unauthorized refunds
    if _CREDIT_CARD_PATTERN.search(output):
        return GuardrailFunctionOutput(
            output_info="Response blocked: Contains credit card number.",
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(
        output_info="Response passed safety validation.",
        tripwire_triggered=False,
    )

response_safety_guardrail = OutputGuardrail(
    guardrail_function=validate_response_safety,
    name="response_safety_check",
)
```

### AgentHooks

Lifecycle callbacks for observability:

```python
from agents import AgentHooks

class CustomerSupportHooks(AgentHooks):
    async def on_start(self, context, agent):
        print(f"AGENT: {agent.name}")

    async def on_end(self, context, agent, output):
        print(f"[{agent.name}] completed.")

    async def on_tool_start(self, context, agent, tool):
        print(f"[{agent.name}] calling tool: {tool.name}")

    async def on_tool_end(self, context, agent, tool, result):
        print(f"[{agent.name}] tool {tool.name} completed.")

    async def on_handoff(self, context, agent, source):
        print(f"Handoff: {source.name} -> {agent.name}")
```

### Runner

Executes the agent pipeline:

```python
from agents import Runner, RunConfig

run_config = RunConfig(
    workflow_name="customer_support",
    tracing_disabled=True,
)

result = await Runner.run(
    starting_agent=intake_agent,  # Entry point
    input=support_input,          # Initial message
    context=scenario_data,        # Shared context (ScenarioData)
    max_turns=40,                 # Maximum agent turns
    run_config=run_config,
)

final_report = result.final_output  # Terminal agent's output
```

### OpenAIChatCompletionsModel

Connects to OpenRouter (or any OpenAI-compatible API):

```python
from agents import AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="your_key",
)

set_tracing_disabled(True)  # Disable OpenAI tracing

model = OpenAIChatCompletionsModel(
    model="openai/gpt-5-mini",
    openai_client=client,
)

# Apply to all agents
for agent in all_agents:
    agent.model = model
```

### ModelSettings

Controls LLM behavior per agent:

```python
from agents import ModelSettings

# Lower temperature for deterministic routing
intake_agent.model_settings = ModelSettings(temperature=0.2)

# Slightly higher for creative support responses
order_support.model_settings = ModelSettings(temperature=0.3)
```

## Tool Design Patterns

### Context-Aware Tools

All tools receive the shared `ScenarioData` context via `RunContextWrapper`:

```python
@function_tool
def get_billing_info(ctx: RunContextWrapper[ScenarioData], customer_id: str) -> str:
    scenario = ctx.context
    subs = [s for s in scenario.subscriptions if s.customer_id == customer_id]
    invoices = [i for i in scenario.invoices if i.customer_id == customer_id]
    # ... build response
```

### Validation Within Tools

Tools validate inputs and return structured errors:

```python
@function_tool
def process_refund(ctx, payment_id: str, amount: float, reason: str) -> str:
    if target_payment is None:
        return json.dumps({"error": f"Payment {payment_id} not found"})

    if amount > target_payment.amount:
        return json.dumps({"error": f"Refund ${amount} exceeds payment ${target_payment.amount}"})

    requires_approval = amount > 500.0  # Business rule
    # ...
```

### Simulated External Systems

Tools simulate real external systems (CRM, OMS, billing platform) using the scenario data. This makes the system self-contained for testing while maintaining realistic tool interfaces:

```python
# Simulated shipment tracking with delay analysis
@function_tool
def track_shipment(ctx, tracking_number: str) -> str:
    for order in scenario.orders:
        if order.shipment and order.shipment.tracking_number == tracking_number:
            shipment_data = asdict(order.shipment)
            if order.shipment.status == "in_transit":
                shipment_data["delay_analysis"] = {
                    "note": "Package may be experiencing carrier delays."
                }
            return json.dumps(shipment_data)
```

### Sentiment Analysis Tool

The sentiment analyzer uses keyword matching to assess customer emotional state:

```python
@function_tool
def analyze_sentiment(ctx, message: str) -> str:
    # Check negative indicators: "frustrated", "angry", "disappointed", etc.
    # Check very negative: "extremely frustrated", "cancelling everything", etc.
    # Check positive: "thank", "appreciate", "great", etc.
    # Check urgency: "urgent", "asap", "immediately", etc.
    # Score: -1.0 (very negative) to 1.0 (very positive)
```

## Pipeline Construction Pattern

Agents are built in **reverse order** (terminal first) to wire handoffs:

```python
def build_agent_pipeline(model, hooks):
    # 1. Terminal agent (no handoffs)
    resolution = create_resolution_agent(hooks=hooks)

    # 2. Escalation (hands off to resolution)
    escalation = create_escalation_agent(resolution, hooks=hooks)

    # 3. Specialists (hand off to escalation or resolution)
    order_support = create_order_support_agent(escalation, resolution, hooks=hooks)
    billing_support = create_billing_support_agent(escalation, resolution, hooks=hooks)
    technical_support = create_technical_support_agent(escalation, resolution, hooks=hooks)

    # 4. Entry point (routes to all specialists + escalation)
    intake_router = create_intake_router_agent(
        order_support, billing_support, technical_support, escalation, hooks=hooks,
    )

    # 5. Set model on all agents
    for agent in [intake_router, order_support, billing_support,
                  technical_support, escalation, resolution]:
        agent.model = model

    return intake_router
```

## CSAT Prediction Model

The CSAT prediction uses a weighted scoring model:

```
Base Score: 3.0

+ Resolution Quality:  excellent(+1.5), good(+0.8), fair(0), poor(-1.5)
+ Response Time:       fast(+0.5), acceptable(0), slow(-0.8)
+ Issue Resolved:      yes(+0.5), no(-1.0)
+ Escalation:          no(0), yes(-0.3)
+ Customer Tier:       platinum(-0.3), gold(-0.1), silver(0), bronze(+0.2)
                       (higher tier = higher expectations)

Final Score: clamp(round(sum), 1, 5)
```

The tier adjustment reflects that premium customers have higher service expectations, so the same resolution quality may produce lower satisfaction for platinum vs. bronze customers.

## Error Handling Philosophy

Following the project's coding guidelines:
- **Errors as return values** — Tools return JSON error objects instead of raising exceptions
- **Assertions for invariants** — `assert scenario_type in generators` for programmer errors
- **Graceful degradation** — Specialist agents can escalate when they can't resolve
- **No nested try-except** — Tool failures are communicated through return values
- **Liberal logging** — All tool invocations and results are logged for observability

## Key Design Decisions

1. **Frozen dataclasses** — All models are immutable (`frozen=True`) to prevent accidental mutation
2. **Literal types over enums** — `CustomerTier = Literal["bronze", "silver", "gold", "platinum"]` for simplicity
3. **JSON tool responses** — All tools return JSON strings for consistent LLM parsing
4. **Dual handoff from specialists** — Each specialist can go to Escalation (unresolved) or Resolution (resolved)
5. **Simulated data stack** — Self-contained testing without external dependencies
6. **Keyword sentiment analysis** — Simple but effective for demo purposes; production would use a dedicated NLP model
7. **CSAT prediction** — Algorithmic scoring based on interaction metrics; production would use ML model trained on historical data
