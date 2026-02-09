# Code Guide

This document explains the AI agent concepts, OpenAI Agents SDK constructs, and implementation patterns used throughout the codebase. It serves as a reference for understanding how the code works and why specific decisions were made.

---

## Table of Contents

1. [AI Agent Concepts](#ai-agent-concepts)
2. [OpenAI Agents SDK Concepts](#openai-agents-sdk-concepts)
3. [OpenRouter Integration](#openrouter-integration)
4. [Tool Implementation Patterns](#tool-implementation-patterns)
5. [Handoff Mechanics](#handoff-mechanics)
6. [Guardrail System](#guardrail-system)
7. [Context and State Management](#context-and-state-management)
8. [Runner and Execution Model](#runner-and-execution-model)
9. [Hooks and Observability](#hooks-and-observability)
10. [Model Configuration](#model-configuration)

---

## AI Agent Concepts

### What is an AI Agent?

An AI agent is a system that can:
- **Perceive** its environment (via tools that read data)
- **Reason** about what to do (via LLM inference)
- **Act** on its environment (via tool calls)
- **Adapt** based on feedback (via observing tool results and adjusting)

In this system, each of the six agents perceives through its tools, reasons via the LLM, acts by calling tools and handing off, and adapts by processing tool outputs before deciding the next step.

### Multi-Agent Systems

A multi-agent system uses multiple specialized agents instead of one monolithic agent. Benefits:
- **Separation of concerns** — Each agent is an expert in one domain
- **Simpler prompts** — Each agent's instructions are focused and short
- **Better tool scoping** — Each agent only sees tools relevant to its task
- **Debuggability** — You can trace exactly which agent made which decision

### Agent Pipeline vs. Agent Swarm

This system uses a **pipeline** (linear chain with one routing point), not a swarm:

```
Pipeline:  A → B → C → D → E → F
Swarm:     A ↔ B ↔ C ↔ D (any agent can call any other)
```

The pipeline is simpler, more predictable, and easier to debug. The one routing point (Triage → Log Analyzer OR Metrics Analyzer) adds flexibility without the complexity of a full swarm.

### Handoffs vs. Function Calls

Two ways agents can interact:
- **Tool/Function calls**: Agent calls a function, gets a result, continues reasoning
- **Handoffs**: Agent transfers control entirely to another agent, passing the full conversation history

In this system, tools are for data gathering (reading from the simulated observability stack), while handoffs are for agent-to-agent delegation (passing the investigation to the next specialist).

---

## OpenAI Agents SDK Concepts

The [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) (`openai-agents` package) provides the core building blocks used throughout this project. Below is every SDK construct used, with explanations.

### `Agent`

The fundamental building block. An `Agent` is a configured LLM with instructions, tools, handoffs, and guardrails.

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Triage Agent",                    # Display name for logging
    instructions="You are an SRE...",        # System prompt defining the agent's role
    tools=[fetch_alerts, get_health],        # Functions the agent can call
    handoffs=[log_analyzer, metrics_analyzer], # Agents it can transfer to
    input_guardrails=[input_guardrail],      # Validates input before processing
    output_guardrails=[output_guardrail],    # Validates output before returning
    hooks=hooks,                             # Lifecycle callbacks
    model_settings=ModelSettings(temperature=0.2),  # LLM parameters
)
```

**Key properties:**
- `name` — Used in logging and as part of the auto-generated handoff tool name
- `instructions` — The system prompt. This is the most important part — it defines the agent's behavior, workflow, and constraints
- `tools` — List of `@function_tool` decorated functions the agent can invoke
- `handoffs` — List of `Agent` objects this agent can transfer control to. The SDK auto-generates transfer tools (e.g., `transfer_to_log_analyzer_agent`)
- `model` — Set after construction to point to the OpenRouter model
- `model_settings` — Controls LLM parameters like `temperature`

### `@function_tool`

Decorator that converts a Python function into a tool callable by an agent.

```python
from agents import RunContextWrapper, function_tool

@function_tool
def fetch_active_alerts(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Fetch all currently active alerts from the monitoring system.

    Returns a JSON list of active alerts with severity, service, message.
    """
    scenario = ctx.context
    return json.dumps([asdict(a) for a in scenario.alerts], indent=2)
```

**How it works:**
1. The decorator inspects the function signature to extract parameter names and types
2. It generates a JSON schema from the type annotations
3. The function's docstring becomes the tool description (visible to the LLM)
4. When the LLM decides to call the tool, the SDK invokes the function with the appropriate arguments
5. The return value (must be `str`) is sent back to the LLM as the tool result

**Parameter conventions in this project:**
- `ctx: RunContextWrapper[ScenarioData]` — Always the first parameter, provides access to the shared context. This parameter is **not** exposed to the LLM; the SDK injects it automatically.
- Remaining parameters (e.g., `service: str = ""`, `limit: int = 50`) become the tool's input schema and are visible to the LLM
- Default values make parameters optional for the LLM

### `RunContextWrapper`

A typed wrapper around the context object passed to `Runner.run()`.

```python
from agents import RunContextWrapper

@function_tool
def query_logs(ctx: RunContextWrapper[ScenarioData], service: str = "") -> str:
    scenario = ctx.context  # Access the ScenarioData instance
    logs = scenario.logs
    ...
```

The generic type parameter `[ScenarioData]` provides type safety — `ctx.context` is typed as `ScenarioData`, giving IDE autocomplete and type checking.

### `ModelSettings`

Controls LLM generation parameters.

```python
from agents import ModelSettings

ModelSettings(temperature=0.2)  # Low temperature for deterministic tool calling
```

In this project, all agents use low temperatures (0.1-0.3) because:
- Tool calling requires precise, deterministic behavior
- We want consistent handoff decisions
- Creative variation is undesirable in incident response

### `Runner.run()`

The main execution function that drives the agent loop.

```python
from agents import Runner, RunConfig

result = await Runner.run(
    starting_agent=triage_agent,     # Which agent to start with
    input=incident_input,            # Initial user message (string)
    context=scenario_data,           # Shared context passed to all tools
    max_turns=40,                    # Maximum number of LLM calls + tool calls
    run_config=RunConfig(
        workflow_name="aiops_incident_response",
        tracing_disabled=True,
    ),
)

final_report = result.final_output  # The last agent's text output
```

**Execution loop:**
1. Send `input` to the `starting_agent`
2. The LLM responds with either:
   - **Tool calls** → Execute tools, send results back, loop
   - **Handoff** → Transfer to the target agent, continue the loop with that agent
   - **Text output** → If the current agent has no handoffs, this is the final output
3. Repeat until `max_turns` is reached or a final output is produced

**`RunConfig` parameters used:**
- `workflow_name` — Labels the execution for tracking purposes
- `tracing_disabled` — Disables OpenAI's tracing backend (we use OpenRouter, not OpenAI)

### `AsyncOpenAI`

The async HTTP client for communicating with LLM APIs.

```python
from agents import AsyncOpenAI

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="your_key",
)
```

This is the standard OpenAI Python client (`openai.AsyncOpenAI`), re-exported by the Agents SDK. By setting `base_url` to OpenRouter's endpoint, all API calls are routed through OpenRouter instead of OpenAI.

### `OpenAIChatCompletionsModel`

A model wrapper that uses the Chat Completions API (as opposed to the newer Responses API).

```python
from agents import OpenAIChatCompletionsModel

model = OpenAIChatCompletionsModel(
    model="openai/gpt-5-mini",      # Model identifier (OpenRouter format)
    openai_client=client,            # The AsyncOpenAI client to use
)
```

**Why Chat Completions instead of Responses API?**
OpenRouter implements the OpenAI-compatible **Chat Completions** endpoint (`/v1/chat/completions`), not the newer Responses API. The `OpenAIChatCompletionsModel` class tells the SDK to use the Chat Completions format for all requests, including tool calls.

### `set_tracing_disabled()`

Disables the SDK's built-in tracing system.

```python
from agents import set_tracing_disabled

set_tracing_disabled(True)
```

Tracing sends telemetry to OpenAI's backend. Since we're using OpenRouter, this is disabled to avoid unnecessary network calls and potential errors.

### `AgentHooks`

Abstract base class for lifecycle callbacks during agent execution.

```python
from agents import AgentHooks

class IncidentResponseHooks(AgentHooks):
    async def on_start(self, context, agent): ...
    async def on_end(self, context, agent, output): ...
    async def on_tool_start(self, context, agent, tool): ...
    async def on_tool_end(self, context, agent, tool, result): ...
    async def on_handoff(self, context, agent, source): ...
```

Hooks are called by the SDK at each lifecycle event. In this project, they print formatted output to the console for real-time observability.

### `InputGuardrail`

Validates input before an agent processes it.

```python
from agents import InputGuardrail, GuardrailFunctionOutput

async def validate_input(ctx, agent, input_data) -> GuardrailFunctionOutput:
    if not valid:
        return GuardrailFunctionOutput(
            output_info="Error message",
            tripwire_triggered=True,   # Stops execution
        )
    return GuardrailFunctionOutput(
        output_info="OK",
        tripwire_triggered=False,      # Allows execution to continue
    )

guardrail = InputGuardrail(
    guardrail_function=validate_input,
    name="my_guardrail",
)
```

When `tripwire_triggered=True`, the SDK raises a `GuardrailTripwireTriggered` exception, halting the pipeline.

### `OutputGuardrail`

Validates an agent's output before it's returned or passed to the next agent.

```python
from agents import OutputGuardrail, GuardrailFunctionOutput

async def validate_output(ctx, agent, output) -> GuardrailFunctionOutput:
    if "dangerous_pattern" in output.lower():
        return GuardrailFunctionOutput(
            output_info="Blocked",
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(output_info="Safe", tripwire_triggered=False)

guardrail = OutputGuardrail(
    guardrail_function=validate_output,
    name="safety_check",
)
```

The output guardrail runs after the agent produces its final text output but before it's returned to the caller.

### `GuardrailFunctionOutput`

The return type for guardrail functions.

```python
from agents import GuardrailFunctionOutput

GuardrailFunctionOutput(
    output_info="Description of what happened",  # Logged for debugging
    tripwire_triggered=False,                      # True = block, False = allow
)
```

---

## OpenRouter Integration

### Why OpenRouter?

OpenRouter provides a single API endpoint that routes to multiple LLM providers (OpenAI, Anthropic, Google, etc.). This allows:
- Using any model without changing the code
- Falling back to alternative models if one is unavailable
- Accessing free-tier models for development

### Configuration Chain

```
.env file
    ↓
load_dotenv() reads environment variables
    ↓
load_config() returns dict with api_key, base_url, model_name
    ↓
AsyncOpenAI(base_url=..., api_key=...) creates HTTP client
    ↓
OpenAIChatCompletionsModel(model=..., openai_client=...) wraps for SDK
    ↓
agent.model = model  (set on each agent)
```

### Model Naming Convention

OpenRouter uses the format `provider/model-name`:
- `openai/gpt-5-mini` — OpenAI's GPT-5 Mini via OpenRouter
- `anthropic/claude-sonnet-4` — Anthropic's Claude Sonnet via OpenRouter

---

## Tool Implementation Patterns

### Pattern: Context-Aware Tools

Every tool receives the shared `ScenarioData` via `RunContextWrapper`:

```python
@function_tool
def fetch_active_alerts(ctx: RunContextWrapper[ScenarioData]) -> str:
    scenario = ctx.context  # Access shared state
    ...
```

This avoids global state and makes tools testable in isolation.

### Pattern: Filter-and-Return

Most query tools follow a filter-and-return pattern:

```python
@function_tool
def query_logs(ctx: RunContextWrapper[ScenarioData], service: str = "", level: str = "", limit: int = 50) -> str:
    logs = ctx.context.logs
    if service:
        logs = [l for l in logs if l.service == service]
    if level:
        logs = [l for l in logs if l.level == level]
    logs = logs[:limit]
    return json.dumps([asdict(l) for l in logs], indent=2)
```

1. Start with the full dataset
2. Apply optional filters
3. Limit results
4. Serialize to JSON

### Pattern: Computed Analysis Tools

Some tools compute derived insights rather than just filtering:

```python
@function_tool
def detect_anomalies(ctx: RunContextWrapper[ScenarioData]) -> str:
    # Statistical analysis: split time series, compute z-scores
    ...
    return json.dumps(anomalies, indent=2)
```

```python
@function_tool
def correlate_signals(ctx: RunContextWrapper[ScenarioData]) -> str:
    # Cross-signal correlation across logs, alerts, traces, health
    ...
    return json.dumps(result, indent=2)
```

These tools do meaningful computation, not just data retrieval.

### Pattern: Simulated Action Tools

Remediation tools simulate actions without executing them:

```python
@function_tool
def propose_rollback(service: str, current_version: str = "", target_version: str = "", reason: str = "") -> str:
    return json.dumps({
        "action": "rollback",
        "command": f"kubectl rollout undo deployment/{service}",
        "risk_level": "medium",
        "requires_approval": True,
    }, indent=2)
```

These return the proposed command and metadata without executing anything. In a production system, these would integrate with actual infrastructure APIs.

### Tool Return Type

All tools return `str` (JSON-serialized). This is a requirement of the OpenAI Agents SDK — tool outputs must be strings that the LLM can process.

---

## Handoff Mechanics

### How Handoffs Work

When you pass an `Agent` object in the `handoffs` list:

```python
Agent(
    name="Triage Agent",
    handoffs=[log_analyzer, metrics_analyzer],
    ...
)
```

The SDK automatically:
1. Creates a transfer tool for each handoff target
2. Names it `transfer_to_{agent_name_snake_case}` (e.g., `transfer_to_log_analyzer_agent`)
3. Adds it to the agent's available tools
4. When the LLM calls this tool, the SDK transfers execution to the target agent

### Handoff Tool Names

The SDK generates tool names by converting the agent's `name` to snake_case and prepending `transfer_to_`:

| Agent Name | Generated Tool Name |
|------------|-------------------|
| Log Analyzer Agent | `transfer_to_log_analyzer_agent` |
| Metrics Analyzer Agent | `transfer_to_metrics_analyzer_agent` |
| Root Cause Analyzer Agent | `transfer_to_root_cause_analyzer_agent` |
| Remediation Agent | `transfer_to_remediation_agent` |
| Incident Reporter Agent | `transfer_to_incident_reporter_agent` |

### What Gets Transferred

On handoff, the SDK passes the **full conversation history** to the target agent. This includes:
- The original user input
- All tool calls and results from previous agents
- The transferring agent's reasoning and conclusions

This is how downstream agents "know" what happened upstream — they receive the entire conversation context.

### Instructing Handoffs

A key learning from this project: the LLM must be explicitly instructed to **call the transfer tool**, not just describe its intention. Compare:

**Bad** (agent describes but doesn't execute):
```
After your analysis, hand off to the Root Cause Analyzer.
```

**Good** (agent actually calls the tool):
```
IMPORTANT: After completing your analysis, you MUST use the transfer_to_root_cause_analyzer_agent tool to hand off your findings. Do NOT just describe your findings - call the transfer tool.
```

---

## Guardrail System

### Input Guardrails

Applied to the **Triage Agent** (pipeline entry point):

```python
# guardrails/input_validation.py
async def validate_incident_input(ctx, agent, input_data) -> GuardrailFunctionOutput:
    scenario = ctx.context
    has_alerts = len(scenario.alerts) > 0
    has_health = len(scenario.service_health) > 0
    has_logs = len(scenario.logs) > 0

    if not has_alerts and not has_health and not has_logs:
        return GuardrailFunctionOutput(
            output_info="No observability data available.",
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(output_info="OK", tripwire_triggered=False)
```

This runs **before** the agent processes any input. If the scenario data is empty (e.g., a bug in the simulator), the pipeline stops immediately with a clear error.

### Output Guardrails

Applied to the **Remediation Agent**:

```python
# guardrails/remediation_safety.py
DANGEROUS_PATTERNS = ["delete", "drop database", "rm -rf", "format", "destroy", "terminate all"]

async def validate_remediation_safety(ctx, agent, output) -> GuardrailFunctionOutput:
    output_lower = output.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in output_lower:
            return GuardrailFunctionOutput(
                output_info=f"Dangerous action detected: '{pattern}'",
                tripwire_triggered=True,
            )
    return GuardrailFunctionOutput(output_info="Safe", tripwire_triggered=False)
```

This runs **after** the Remediation Agent produces its output. If the output contains dangerous command patterns, the pipeline stops before the output is passed to the Incident Reporter.

---

## Context and State Management

### ScenarioData as Shared Context

The `ScenarioData` dataclass is the single source of truth for all observability data:

```python
result = await Runner.run(
    starting_agent=triage_agent,
    input=incident_input,
    context=scenario_data,   # <-- Passed here
    ...
)
```

Every tool receives this via `ctx.context`:

```python
@function_tool
def fetch_active_alerts(ctx: RunContextWrapper[ScenarioData]) -> str:
    scenario = ctx.context  # Same ScenarioData instance
```

**Benefits:**
- No global variables
- Type-safe access to all data
- Tools are pure functions of their inputs + context
- Easy to test by constructing a `ScenarioData` with known values

### No Mutable State

The `ScenarioData` and all its contained dataclasses are either frozen or effectively read-only. Tools never modify the context — they only read from it and return results as strings.

---

## Runner and Execution Model

### Turn-Based Execution

The SDK's `Runner.run()` operates on a **turn-based** model:

```
Turn 1: LLM receives input → decides to call fetch_active_alerts
Turn 2: Tool result returned → LLM decides to call get_service_health_summary
Turn 3: Tool result returned → LLM decides to call transfer_to_log_analyzer_agent
Turn 4: (Now Log Analyzer Agent) → LLM decides to call search_error_patterns + get_log_statistics
Turn 5: Tool results returned → LLM decides to call query_logs
...
```

Each "turn" is one LLM inference call. `max_turns=40` means at most 40 LLM calls across all agents in the pipeline.

### Parallel Tool Calls

The SDK supports parallel tool calls — the LLM can request multiple tools in a single turn:

```
Turn N: LLM requests [search_error_patterns, get_log_statistics]  # Both called in parallel
Turn N+1: Both results returned at once
```

This is visible in the E2E output:
```
[Log Analyzer Agent] calling tool: search_error_patterns
[Log Analyzer Agent] calling tool: get_log_statistics
[Log Analyzer Agent] tool search_error_patterns completed.
[Log Analyzer Agent] tool get_log_statistics completed.
```

### Async Execution

The entire pipeline is async (`async/await`). The entry point uses `asyncio.run()`:

```python
asyncio.run(main())
```

Tools are synchronous functions (the SDK handles wrapping them), but the overall execution is async to support non-blocking HTTP calls to the LLM API.

---

## Hooks and Observability

### IncidentResponseHooks

The custom hooks class provides formatted console output:

```python
class IncidentResponseHooks(AgentHooks):
    async def on_start(self, context, agent):
        # Prints agent name header when an agent begins
        print(f"\n{'='*60}")
        print(f"  AGENT: {agent.name}")

    async def on_tool_start(self, context, agent, tool):
        # Prints when a tool is invoked
        print(f"  [{agent.name}] calling tool: {tool.name}")

    async def on_tool_end(self, context, agent, tool, result):
        # Prints when a tool completes
        print(f"  [{agent.name}] tool {tool.name} completed.")

    async def on_handoff(self, context, agent, source):
        # Prints the handoff transition
        print(f"\n  >> Handoff: {source.name} -> {agent.name}")

    async def on_end(self, context, agent, output):
        # Prints when an agent finishes
        print(f"\n  [{agent.name}] completed.")
```

Hooks are passed to each agent at construction time and are called by the SDK automatically.

### Logging Strategy

Following the project's coding guidelines:

1. **Module-level loggers**: `logger = logging.getLogger(__name__)`
2. **No f-strings in log calls**: `logger.info("Queried %d logs", count)` (delegates formatting to the logger)
3. **Structured information**: Log messages include counts, service names, and filter parameters
4. **Appropriate levels**: INFO for normal operations, WARNING for validation failures

---

## Model Configuration

### Temperature Settings

Each agent has a carefully chosen temperature:

| Agent | Temperature | Rationale |
|-------|-------------|-----------|
| Triage | 0.2 | Needs consistent classification and routing |
| Log Analyzer | 0.1 | Must follow a precise analytical workflow |
| Metrics Analyzer | 0.1 | Statistical analysis requires precision |
| Root Cause Analyzer | 0.1 | Evidence-based reasoning must be deterministic |
| Remediation | 0.2 | Slight flexibility for creative fix proposals |
| Incident Reporter | 0.3 | Most creative agent — writes human-readable reports |

### Why Low Temperatures?

Tool-calling agents need low temperatures because:
- Tool names and parameters must be exact
- Handoff decisions must be reliable
- Analytical reasoning should be consistent across runs
- Higher temperatures cause the model to "describe" actions instead of executing them

---

## Key Implementation Lessons

### 1. Explicit Handoff Instructions

The most critical lesson: agent instructions must **explicitly command** the use of transfer tools. Without explicit instructions like "you MUST use the `transfer_to_X` tool", the LLM tends to describe its intention to hand off rather than actually calling the tool.

### 2. Chat Completions vs. Responses API

When using OpenRouter (or any OpenAI-compatible provider), you must use `OpenAIChatCompletionsModel` instead of the default model class. The default uses the Responses API, which is only available on OpenAI's own servers.

### 3. Context Over Global State

Passing `ScenarioData` as the `context` parameter to `Runner.run()` and accessing it via `RunContextWrapper` is cleaner than global variables. It makes tools testable and the data flow explicit.

### 4. Reverse Construction Order

Agents must be constructed in reverse order (terminal first) because each agent needs a reference to its handoff targets at construction time:

```python
reporter    = create_incident_reporter_agent()          # No handoffs
remediation = create_remediation_agent(reporter)         # Needs reporter
rca         = create_rca_agent(remediation)              # Needs remediation
log_analyzer = create_log_analyzer_agent(rca)            # Needs rca
metrics_analyzer = create_metrics_analyzer_agent(rca)    # Needs rca
triage      = create_triage_agent(log_analyzer, metrics_analyzer)  # Needs both
```

### 5. JSON as the Universal Tool Output

All tools return JSON strings. This is both an SDK requirement and a good practice — it gives the LLM structured data to reason about, rather than free-form text that might be ambiguous.
