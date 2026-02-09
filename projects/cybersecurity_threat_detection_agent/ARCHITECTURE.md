# Architecture

## System Overview

The Cybersecurity Threat Detection Agent is a multi-agent pipeline that processes security events through six specialized agents, each with dedicated tools, to produce a comprehensive SOC incident report.

```
Security Event Feed
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT PIPELINE                         │
│                                                                 │
│  ┌──────────────┐                                               │
│  │ Alert Intake  │──── Auth-related ──▶ ┌────────────────┐      │
│  │    Agent      │                      │  Auth Analyzer  │      │
│  │ (Triage +     │                      │     Agent       │──┐   │
│  │  Routing)     │                      └────────────────┘  │   │
│  │               │                                           │   │
│  │               │──── Network-related ▶ ┌────────────────┐  │   │
│  └──────────────┘                       │ Network/API     │  │   │
│                                         │ Analyzer Agent  │──┤   │
│                                         └────────────────┘  │   │
│                                                              │   │
│                                         ┌────────────────┐   │   │
│                                         │  Threat Intel   │◀─┘   │
│                                         │     Agent       │      │
│                                         └───────┬────────┘      │
│                                                  │               │
│                                         ┌────────▼───────┐      │
│                                         │  Containment   │      │
│                                         │     Agent      │      │
│                                         └───────┬────────┘      │
│                                                  │               │
│                                         ┌────────▼───────┐      │
│                                         │  SOC Report    │      │
│                                         │     Agent      │      │
│                                         └────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
        │
        ▼
SOC Incident Report + Threat Score
```

---

## Agentic Design Patterns Applied

The system implements 12 patterns from `agentic_design_patterns.mdc`:

| # | Pattern | Application |
|---|---------|-------------|
| 2 | Default Agent Loop | Each agent follows: goal intake -> context gathering (tools) -> planning -> action -> reflection |
| 3 | Prompt Chaining | 6-agent pipeline: Intake -> Auth/Network Analysis -> Threat Intel -> Containment -> Report |
| 4 | Routing | Alert Intake routes to Auth Analyzer OR Network/API Analyzer based on threat category |
| 5 | Parallelization | Auth and Network analyzers operate independently; Threat Intel agent calls multiple IOC lookups in parallel |
| 7 | Tool Use | 16 tools with strict schemas, JSON returns, error-as-values |
| 8 | Planning | Each agent has explicit numbered workflow steps in instructions |
| 9 | Multi-Agent | 6 agents, single responsibility each, no circular dependencies |
| 13 | Exception Handling | Guardrails, max_turns=40, assertions, error JSON returns |
| 14 | Human-in-the-Loop | Containment actions flagged with `requires_approval` for high-risk targets |
| 15 | Knowledge Retrieval | Threat Intel agent retrieves IOCs, MITRE mappings, reputation data from simulated databases |
| 19 | Guardrails | Input validation (security data present) + containment safety (no mass-disable, no SOC lockout) |
| 20 | Evaluation | AgentHooks for full lifecycle logging (on_start, on_end, on_tool_start, on_tool_end, on_handoff) |

---

## Data Architecture

### Type System

All data models follow the project coding guidelines:

- **Frozen dataclasses** for all data types (products in the algebra of types)
- **Literal types** for enumerations (sums): `ThreatCategory`, `ThreatSeverity`, `AuthAction`, `NetworkAction`, etc.
- **No inheritance** -- composition only
- **Modern Python annotations**: `list[str]`, `dict[str, str]`, `str | None`

### Model Hierarchy

```
models/
├── events.py          # Input types
│   ├── SecurityAlert     (alert_id, source, severity, category, message, timestamp, indicators)
│   ├── AssetInfo         (asset_id, hostname, ip_address, asset_type, owner, criticality)
│   ├── ThreatCategory    Literal["brute_force", "credential_stuffing", ..., "insider_threat"]
│   └── ThreatSeverity    Literal["critical", "high", "medium", "low", "info"]
│
├── analysis.py        # Intermediate types
│   ├── AuthLogEntry      (timestamp, user, source_ip, action, geo_location, ...)
│   ├── NetworkLogEntry   (timestamp, source_ip, dest_ip, dest_port, protocol, bytes, action, ...)
│   ├── APIAccessEntry    (timestamp, user, api_key_id, endpoint, method, status_code, ...)
│   ├── EndpointEvent     (timestamp, hostname, process_name, process_hash, parent_process, ...)
│   ├── CloudAuditEntry   (timestamp, principal, action, resource, resource_type, region, ...)
│   ├── IOCMatch          (indicator, indicator_type, threat_name, confidence, source, ...)
│   └── MITREMapping      (tactic_id, tactic_name, technique_id, technique_name, description)
│
└── response.py        # Output types
    ├── ContainmentAction (action_type, target, reason, risk_level, requires_approval, command)
    ├── ThreatScore       (score, confidence, factors)
    └── SOCIncidentReport (title, severity, threat_score, summary, mitre_mappings, ...)
```

---

## Simulation Architecture

### Simulated Security Stack

Five simulators produce correlated security event data:

