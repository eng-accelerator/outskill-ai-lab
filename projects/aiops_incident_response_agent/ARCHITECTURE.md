# Architecture

This document describes the system design, agentic design patterns, data flow, and architectural decisions behind the AI Ops Incident Response Agent.

---

## System Overview

The system is a **multi-agent pipeline** that processes simulated incident scenarios through six specialized AI agents. Each agent has a distinct responsibility, its own set of tools, and explicit handoff points to the next agent in the chain.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Incident Alert Input                          │
└──────────────────────┬───────────────────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Triage Agent  │ ◄── Input Guardrail (validates scenario data)
              │                │
              │  Tools:        │
              │  • fetch_active_alerts
              │  • get_service_health_summary
              └───────┬────────┘
                      │
            ┌─────────┴─────────┐
            │ Routing Decision  │
            └────┬─────────┬────┘
                 │         │
                 ▼         ▼
    ┌──────────────┐  ┌──────────────────┐
    │ Log Analyzer │  │ Metrics Analyzer │
    │    Agent     │  │     Agent        │
    │              │  │                  │
    │ Tools:       │  │ Tools:           │
    │ • query_logs │  │ • query_metrics  │
    │ • search_    │  │ • detect_        │
    │   error_     │  │   anomalies      │
    │   patterns   │  │ • get_service_   │
    │ • get_log_   │  │   dependencies   │
    │   statistics │  │                  │
    └──────┬───────┘  └────────┬─────────┘
           │                   │
           └─────────┬─────────┘
                     ▼
         ┌───────────────────────┐
         │  Root Cause Analyzer  │
         │       Agent           │
         │                       │
         │  Tools:               │
         │  • correlate_signals  │
         │  • query_traces       │
         │  • get_recent_        │
         │    deployments        │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Remediation Agent    │ ──► Output Guardrail (blocks dangerous actions)
         │                       │
         │  Tools:               │
         │  • lookup_runbook     │
         │  • propose_rollback   │
         │  • propose_scaling_   │
         │    action             │
         │  • propose_config_    │
         │    change             │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Incident Reporter    │
         │       Agent           │
         │                       │
         │  Tools:               │
         │  • generate_timeline  │
         │  • format_incident_   │
         │    report             │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Final Incident      │
         │      Report           │
         └───────────────────────┘
