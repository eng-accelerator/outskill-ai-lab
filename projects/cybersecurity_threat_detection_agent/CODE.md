# Code Guide

This document covers the AI agent concepts, OpenAI Agents SDK constructs, and implementation details needed to fully understand the Cybersecurity Threat Detection Agent codebase.

---

## AI Agent Concepts

### What Is an Agent?

An agent is an LLM equipped with:
- **Instructions** -- a system prompt defining its role, workflow, and constraints
- **Tools** -- functions it can call to interact with external systems
- **Handoffs** -- other agents it can transfer control to
- **Guardrails** -- input/output validators that can halt execution

The LLM decides which tools to call, in what order, and when to hand off. The SDK manages the execution loop.

### Multi-Agent Pipeline

This system uses a **prompt chaining** pattern with **routing**:

```
Alert Intake → [Auth Analyzer | Network Analyzer] → Threat Intel → Containment → SOC Report
```

Each agent is a specialist. The Alert Intake agent routes to the appropriate analyzer based on threat category. Both analyzers converge on the Threat Intel agent, which enriches findings before passing to Containment and finally SOC Report.

### Handoffs vs. Function Calls

- **Function calls (tools)**: The agent calls a Python function, gets a result, and continues reasoning
- **Handoffs**: The agent transfers control to another agent entirely. The target agent takes over the conversation with full context. The source agent does not resume.

Handoffs are implemented as auto-generated tools by the SDK. When an agent has `handoffs=[other_agent]`, the SDK creates a tool named `transfer_to_{agent_name}` that the LLM can invoke.

---

## OpenAI Agents SDK Constructs Used

### `Agent`

The core construct. Each of our 6 agents is created via:

```python
Agent(
    name="Auth Analyzer Agent",
    instructions=AUTH_ANALYZER_INSTRUCTIONS,
    tools=[query_auth_logs, detect_anomalous_logins, check_privilege_changes],
    handoffs=[threat_intel_agent],
    hooks=hooks,
    model_settings=ModelSettings(temperature=0.2),
)
```

Parameters:
- `name` -- Unique agent name (used in handoff tool names)
- `instructions` -- System prompt string
- `tools` -- List of `@function_tool` decorated functions
- `handoffs` -- List of Agent objects this agent can transfer to
- `input_guardrails` -- List of InputGuardrail objects (checked before processing)
- `output_guardrails` -- List of OutputGuardrail objects (checked after output)
- `hooks` -- AgentHooks instance for lifecycle callbacks
- `model_settings` -- ModelSettings for temperature, top_p, etc.
- `model` -- Set after construction to the OpenRouter model

### `@function_tool`

Decorator that converts a Python function into an agent-callable tool:

```python
@function_tool
def query_auth_logs(
    ctx: RunContextWrapper[ScenarioData],
    user: str = "",
    source_ip: str = "",
    action: str = "",
    limit: int = 50,
) -> str:
    """Query authentication logs, optionally filtered by user, source IP, or action.
    ...
    """
```

The SDK extracts the function signature and docstring to generate a JSON schema that the LLM uses to decide when and how to call the tool. Default values become optional parameters.

### `RunContextWrapper[T]`

Generic wrapper that carries shared state through the pipeline. Our `T` is `ScenarioData`:

```python
ctx: RunContextWrapper[ScenarioData]
scenario = ctx.context  # Access the ScenarioData instance
```

Every tool receives the same context, allowing all agents to access the simulated security data.

### `ModelSettings`

Controls LLM generation parameters:

```python
ModelSettings(temperature=0.2)  # Low temperature for deterministic analysis
ModelSettings(temperature=0.3)  # Slightly higher for report generation
```

We use low temperatures (0.2) for analysis agents to ensure consistent, factual output, and slightly higher (0.3) for the SOC Report agent to allow more natural report writing.

### `Runner.run()`

The main execution entry point:

```python
result = await Runner.run(
    starting_agent=alert_intake_agent,
    input=threat_input,
    context=scenario_data,
    max_turns=40,
    run_config=run_config,
)
```

Parameters:
- `starting_agent` -- The first agent in the pipeline
- `input` -- Initial message string
- `context` -- Shared context object (becomes `RunContextWrapper.context`)
- `max_turns` -- Maximum number of LLM calls across all agents (prevents infinite loops)
- `run_config` -- RunConfig with workflow metadata

The SDK manages the full agent loop: LLM call -> tool execution -> handoff -> next agent -> ... -> final output.

### `AsyncOpenAI`

OpenAI's async HTTP client, configured to point at OpenRouter:

```python
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openrouter_api_key,
)
```

### `OpenAIChatCompletionsModel`

Wraps the AsyncOpenAI client into a model object the SDK can use:

```python
model = OpenAIChatCompletionsModel(
    model="openai/gpt-5-mini",
    openai_client=client,
)
```

This is critical for OpenRouter integration. Without explicitly using this class, the SDK defaults to OpenAI's Responses API, which OpenRouter does not support.

### `set_tracing_disabled(True)`

Disables the SDK's built-in tracing since we're using OpenRouter, not OpenAI's tracing backend.

### `AgentHooks`