| Simulator | Data Source | Events Generated |
|-----------|-----------|-----------------|
| `auth_log_simulator` | Identity/IAM | Normal logins, brute force, impossible travel, privilege escalation, lateral movement |
| `network_log_simulator` | Firewall/NDR | Normal traffic, port scanning, C2 beaconing, data exfiltration, lateral movement |
| `api_access_simulator` | WAF/API Gateway | Normal API usage, admin endpoint access, mass data extraction, key abuse |
| `endpoint_simulator` | EDR | Normal processes, phishing payloads, malware (Cobalt Strike, Mimikatz), PsExec lateral movement |
| `cloud_audit_simulator` | CloudTrail/CSPM | Normal IAM ops, S3 policy changes, security group modifications, secret access |

### Scenario Engine

The `scenario_engine.py` orchestrates all five simulators for each scenario, producing a `ScenarioData` object with:

- Security alerts (SIEM/EDR/WAF/CSPM sources)
- Asset inventory (servers, workstations, cloud resources)
- Auth logs, network logs, API access logs, endpoint events, cloud audit entries

Each scenario generates 50-100+ events across all data sources, with realistic timestamps, IPs, usernames, and indicators.

### Simulated Threat Intelligence

The `threat_intel_tools.py` contains three simulated databases:

1. **IOC Database** -- 10 known-malicious IPs and 3 malware hashes with threat names, confidence scores, and intelligence sources
2. **MITRE ATT&CK Mapping Database** -- 10 threat categories mapped to 20+ MITRE techniques with tactic IDs, technique IDs, and descriptions
3. **Reputation Database** -- IP reputation scores (0-100), abuse report counts, country, and ISP information

---

## Pipeline Execution Flow

### Initialization Phase

```
1. Load config (OpenRouter API key, base URL, model name)
2. Create AsyncOpenAI client pointing to OpenRouter
3. Create OpenAIChatCompletionsModel with the client
4. Disable tracing (not using OpenAI tracing backend)
```

### Agent Construction Phase

Agents are built in reverse order to wire handoffs:

```
1. SOC Report Agent          (terminal, no handoffs)
2. Containment Agent         (handoffs to SOC Report)
3. Threat Intel Agent        (handoffs to Containment)
4. Auth Analyzer Agent       (handoffs to Threat Intel)
5. Network/API Analyzer Agent (handoffs to Threat Intel)
6. Alert Intake Agent        (handoffs to Auth Analyzer + Network Analyzer)
```

All agents receive the same `OpenAIChatCompletionsModel` instance and `AgentHooks`.

### Execution Phase

```
1. Generate ScenarioData via scenario_engine
2. Compose initial threat alert message from scenario alerts
3. Runner.run(starting_agent=alert_intake, input=threat_message, context=scenario_data, max_turns=40)
4. SDK executes the agent loop:
   a. Alert Intake: calls tools, classifies, hands off
   b. Auth/Network Analyzer: calls analysis tools, hands off
   c. Threat Intel: enriches with IOC/MITRE/reputation, hands off
   d. Containment: proposes actions, hands off
   e. SOC Report: generates timeline and report
5. Return result.final_output
```

---

## Configuration Chain

```
.env file
    │
    ▼
utils/config.py (load_config)
    │
    ▼
main.py (create_openrouter_model)
    │
    ▼
AsyncOpenAI client
    │
    ▼
OpenAIChatCompletionsModel
    │
    ▼
Agent.model (set on all 6 agents)
```

---

## Error Handling Strategy

Following the project guidelines of errors-as-values (no try/except):

1. **Assertions** -- `assert scenario_type in generators` for invalid scenarios; `assert api_key` for missing config
2. **Guardrails** -- Input validation trips if no security data; containment safety trips on dangerous patterns
3. **Tool error returns** -- Tools return JSON with error information rather than raising exceptions
4. **max_turns=40** -- Prevents infinite agent loops
5. **Protected accounts/IPs** -- Containment tools flag high-risk targets with warnings and approval requirements

---

## Observability Architecture

### AgentHooks Lifecycle

```
ThreatDetectionHooks
├── on_start(agent)       → Print agent name banner
├── on_end(agent, output) → Print completion message
├── on_tool_start(tool)   → Print tool invocation
├── on_tool_end(tool)     → Print tool completion
└── on_handoff(target)    → Print handoff arrow
```

### Structured Logging

Every tool and simulator uses Python's `logging` module with structured parameters:

```python
logger.info("Queried %d auth logs (user=%s, source_ip=%s, action=%s)", len(logs), user, source_ip, action)
```

No f-strings in logging calls -- formatting is delegated to the logger per project guidelines.

---

## Key Differences from AI Ops Project

| Aspect | AI Ops | Cybersecurity |
|--------|--------|---------------|
| Domain | Infrastructure incidents | Security threats |
| Data sources | Logs, metrics, traces | Auth, network, API, endpoint, cloud audit |
| Routing targets | Log Analyzer / Metrics Analyzer | Auth Analyzer / Network Analyzer |
| Correlation | Cross-signal (logs, metrics, traces) | Cross-source (auth, network, endpoint, cloud) |
| Scoring | Incident severity (P0-P3) | Threat score (0-100) + confidence |
| Knowledge base | Runbooks | MITRE ATT&CK + IOC database + reputation |
| Actions | Rollback, scale, config change | Block IP, disable account, revoke key, isolate host |
| Terminal output | Incident report | SOC incident report with MITRE mapping |
| Simulators | 4 (logs, metrics, alerts, traces) | 5 (auth, network, API, endpoint, cloud) |
| Scenarios | 5 infra scenarios | 5 threat scenarios |