```

---

## Agentic Design Patterns Applied

The system applies 12 of the 21 agentic design patterns defined in `.cursor/rules/agentic_design_patterns.mdc`. Below is how each pattern maps to the implementation.

### Pattern #2: Default Agent Loop

Every agent in the pipeline follows the conceptual loop:

1. **Goal intake** — Defined in agent `instructions` (e.g., "Triage this incident and classify severity")
2. **Context gathering** — Tool calls to fetch observability data (alerts, logs, metrics, traces)
3. **Planning** — LLM reasoning about which tools to call and in what order
4. **Action execution** — Tool invocations and handoff decisions
5. **Reflection** — The LLM evaluates tool results before deciding next steps

The loop is driven by the SDK's `Runner.run()`, which iterates until the agent produces a final output or hands off.

### Pattern #3: Prompt Chaining

The six-agent pipeline is a prompt chain where each agent's output feeds the next:

```
Triage findings → Log/Metrics analysis → RCA determination → Remediation plan → Incident report
```

Each agent has a single responsibility, and context flows forward through the handoff mechanism. The chain is 5 steps deep (within the recommended 3-5 range).

### Pattern #4: Routing

The **Triage Agent** implements routing:
- If the incident involves error patterns or application-level issues → routes to **Log Analyzer Agent**
- If the incident involves resource metrics (CPU, memory, latency) → routes to **Metrics Analyzer Agent**

This routing decision is:
- **Explicit** — encoded in the agent's instructions
- **Inspectable** — logged via `AgentHooks.on_handoff()`
- **LLM-driven** — the model decides based on alert content and service health data

### Pattern #7: Tool Use

All 14 tools follow strict conventions:
- **Clear descriptions** — Each `@function_tool` has a detailed docstring explaining what it does, its parameters, and return format
- **Strict input/output schema** — Parameters are typed Python arguments; outputs are JSON strings
- **Validated outputs** — Tools return structured JSON that the LLM can parse deterministically
- **Recoverable failures** — Tools return error messages as JSON rather than raising exceptions

### Pattern #8: Planning

Each agent's `instructions` define an explicit workflow (numbered steps). For example, the Triage Agent's plan:
1. Fetch active alerts
2. Get service health summary
3. Analyze and classify
4. Hand off to the appropriate specialist

The LLM follows this plan, calling tools in the prescribed order.

### Pattern #9: Multi-Agent

Six agents with clearly separated roles:

| Agent | Single Responsibility |
|-------|----------------------|
| Triage | Classification and routing |
| Log Analyzer | Log pattern analysis |
| Metrics Analyzer | Metric anomaly detection |
| Root Cause Analyzer | Cross-signal correlation |
| Remediation | Fix proposal |
| Incident Reporter | Report generation |

There are no circular dependencies — the pipeline flows strictly forward. Communication contracts are defined by the handoff mechanism (conversation history is passed forward).

### Pattern #13: Exception Handling

- **Tool failures** return error JSON rather than raising exceptions
- **Guardrails** catch invalid inputs and unsafe outputs before they propagate
- **`max_turns=40`** in `Runner.run()` prevents infinite loops
- **Assertions** validate configuration at startup (e.g., API key must be set)

### Pattern #14: Human-in-the-Loop

The Remediation Agent implements human-in-the-loop by:
- Flagging high-risk actions with `requires_approval: true`
- Never auto-executing destructive actions
- Proposing actions with explicit risk levels and rollback plans

### Pattern #16: Inter-Agent Communication

Agent-to-agent communication uses the SDK's **handoff** mechanism:
- Messages are structured (the full conversation history is passed)
- Handoffs are logged via `AgentHooks.on_handoff()`
- Each handoff is a transfer tool call (e.g., `transfer_to_log_analyzer_agent`)

### Pattern #19: Guardrails & Safety

Two guardrails are implemented:

1. **Input Guardrail** (`incident_input_guardrail`):
   - Validates that the scenario has loaded observability data
   - Triggers `tripwire` if no alerts, health data, or logs are available
   - Prevents the pipeline from running on empty data

2. **Output Guardrail** (`remediation_output_guardrail`):
   - Scans remediation output for dangerous patterns (`delete`, `drop database`, `rm -rf`, etc.)
   - Triggers `tripwire` to block unsafe remediation proposals
   - Applied as an `output_guardrail` on the Remediation Agent

### Pattern #20: Evaluation & Monitoring

- **Structured logging** throughout all components (`logging.getLogger(__name__)`)
- **AgentHooks** provide lifecycle callbacks for every agent start, tool call, tool completion, handoff, and agent completion
- **Real-time console output** shows the pipeline progression
- **`RunConfig`** with `workflow_name` enables workflow-level tracking

### Pattern #17: Resource-Aware Optimization

- Uses `gpt-5-mini` (a smaller, faster model) rather than full-size models
- `temperature` is set low (0.1-0.3) per agent for deterministic tool calling
- Tracing is disabled (`set_tracing_disabled(True)`) since we're not using OpenAI's tracing backend

---

## Data Architecture

### Data Models

The system uses **frozen dataclasses** (immutable value types) following the algebraic type system approach:

```
models/
├── incident.py      # Input/triage types
│   ├── Severity     = Literal["P0", "P1", "P2", "P3"]
│   ├── IncidentCategory = Literal["memory_leak", "deployment_regression", ...]
│   ├── Alert        = @dataclass(frozen=True)
│   ├── ServiceHealth = @dataclass(frozen=True)
│   └── TriageResult = @dataclass(frozen=True)
│
├── analysis.py      # Analysis types
│   ├── LogEntry     = @dataclass(frozen=True)
│   ├── ErrorPattern = @dataclass(frozen=True)
│   ├── MetricDataPoint = @dataclass(frozen=True)
│   ├── AnomalyDetection = @dataclass(frozen=True)
│   ├── TraceSpan    = @dataclass(frozen=True)
│   ├── Deployment   = @dataclass(frozen=True)
│   ├── LogAnalysisResult = @dataclass(frozen=True)
│   ├── MetricsAnalysisResult = @dataclass(frozen=True)
│   └── RCAResult    = @dataclass(frozen=True)
│
└── remediation.py   # Output types
    ├── RiskLevel    = Literal["low", "medium", "high", "critical"]
    ├── ActionType   = Literal["rollback", "scale_up", ...]
    ├── RemediationAction = @dataclass(frozen=True)
    └── RemediationPlan = @dataclass(frozen=True)
