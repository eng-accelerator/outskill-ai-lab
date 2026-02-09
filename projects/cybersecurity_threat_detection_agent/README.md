# Cybersecurity Threat Detection Agent

An autonomous SOC (Security Operations Center) analyst built with the OpenAI Agents SDK and OpenRouter. It ingests SIEM-style security events, correlates threats across authentication, network, API, endpoint, and cloud data sources, assigns threat scores, maps to MITRE ATT&CK, drafts SOC incident reports, and proposes containment actions.

---

## Setup

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- An [OpenRouter](https://openrouter.ai/) API key

### Installation

```bash
# Clone the repository (if not already done)
cd outskill-ai-lab

# Install dependencies
uv sync
```

### Environment Variables

Create or update the `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-5-mini
```

### Running the Agent

```bash
# Interactive mode (select a scenario)
PYTHONPATH=projects uv run python -m cybersecurity_threat_detection_agent.main

# Programmatic mode (specific scenario)
PYTHONPATH=projects uv run python -c "
import asyncio
from cybersecurity_threat_detection_agent.main import run_threat_detection

async def main():
    report = await run_threat_detection('brute_force_attack')
    print(report)

asyncio.run(main())
"
```

---

## Key Features

| Agent | Responsibility | Tools |
|-------|---------------|-------|
| **Alert Intake Agent** | Ingest security events, classify threat category, assign initial severity, route to specialist | `fetch_security_alerts`, `get_asset_inventory` |
| **Auth Analyzer Agent** | Analyze authentication logs for brute force, impossible travel, credential stuffing, privilege escalation | `query_auth_logs`, `detect_anomalous_logins`, `check_privilege_changes` |
| **Network/API Analyzer Agent** | Analyze network logs, API access patterns, detect C2 communication, data exfiltration | `query_network_logs`, `query_api_access_logs`, `detect_c2_patterns` |
| **Threat Intel Agent** | Enrich findings with IOC lookups, MITRE ATT&CK mapping, reputation scoring, compute threat score | `lookup_ioc`, `map_mitre_attack`, `get_threat_reputation` |
| **Containment Agent** | Propose containment actions (block IP, disable account, revoke key, isolate host) | `propose_ip_block`, `propose_account_disable`, `propose_api_key_revoke`, `propose_host_isolation` |
| **SOC Report Agent** | Generate structured SOC incident report with timeline, threat score, MITRE mapping, evidence | `generate_threat_timeline`, `format_soc_report` |

---

## Pre-Built Threat Scenarios

| Scenario | Description |
|----------|-------------|
| `brute_force_attack` | Brute force against admin accounts from botnet IPs, account compromise, lateral movement |
| `insider_threat` | Employee escalates privileges, accesses sensitive APIs, exfiltrates data via cloud storage |
| `api_key_compromise` | Leaked production API key used from foreign IP for mass data extraction |
| `malware_lateral_movement` | Phishing leads to Cobalt Strike beacon, Mimikatz credential dump, PsExec lateral movement, C2 beaconing |
| `cloud_misconfiguration` | S3 bucket made public, security group opened to 0.0.0.0/0, external actors access sensitive data |

---

## Project Structure

```
projects/cybersecurity_threat_detection_agent/
├── main.py                          # Entry point, OpenRouter config, pipeline orchestration
├── utils/
│   └── config.py                    # Environment variable loader
├── models/
│   ├── events.py                    # SecurityAlert, AssetInfo, ThreatCategory, ThreatSeverity
│   ├── analysis.py                  # AuthLogEntry, NetworkLogEntry, APIAccessEntry, EndpointEvent, CloudAuditEntry, IOCMatch, MITREMapping
│   └── response.py                  # ContainmentAction, ThreatScore, SOCIncidentReport
├── simulators/
│   ├── auth_log_simulator.py        # Auth log generation (brute force, impossible travel, etc.)
│   ├── network_log_simulator.py     # Network/firewall log generation (C2, scanning, exfil)
│   ├── api_access_simulator.py      # API access log generation (abuse, key compromise)
│   ├── endpoint_simulator.py        # Endpoint/EDR event generation (malware, lateral movement)
│   ├── cloud_audit_simulator.py     # Cloud audit trail generation (IAM, S3, security groups)
│   └── scenario_engine.py           # Orchestrates all simulators for 5 threat scenarios
├── tools/
│   ├── alert_tools.py               # fetch_security_alerts, get_asset_inventory
│   ├── auth_tools.py                # query_auth_logs, detect_anomalous_logins, check_privilege_changes
│   ├── network_tools.py             # query_network_logs, query_api_access_logs, detect_c2_patterns
│   ├── threat_intel_tools.py        # lookup_ioc, map_mitre_attack, get_threat_reputation
│   ├── containment_tools.py         # propose_ip_block, propose_account_disable, propose_api_key_revoke, propose_host_isolation
│   └── reporting_tools.py           # generate_threat_timeline, format_soc_report
├── guardrails/
│   ├── input_validation.py          # Validates security event data before processing
│   └── containment_safety.py        # Blocks dangerous/overbroad containment actions
└── agents/
    ├── alert_intake.py              # Alert Intake Agent (entry point, routing)
    ├── auth_analyzer.py             # Auth Analyzer Agent (identity threats)
    ├── network_analyzer.py          # Network/API Analyzer Agent (network threats)
    ├── threat_intel.py              # Threat Intel Agent (IOC, MITRE, reputation)
    ├── containment.py               # Containment Agent (propose actions)
    └── soc_reporter.py              # SOC Report Agent (final report, terminal)
```

---

## Usage Examples

### Run a Specific Scenario Programmatically

```python
import asyncio
from cybersecurity_threat_detection_agent.main import run_threat_detection

report = asyncio.run(run_threat_detection("malware_lateral_movement"))
print(report)
```

### Use a Different Model

Update `.env`:

```env
OPENROUTER_MODEL=anthropic/claude-sonnet-4
```

### Test Simulators Standalone

```python
from cybersecurity_threat_detection_agent.simulators.scenario_engine import generate_scenario

data = generate_scenario("insider_threat")
print(f"Auth logs: {len(data.auth_logs)}")
print(f"Network logs: {len(data.network_logs)}")
print(f"API logs: {len(data.api_access_logs)}")
print(f"Alerts: {len(data.alerts)}")
```

---

## Sample Output

```
======================================================================
SOC INCIDENT REPORT
======================================================================

TITLE: Brute Force Compromise of 'admin' with Lateral Movement
SEVERITY: CRITICAL
THREAT SCORE: 88/100
STATUS: CONTAINING

EXECUTIVE SUMMARY
Multiple external IPs executed a coordinated brute-force campaign against
the privileged 'admin' account. A successful login from malicious IP
185.220.101.34 led to lateral movement to jsmith and mchen accounts.

MITRE ATT&CK MAPPING
T1110 (Brute Force), T1078 (Valid Accounts), T1110.004 (Credential Stuffing)

CONTAINMENT ACTIONS
1) Block 5 malicious external IPs at firewall
2) Disable compromised accounts (admin, jsmith, mchen)
3) Isolate affected workstations for forensic imaging
...
======================================================================
END OF REPORT
======================================================================
```

---

## Environment Variable Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key (required) | - |
| `OPENROUTER_BASE_URL` | OpenRouter API base URL | `https://openrouter.ai/api/v1` |
| `OPENROUTER_MODEL` | LLM model to use via OpenRouter | `openai/gpt-5-mini` |