Lifecycle callbacks for observability:

```python
class ThreatDetectionHooks(AgentHooks):
    async def on_start(self, context, agent): ...
    async def on_end(self, context, agent, output): ...
    async def on_tool_start(self, context, agent, tool): ...
    async def on_tool_end(self, context, agent, tool, result): ...
    async def on_handoff(self, context, agent, source): ...
```

These hooks are called at each stage of the agent lifecycle, providing real-time visibility into the pipeline execution.

### `InputGuardrail` and `OutputGuardrail`

Validation functions that can halt the pipeline:

```python
async def validate_security_input(
    ctx: RunContextWrapper[ScenarioData],
    agent: Agent,
    input_data: str | list,
) -> GuardrailFunctionOutput:
    ...
    return GuardrailFunctionOutput(
        output_info="...",
        tripwire_triggered=True,  # True = halt execution
    )

security_input_guardrail = InputGuardrail(
    guardrail_function=validate_security_input,
    name="security_input_validation",
)
```

- **Input guardrails** run before the agent processes input (e.g., validate security data exists)
- **Output guardrails** run after the agent produces output (e.g., validate containment actions are safe)

### `GuardrailFunctionOutput`

Return type for guardrail functions:
- `output_info` -- Human-readable message about the validation result
- `tripwire_triggered` -- `True` to halt execution, `False` to continue

### `RunConfig`

Workflow-level configuration:

```python
run_config = RunConfig(
    workflow_name="cybersecurity_threat_detection",
    tracing_disabled=True,
)
```

---

## OpenRouter Integration

OpenRouter serves as a drop-in replacement for the OpenAI API. The key integration points:

1. **AsyncOpenAI client** with `base_url` pointing to OpenRouter
2. **OpenAIChatCompletionsModel** wrapping the client (forces Chat Completions API, not Responses API)
3. **`set_tracing_disabled(True)`** since OpenRouter doesn't support OpenAI tracing
4. **Model name format**: `provider/model` (e.g., `openai/gpt-5-mini`, `anthropic/claude-sonnet-4`)

The model is set on all agents after construction:

```python
for agent in [alert_intake, auth_analyzer, ...]:
    agent.model = model
```

---

## Tool Implementation Patterns

### Context-Aware Tools

All tools receive `RunContextWrapper[ScenarioData]` to access simulated data:

```python
@function_tool
def fetch_security_alerts(ctx: RunContextWrapper[ScenarioData]) -> str:
    scenario = ctx.context
    alerts_data = [asdict(a) for a in scenario.alerts]
    return json.dumps(alerts_data, indent=2)
```

### Filter-and-Return Tools

Tools that query data with optional filters:

```python
@function_tool
def query_auth_logs(ctx, user="", source_ip="", action="", limit=50) -> str:
    logs = ctx.context.auth_logs
    if user:
        logs = [e for e in logs if e.user == user]
    if source_ip:
        logs = [e for e in logs if e.source_ip == source_ip]
    ...
```

### Computed Analysis Tools

Tools that perform statistical analysis on the data:

```python
@function_tool
def detect_anomalous_logins(ctx) -> str:
    # Groups by user, detects brute force patterns, impossible travel,
    # malicious IP logins. Returns structured JSON anomaly list.
```

```python
@function_tool
def detect_c2_patterns(ctx) -> str:
    # Groups network logs by destination, detects known C2 IPs,
    # periodic beaconing, port scanning. Returns findings.
```

### Simulated Action Tools

Tools that propose actions rather than executing them:

```python
@function_tool
def propose_ip_block(ctx, ip_address, reason, duration_hours=24) -> str:
    is_internal = ip_address.startswith("10.")
    risk_level = "high" if is_internal else "low"
    return json.dumps({
        "action_type": "block_ip",
        "target": ip_address,
        "risk_level": risk_level,
        "requires_approval": is_internal,
        "command": f"firewall-cmd --add-rich-rule=...",
        "warnings": [...],
    })
```

### Lookup Tools

Tools that query simulated databases:

```python
@function_tool
def lookup_ioc(ctx, indicator) -> str:
    if indicator in IOC_DATABASE:
        return json.dumps({"match": True, ...})
    return json.dumps({"match": False, ...})
```

---

## Handoff Mechanics

When an agent has `handoffs=[other_agent]`, the SDK auto-generates a transfer tool:

- Agent named `"Auth Analyzer Agent"` gets tool `transfer_to_auth_analyzer_agent`
- Agent named `"Network API Analyzer Agent"` gets tool `transfer_to_network_api_analyzer_agent`

The tool name is derived by lowercasing the agent name and replacing spaces with underscores, prefixed with `transfer_to_`.

When the LLM calls this tool, the SDK:
1. Ends the current agent's turn
2. Passes the full conversation history to the target agent
3. The target agent begins processing with all prior context

---

## Guardrail System

### Input Guardrail (Alert Intake Agent)

Validates that the scenario contains actionable security data:

```python
has_alerts = len(scenario.alerts) > 0
has_auth = len(scenario.auth_logs) > 0
has_network = len(scenario.network_logs) > 0

if not has_alerts and not has_auth and not has_network:
    return GuardrailFunctionOutput(tripwire_triggered=True)
```

