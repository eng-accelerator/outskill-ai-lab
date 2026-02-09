# AI Ops Incident Response Agent

A production-grade, multi-agent incident response system built with the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) and [OpenRouter](https://openrouter.ai/) as the LLM provider. The system autonomously detects anomalies, performs root-cause analysis, correlates signals across observability data, and proposes remediation actions — all orchestrated through a pipeline of 6 specialized AI agents.

---

## Setup

### Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** package manager
- An **OpenRouter API key** (free tier available at [openrouter.ai](https://openrouter.ai/))

### Installation

1. **Clone the repository** and navigate to the workspace root:

```bash
cd outskill-ai-lab
```

2. **Install dependencies** using `uv`:

```bash
uv sync
```

This installs all dependencies from `pyproject.toml`, including:
- `openai-agents>=0.6.5` — OpenAI Agents SDK
- `python-dotenv` — Environment variable management

3. **Configure your API key** by creating a `.env` file in the workspace root:

```bash
# .env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1   # optional, this is the default
OPENROUTER_MODEL=openai/gpt-5-mini                  # optional, this is the default
```

### Running the Agent

**Interactive mode** — select a scenario from the menu:

```bash
PYTHONPATH=projects uv run python -m aiops_incident_response_agent.main
```

**Programmatic mode** — run a specific scenario directly:

```python
import asyncio
from aiops_incident_response_agent.main import run_incident_response

report = asyncio.run(run_incident_response("deployment_regression"))
print(report)
```

---

## Key Features

### Multi-Agent Pipeline
Six specialized agents collaborate through a handoff chain to process incidents end-to-end:

| Agent | Role | Tools |
|-------|------|-------|
| **Triage Agent** | Initial assessment, severity classification, routing | `fetch_active_alerts`, `get_service_health_summary` |
| **Log Analyzer Agent** | Error pattern detection, log volume analysis | `query_logs`, `search_error_patterns`, `get_log_statistics` |
| **Metrics Analyzer Agent** | Anomaly detection, trend analysis, dependency mapping | `query_metrics`, `detect_anomalies`, `get_service_dependencies` |
| **Root Cause Analyzer Agent** | Signal correlation, trace analysis, deployment checks | `correlate_signals`, `query_traces`, `get_recent_deployments` |
| **Remediation Agent** | Runbook lookup, action proposals (rollback, scaling, config) | `lookup_runbook`, `propose_rollback`, `propose_scaling_action`, `propose_config_change` |
| **Incident Reporter Agent** | Timeline generation, structured report formatting | `generate_timeline`, `format_incident_report` |

### Simulated Observability Stack
A fully self-contained simulation layer generates realistic, correlated observability data across 8 microservices:

- **Logs** — Application logs with error patterns, stack traces, and cascading failures
- **Metrics** — Time-series data for CPU, memory, latency, error rates, and request rates
- **Alerts** — Monitoring alerts with severity levels and service attribution
- **Traces** — Distributed trace spans showing request flow across services
- **Deployments** — Recent deployment records with version info and rollback availability

### 5 Pre-Built Incident Scenarios

| Scenario | Description |
|----------|-------------|
| `memory_leak` | Gradual memory exhaustion in order-service leading to OOM kills and cascading failures |
| `deployment_regression` | Bad deployment of user-service v2.5.0 causing NullPointerExceptions and latency spikes |
| `database_exhaustion` | Connection pool exhaustion on database-proxy cascading to dependent services |
| `network_partition` | Network partition isolating inventory-service from the rest of the cluster |
| `cpu_spike` | CPU saturation on payment-service causing request queue buildup and timeouts |

### Safety Guardrails
- **Input Guardrail** — Validates that scenario data is loaded and contains actionable observability data before the pipeline starts
- **Output Guardrail** — Blocks dangerous remediation actions (destructive commands like `rm -rf`, `drop database`, etc.) from being proposed

### OpenRouter Integration
Uses OpenRouter as a drop-in replacement for the OpenAI API, enabling access to multiple LLM providers through a single API key. Configured via `OpenAIChatCompletionsModel` from the Agents SDK.

### Observability
- Structured logging throughout all components using Python's `logging` module
- `AgentHooks` lifecycle callbacks print agent transitions, tool invocations, and handoffs in real-time
- All tool calls are logged with parameters and result summaries

---

## Project Structure

```
projects/aiops_incident_response_agent/
├── main.py                          # Entry point, pipeline orchestration
├── utils/
│   └── config.py                    # OpenRouter configuration loader
├── models/
│   ├── incident.py                  # Alert, ServiceHealth, TriageResult
│   ├── analysis.py                  # LogEntry, MetricDataPoint, TraceSpan, Deployment, etc.
│   └── remediation.py               # RemediationAction, RemediationPlan
├── agents/
│   ├── triage.py                    # Triage Agent definition
│   ├── log_analyzer.py              # Log Analyzer Agent definition
│   ├── metrics_analyzer.py          # Metrics Analyzer Agent definition
│   ├── root_cause_analyzer.py       # Root Cause Analyzer Agent definition
│   ├── remediation.py               # Remediation Agent definition
│   └── incident_reporter.py         # Incident Reporter Agent definition
├── tools/
│   ├── alert_tools.py               # Alert and health query tools
│   ├── log_tools.py                 # Log query and analysis tools
│   ├── metrics_tools.py             # Metrics query and anomaly detection tools
│   ├── trace_tools.py               # Trace query and signal correlation tools
│   ├── remediation_tools.py         # Runbook lookup and action proposal tools
│   └── notification_tools.py        # Report formatting and timeline tools
├── simulators/
│   ├── scenario_engine.py           # Scenario orchestrator and ScenarioData model
│   ├── log_simulator.py             # Realistic log generation
│   ├── metrics_simulator.py         # Time-series metrics generation
│   ├── alert_simulator.py           # Alert and health data generation
│   └── trace_simulator.py           # Distributed trace and deployment generation
└── guardrails/
    ├── input_validation.py          # Input guardrail for scenario data
    └── remediation_safety.py        # Output guardrail for remediation safety
```

---

## Usage Examples

### Run a Specific Scenario

```python
import asyncio
from aiops_incident_response_agent.main import run_incident_response

# Available scenarios: memory_leak, deployment_regression,
# database_exhaustion, network_partition, cpu_spike
report = asyncio.run(run_incident_response("memory_leak"))
print(report)
```

### Use a Different Model

Set the `OPENROUTER_MODEL` environment variable or update `.env`:

```bash
OPENROUTER_MODEL=anthropic/claude-sonnet-4 PYTHONPATH=projects uv run python -m aiops_incident_response_agent.main
```

### Generate Scenario Data Without Running Agents

```python
from aiops_incident_response_agent.simulators.scenario_engine import generate_scenario

data = generate_scenario("cpu_spike")
print(f"Logs: {len(data.logs)}, Metrics: {len(data.metrics)}")
print(f"Alerts: {len(data.alerts)}, Traces: {len(data.traces)}")
```

---

## Sample Output

When running the `deployment_regression` scenario, the pipeline produces output like:

```
============================================================
  STARTING INCIDENT RESPONSE PIPELINE
============================================================

  AGENT: Triage Agent
  [Triage Agent] calling tool: fetch_active_alerts
  [Triage Agent] calling tool: get_service_health_summary

  >> Handoff: Triage Agent -> Log Analyzer Agent

  AGENT: Log Analyzer Agent
  [Log Analyzer Agent] calling tool: search_error_patterns
  [Log Analyzer Agent] calling tool: get_log_statistics
  [Log Analyzer Agent] calling tool: query_logs

  >> Handoff: Log Analyzer Agent -> Root Cause Analyzer Agent

  AGENT: Root Cause Analyzer Agent
  [Root Cause Analyzer Agent] calling tool: correlate_signals
  [Root Cause Analyzer Agent] calling tool: query_traces
  [Root Cause Analyzer Agent] calling tool: get_recent_deployments

  >> Handoff: Root Cause Analyzer Agent -> Remediation Agent

  AGENT: Remediation Agent
  [Remediation Agent] calling tool: lookup_runbook
  [Remediation Agent] calling tool: propose_rollback
  [Remediation Agent] calling tool: propose_scaling_action

  >> Handoff: Remediation Agent -> Incident Reporter Agent

  AGENT: Incident Reporter Agent
  [Incident Reporter Agent] calling tool: generate_timeline
  [Incident Reporter Agent] calling tool: format_incident_report

  [Incident Reporter Agent] completed.

================================================================================
                         INCIDENT REPORT
================================================================================
Title:              user-service v2.5.0 deployment regression
Severity:           P1
Status:             mitigating
...
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | — | Your OpenRouter API key |
| `OPENROUTER_BASE_URL` | No | `https://openrouter.ai/api/v1` | OpenRouter API base URL |
| `OPENROUTER_MODEL` | No | `openai/gpt-5-mini` | Model to use via OpenRouter |