```

**Design decisions:**
- **Frozen dataclasses** over Pydantic models — aligns with the "functional core; imperative shell" principle. Data is immutable once created.
- **Literal types** over enums — follows the coding guideline "prefer Python Literals over String Enumerations"
- **Products as dataclasses, sums as `|`** — follows the algebraic type system guideline

### Context Passing

The `ScenarioData` dataclass serves as the **shared context** for all agents:

```python
@dataclass
class ScenarioData:
    scenario_type: ScenarioType
    description: str
    base_time: datetime
    logs: list[LogEntry]
    metrics: list[MetricDataPoint]
    alerts: list[Alert]
    service_health: list[ServiceHealth]
    traces: list[TraceSpan]
    deployments: list[Deployment]
```

This is passed as the `context` parameter to `Runner.run()`, and every tool receives it via `RunContextWrapper[ScenarioData]`. This means:
- All tools can access the full observability dataset
- No global state is needed
- The context is typed and inspectable

---

## Simulation Architecture

### Scenario Engine

The `ScenarioEngine` (`simulators/scenario_engine.py`) is the orchestrator that coordinates four specialized simulators:

```
ScenarioEngine.generate_scenario("deployment_regression")
    │
    ├── log_simulator.generate_deployment_regression_logs(base_time)
    ├── metrics_simulator.generate_deployment_regression_metrics(base_time)
    ├── alert_simulator.generate_deployment_regression_alerts(base_time)
    └── trace_simulator.generate_deployment_regression_traces(base_time)
                         .generate_deployment_regression_deployments(base_time)
```

All simulators share the same `base_time` to ensure temporal correlation across data types.

### Simulator Design

Each simulator follows a consistent pattern:

1. **Generate baseline data** for all 8 services (normal operating conditions)
2. **Inject anomalies** on the target service(s) at the appropriate time offset
3. **Simulate cascading effects** on dependent services
4. **Sort by timestamp** for realistic time ordering

The 8 simulated microservices form a dependency graph:

```
api-gateway ──► user-service ──► database-proxy
            ──► order-service ──► database-proxy
            │                 ──► payment-service ──► database-proxy
            │                 ──► inventory-service ──► database-proxy
            ──► payment-service                     ──► cache-service
            ──► inventory-service ──► cache-service