### Output Guardrail (Containment Agent)

Validates that containment proposals are safe:

```python
DANGEROUS_PATTERNS = ["disable all", "block 0.0.0.0/0", "isolate all", ...]
SOC_TEAM_ACCOUNTS = {"soc-admin", "soc-analyst", "soc-lead", "svc-monitor"}

# Check for mass-action patterns
for pattern in DANGEROUS_PATTERNS:
    if pattern in output_lower:
        return GuardrailFunctionOutput(tripwire_triggered=True)

# Check for SOC team lockout
for account in SOC_TEAM_ACCOUNTS:
    if account in output_lower and "disable" in output_lower:
        return GuardrailFunctionOutput(tripwire_triggered=True)
```

---

## Context and State Management

### ScenarioData

The shared context object carries all simulated security data:

```python
@dataclass
class ScenarioData:
    scenario_type: ScenarioType
    description: str
    base_time: datetime
    alerts: list[SecurityAlert]
    assets: list[AssetInfo]
    auth_logs: list[AuthLogEntry]
    network_logs: list[NetworkLogEntry]
    api_access_logs: list[APIAccessEntry]
    endpoint_events: list[EndpointEvent]
    cloud_audit_logs: list[CloudAuditEntry]
```

This is passed as `context=scenario_data` to `Runner.run()` and becomes available to all tools via `ctx.context`.

### No Mutable State

All data models are frozen dataclasses. The ScenarioData is generated once and read-only throughout the pipeline. Agents communicate findings through the conversation history (LLM messages), not by mutating shared state.

---

## Turn-Based Execution Model

The SDK's `Runner.run()` manages a turn-based loop:

1. Send messages to LLM
2. LLM responds with either:
   - **Tool calls** -> SDK executes tools, appends results, loops back to step 1
   - **Handoff** -> SDK switches to target agent, loops back to step 1
   - **Text response** -> If this is the terminal agent, return as final output
3. Repeat until final output or `max_turns` exceeded

With `max_turns=40`, the pipeline can execute approximately 6-8 tool calls per agent across 6 agents.

---

## Threat Intelligence Architecture

### IOC Database

Simulated database with 10 malicious IPs and 3 malware hashes:

```python
IOC_DATABASE = {
    "185.220.101.34": {"type": "ip", "threat": "Tor Exit Node / Brute Force Botnet", "confidence": 0.95, ...},
    "a1b2c3d4...": {"type": "hash", "threat": "Cobalt Strike Beacon", "confidence": 0.99, ...},
    ...
}
```

### MITRE ATT&CK Mapping

10 threat categories mapped to 20+ techniques:

```python
MITRE_MAPPINGS = {
    "brute_force": [
        {"tactic_id": "TA0006", "technique_id": "T1110", "technique_name": "Brute Force", ...},
        {"tactic_id": "TA0001", "technique_id": "T1078", "technique_name": "Valid Accounts", ...},
    ],
    "malware": [
        {"tactic_id": "TA0002", "technique_id": "T1204.002", "technique_name": "Malicious File", ...},
        ...
    ],
    ...
}
```

### Reputation Scoring

IP reputation scores from 0 (most malicious) to 100 (benign):

```python
REPUTATION_DATABASE = {
    "185.220.101.34": {"score": 5, "category": "malicious", "reports": 1247, "country": "RU", ...},
    ...
}
```

---

## Scenario Design Philosophy

Each scenario is designed to exercise specific detection capabilities:

| Scenario | Primary Detection | Secondary Detection | Key Indicators |
|----------|------------------|-------------------|----------------|
| `brute_force_attack` | Auth anomaly detection | Lateral movement via auth | 30 failed logins, malicious IPs, geographic anomaly |
| `insider_threat` | Privilege escalation | Data exfiltration via API/cloud | Self-role-change, admin endpoint access, bulk data export |
| `api_key_compromise` | API abuse detection | Foreign IP usage | Foreign IP on prod key, mass data extraction, key rotation attempt |
| `malware_lateral_movement` | Malware/C2 detection | Endpoint forensics | Known malware hashes, C2 beaconing, PsExec, Mimikatz |
| `cloud_misconfiguration` | Cloud audit anomaly | External data access | S3 public policy, security group 0.0.0.0/0, anonymous access |

---

## Key Implementation Lessons

1. **Explicit handoff instructions are critical** -- LLMs will describe handoffs instead of executing them unless instructions explicitly say "CALL the transfer tool"

2. **OpenAIChatCompletionsModel is required for OpenRouter** -- The default SDK path uses OpenAI's Responses API which OpenRouter doesn't support

3. **Tool docstrings are the API contract** -- The LLM reads the docstring to understand when and how to use each tool. Clear, specific docstrings lead to correct tool usage.

4. **Low temperature for analysis, slightly higher for reporting** -- Analysis agents need deterministic reasoning (0.2), while the report agent benefits from slightly more creative writing (0.3)

5. **Simulated databases enable self-contained testing** -- The IOC, MITRE, and reputation databases are in-memory, making the system fully testable without external API dependencies