notification-service ──► user-service
```

### Anomaly Detection Algorithm

The `detect_anomalies` tool in `metrics_tools.py` uses a statistical approach:

1. Split each metric's time series into two halves (baseline vs. recent)
2. Compute mean and standard deviation of the baseline half
3. Calculate the z-score of the recent half's mean against the baseline
4. Flag anomalies where z-score > 2.0 (significant deviation)
5. Classify as `spike` or `drop` based on direction
6. Compute confidence as `min(z_score / 5.0, 1.0)`

This is a simple but effective method for the simulated data, where anomalies are deliberately injected with clear signal.

---

## Pipeline Execution Flow

### 1. Initialization

```python
# main.py
model = create_openrouter_model()      # OpenRouter via AsyncOpenAI client
hooks = IncidentResponseHooks()         # Lifecycle logging hooks
scenario_data = generate_scenario(...)  # Simulated observability data
triage_agent = build_agent_pipeline(model, hooks)  # Build agent chain
```

### 2. Agent Pipeline Construction

Agents are built in **reverse order** (terminal agent first) to wire handoffs:

```python
reporter    = create_incident_reporter_agent(hooks)     # Terminal: no handoffs
remediation = create_remediation_agent(reporter, hooks)  # Hands off to reporter
rca         = create_rca_agent(remediation, hooks)       # Hands off to remediation
log_analyzer = create_log_analyzer_agent(rca, hooks)     # Hands off to RCA
metrics_analyzer = create_metrics_analyzer_agent(rca, hooks)  # Hands off to RCA
triage      = create_triage_agent(log_analyzer, metrics_analyzer, hooks)  # Entry point
```

Then the model is set on all agents:

```python
for agent in [triage, log_analyzer, metrics_analyzer, rca, remediation, reporter]:
    agent.model = model
```

### 3. Execution

```python
result = await Runner.run(
    starting_agent=triage_agent,
    input=incident_input,       # Alert summary string
    context=scenario_data,      # ScenarioData passed to all tools
    max_turns=40,               # Safety limit on agent loop iterations
    run_config=RunConfig(
        workflow_name="aiops_incident_response",
        tracing_disabled=True,
    ),
)
```

The SDK's `Runner.run()` drives the execution:
1. Sends the input to the Triage Agent
2. The agent calls tools, reasons about results, and decides to hand off
3. On handoff, the SDK transfers control (and conversation history) to the target agent
4. This continues until the Incident Reporter Agent produces a final text output (no handoffs)

### 4. Output

The final output is the Incident Reporter Agent's formatted incident report, returned as `result.final_output`.

---

## Configuration Architecture

Configuration follows a simple, explicit approach:

```python
# utils/config.py
def load_config() -> dict[str, str | None]:
    load_dotenv()
    return {
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
        "openrouter_base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        "model_name": os.getenv("OPENROUTER_MODEL", "openai/gpt-5-mini"),
    }
```

The OpenRouter client is created using the SDK's `AsyncOpenAI` with a custom `base_url`:

```python
client = AsyncOpenAI(base_url=base_url, api_key=api_key)
model = OpenAIChatCompletionsModel(model=model_name, openai_client=client)
```

This uses the **Chat Completions API** path (not the Responses API) because OpenRouter implements the OpenAI-compatible chat completions endpoint.

---

## Error Handling Strategy

Following the project's coding guidelines ("errors-as-types over try-except"), the system avoids nested exception handling:

1. **Assertions for invariants** — `assert api_key` at startup, `assert scenario_type in generators`
2. **Error returns from tools** — Tools return `{"error": "..."}` JSON instead of raising
3. **Guardrail tripwires** — Invalid inputs and unsafe outputs are caught by guardrails, not exceptions
4. **SDK-level safety** — `max_turns=40` prevents runaway agent loops

---

## Observability Architecture

### Logging

Every module creates a named logger:

```python
logger = logging.getLogger(__name__)
```

Log messages use **structured formatting** (not f-strings) per the coding guidelines:

```python
logger.info("Queried %d logs (service=%s, level=%s)", len(logs), service, level)
```

### AgentHooks

The `IncidentResponseHooks` class provides real-time visibility:

| Hook | Fires When | Output |
|------|-----------|--------|
| `on_start` | Agent begins processing | Agent name header |
| `on_end` | Agent finishes | Completion message |
| `on_tool_start` | Tool is invoked | Tool name |
| `on_tool_end` | Tool returns | Tool completion |
| `on_handoff` | Agent transfers to another | Source → Target |
