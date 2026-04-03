<p align="center">
  <h1 align="center">🧪 Outskill AI Lab</h1>
  <p align="center">
    Production-grade AI Agent projects built with the OpenAI Agents SDK
    <br />
    <em>Multi-agent pipelines · Full-stack web apps · Real-time streaming · Guardrails · Real-world APIs</em>
  </p>
  <p align="center">
    <a href="https://github.com/ishandutta0098"><img alt="Author" src="https://img.shields.io/badge/creator-Ishan%20Dutta-blue?style=flat-square" /></a>
    <img alt="Python 3.12+" src="https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white" />
    <img alt="uv" src="https://img.shields.io/badge/package%20manager-uv-DE5FE9?style=flat-square" />
    <img alt="OpenAI Agents SDK" src="https://img.shields.io/badge/framework-OpenAI%20Agents%20SDK-412991?style=flat-square&logo=openai&logoColor=white" />
    <img alt="FastAPI" src="https://img.shields.io/badge/backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" />
    <img alt="React" src="https://img.shields.io/badge/frontend-React%2018-61DAFB?style=flat-square&logo=react&logoColor=black" />
    <img alt="License" src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
  </p>
</p>

---

## About

**Outskill AI Lab** is a collection of production-grade AI Agent projects, each designed as a complete, end-to-end multi-agent system. Every project follows battle-tested [agentic design patterns](.cursor/rules/agentic_design_patterns.mdc) — prompt chaining, routing, tool use, guardrails, human-in-the-loop escalation, and observability — implemented with the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) and powered by [OpenRouter](https://openrouter.ai/).

Each project is self-contained with its own agents, tools, models, guardrails, simulators (or real APIs), documentation, a working `main.py` you can run immediately, and a **full-stack web application** (FastAPI backend + React frontend) with real-time SSE streaming.

> **Contributing** — Want to add a new project or improve an existing one? Open an issue and let's discuss!

---

## Projects

| # | Project | Agents | Tools | Description |
|---|---------|--------|-------|-------------|
| 1 | [**AI Ops Incident Response**](projects/aiops_incident_response_agent/) | 6 | 12 | Autonomous incident response — anomaly detection, root-cause analysis, remediation proposals |
| 2 | [**Cybersecurity Threat Detection**](projects/cybersecurity_threat_detection_agent/) | 6 | 12 | Autonomous SOC analyst — SIEM event correlation, MITRE ATT&CK mapping, containment actions |
| 3 | [**Customer Support**](projects/customer_support_agent/) | 6 | 18 | Autonomous support rep — intent classification, order/billing/technical support, CSAT prediction |
| 4 | [**Deep Research**](projects/deep_research_agent/) | 7 | 24 | Autonomous researcher — multi-source web search, source evaluation, cited reports (real APIs) |
| 5 | [**Browser Automation**](projects/browser_automation_agent/) | 6 | 5 | Autonomous browser controller — web scraping, form automation, structured data extraction (Stagehand) |

### Project Details

<details>
<summary><b>1. AI Ops Incident Response Agent</b></summary>
<br />

A multi-agent incident response system that autonomously detects anomalies, performs root-cause analysis, correlates signals across observability data, and proposes remediation actions.

- **Pipeline**: Triage → Log Analyzer → Metrics Analyzer → Root Cause Analyzer → Remediation → Incident Reporter
- **Simulators**: Alert, log, metrics, and trace simulators with 5 pre-built scenarios
- **Guardrails**: Input validation + remediation safety (blocks destructive actions in production)
- **Scenarios**: `cpu_spike`, `memory_leak`, `error_rate_surge`, `latency_degradation`, `cascading_failure`

📖 [README](projects/aiops_incident_response_agent/README.md) · [Architecture](projects/aiops_incident_response_agent/ARCHITECTURE.md) · [Code Guide](projects/aiops_incident_response_agent/CODE.md)

</details>

<details>
<summary><b>2. Cybersecurity Threat Detection Agent</b></summary>
<br />

An autonomous SOC analyst that ingests SIEM-style security events, correlates threats across authentication, network, API, endpoint, and cloud data, assigns threat scores, maps to MITRE ATT&CK, and proposes containment actions.

- **Pipeline**: Alert Intake → Auth Analyzer / Network Analyzer → Threat Intel → Containment → SOC Reporter
- **Simulators**: Auth log, network log, API access, cloud audit, and endpoint simulators with 5 threat scenarios
- **Guardrails**: Input validation + containment safety (validates severity thresholds before action)
- **Scenarios**: `brute_force_attack`, `insider_threat`, `api_key_compromise`, `malware_lateral_movement`, `cloud_misconfiguration`

📖 [README](projects/cybersecurity_threat_detection_agent/README.md) · [Architecture](projects/cybersecurity_threat_detection_agent/ARCHITECTURE.md) · [Code Guide](projects/cybersecurity_threat_detection_agent/CODE.md)

</details>

<details>
<summary><b>3. Customer Support Agent</b></summary>
<br />

An autonomous customer support representative that classifies intents, looks up orders and billing, searches knowledge bases, processes refunds/returns, escalates complex cases, and predicts customer satisfaction.

- **Pipeline**: Intake & Router → Order / Billing / Technical Support → Escalation → Resolution & CSAT
- **Simulators**: Customer, order, billing, and knowledge base simulators with 5 support scenarios
- **Guardrails**: Input validation + response safety (PII leakage prevention, refund caps, language filtering)
- **Scenarios**: `delayed_order`, `refund_request`, `billing_dispute`, `technical_issue`, `complex_escalation`

📖 [README](projects/customer_support_agent/README.md) · [Architecture](projects/customer_support_agent/ARCHITECTURE.md) · [Code Guide](projects/customer_support_agent/CODE.md)

</details>

<details>
<summary><b>4. Deep Research Agent</b></summary>
<br />

An autonomous research system that searches the live web, retrieves academic papers, extracts content, evaluates sources, and synthesizes long-form research reports with citations and confidence scores.

- **Pipeline**: Research Planner → Web / Academic / News Researcher → Content Extractor → Synthesizer → Report Writer
- **Real APIs**: Tavily, DuckDuckGo, Wikipedia, arXiv, Semantic Scholar, Jina Reader, YouTube, Google News, Reddit, GitHub, StackExchange
- **Guardrails**: Input validation (query substantiveness) + output quality (citations, structure, no hallucinated URLs)
- **Capabilities**: APA citations, cross-referencing, credibility scoring, confidence assessment, structured markdown reports

📖 [README](projects/deep_research_agent/README.md) · [Architecture](projects/deep_research_agent/ARCHITECTURE.md) · [Code Guide](projects/deep_research_agent/CODE.md)

</details>

<details>
<summary><b>5. Browser Automation Agent</b></summary>
<br />

An autonomous browser controller that navigates web pages, interacts with elements, and extracts structured data using Stagehand (local Chrome) for browser control and OpenAI Agents SDK for LLM orchestration.

- **Pipeline**: Task Planner → Navigator → Interactor → Extractor → Validator → Reporter
- **Browser Backend**: Stagehand Python SDK with local headless Chrome (no cloud browser service needed)
- **Guardrails**: Input validation (task + API keys) + output quality (report structure, data presence)
- **Scenarios**: Web scraping (Hacker News posts), form automation (Google Search + extract results)

📖 [README](projects/browser_automation_agent/README.md) · [Architecture](projects/browser_automation_agent/ARCHITECTURE.md) · [Code Guide](projects/browser_automation_agent/CODE.md)

</details>

---

## Web Applications

Every project ships with an independent **FastAPI backend** and **React frontend**, turning each CLI-based agent pipeline into a production-ready web application with real-time streaming.

| # | Project | Backend Port | Frontend Port | Design Inspiration |
|---|---------|:---:|:---:|---|
| 1 | Deep Research Agent | 8001 | 5173 | Perplexity AI |
| 2 | Browser Automation Agent | 8002 | 5174 | Comet / Atlas |
| 3 | Customer Support Agent | 8003 | 5175 | Zendesk / Forethought |
| 4 | AI OPs Incident Response Agent | 8004 | 5176 | Datadog Watchdog |
| 5 | Cybersecurity Threat Detection Agent | 8005 | 5177 | CrowdStrike Falcon / MS Sentinel |

**Key features across all web apps:**
- **SSE streaming** -- Real-time agent lifecycle events (agent starts, tool calls, handoffs, phase changes) streamed to the browser via Server-Sent Events
- **Phase indicators** -- Animated pipeline progress showing which agent is currently active
- **Agent activity timeline** -- Collapsible sidebar displaying every tool call, handoff, and agent transition as it happens
- **Markdown report rendering** -- Final reports rendered with full markdown support
- **Dark theme** -- Each project has a unique accent color matching its domain (blue, purple, teal, orange, red)

### Running a Web App

```bash
# Start the backend (from repo root)
PYTHONPATH=projects uv run uvicorn deep_research_agent.api.app:app --reload --port 8001

# Start the frontend (from project's frontend/ dir)
cd projects/deep_research_agent/frontend
npm install   # first time only
npm run dev
```

Then open `http://localhost:5173` in your browser.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Agent Framework** | [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) (`openai-agents`) |
| **LLM Provider** | [OpenRouter](https://openrouter.ai/) (access to GPT-4.1, GPT-5, Claude, etc.) |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) + [SSE-Starlette](https://github.com/sysid/sse-starlette) + [Uvicorn](https://www.uvicorn.org/) |
| **Frontend** | [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/) + [Vite](https://vite.dev/) |
| **Styling** | [TailwindCSS v4](https://tailwindcss.com/) + [Lucide Icons](https://lucide.dev/) |
| **State Management** | [Zustand](https://zustand.docs.pmnd.rs/) + [TanStack Query](https://tanstack.com/query) |
| **Language** | Python 3.12+ / TypeScript |
| **Package Manager** | [uv](https://docs.astral.sh/uv/) (Python) / npm (JS) |
| **Type System** | Modern Python annotations, dataclasses, Literal types, Protocol classes |
| **Web Search** | Tavily, DuckDuckGo |
| **Academic Search** | arXiv, Semantic Scholar, Wikipedia |
| **Content Extraction** | Jina Reader, BeautifulSoup, YouTube Transcript API |
| **News & Community** | Google News RSS, Reddit, GitHub, StackExchange |
| **Browser Automation** | Stagehand Python SDK (local Chrome) |

---

## Quick Start

### Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- **Node.js 18+** and **npm** — for the React frontends

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1. Clone the Repository

```bash
git clone https://github.com/ishandutta0098/outskill-ai-lab.git
cd outskill-ai-lab
```

### 2. Install Dependencies

```bash
uv sync
```

This installs all dependencies from `pyproject.toml` into a virtual environment managed by `uv`.

### 3. Configure Environment Variables

Create a `.env` file in the project root (refer to `dummy.env` for the template):

```env
# Required for all projects — LLM access via OpenRouter
OPENROUTER_API_KEY=your_openrouter_key_here

# Required for Deep Research Agent — Tavily web search
TAVILY_API_KEY=your_tavily_key_here

# Required for Browser Automation Agent — Stagehand's internal LLM
MODEL_API_KEY=your_model_api_key_here
```

**Where to get API keys:**

| Key | Provider | Free Tier |
|-----|----------|-----------|
| `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai/) | Free credits on signup |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com/) | 1,000 searches/month |
| `MODEL_API_KEY` | [openrouter.ai](https://openrouter.ai/) (or OpenAI) | For Stagehand's browser AI |

> **Note**: All other external APIs used by the Deep Research Agent (DuckDuckGo, Wikipedia, arXiv, Semantic Scholar, Jina Reader, YouTube, Google News, Reddit, GitHub, StackExchange) require **no API key**.

### 4. Run a Project

Each project can be run as a **CLI pipeline** or as a **full-stack web application**.

#### Option A: CLI Mode

```bash
# Deep Research Agent
PYTHONPATH=projects uv run python -m deep_research_agent.main

# Browser Automation Agent
PYTHONPATH=projects uv run python -m browser_automation_agent.main

# Customer Support Agent
PYTHONPATH=projects uv run python -m customer_support_agent.main

# AI Ops Incident Response Agent
PYTHONPATH=projects uv run python -m aiops_incident_response_agent.main

# Cybersecurity Threat Detection Agent
PYTHONPATH=projects uv run python -m cybersecurity_threat_detection_agent.main
```

#### Option B: Web Application (Backend + Frontend)

Start the FastAPI backend and React frontend in two separate terminals:

```bash
# Terminal 1 — Backend (e.g. Deep Research Agent on port 8001)
PYTHONPATH=projects uv run uvicorn deep_research_agent.api.app:app --reload --port 8001

# Terminal 2 — Frontend
cd projects/deep_research_agent/frontend
npm install   # first time only
npm run dev
```

Repeat for other projects using their respective ports (see [Web Applications](#web-applications) table above).

#### Programmatic Usage

```python
import asyncio
from deep_research_agent.main import run_deep_research

async def main():
    report = await run_deep_research("What are the latest advancements in quantum computing?")
    print(report)

asyncio.run(main())
```

---

## Repository Structure

```
outskill-ai-lab/
├── .env                          # API keys (create from dummy.env)
├── dummy.env                     # Environment variable template
├── pyproject.toml                # Dependencies and project metadata
├── .cursor/rules/                # Agentic design pattern rules
│   └── agentic_design_patterns.mdc
│
└── projects/
    └── <project_name>/           # Each project follows this structure
        ├── main.py               # CLI pipeline entry point
        ├── agents/               # Agent definitions (OpenAI Agents SDK)
        ├── tools/                # @function_tool implementations
        ├── models/               # Frozen dataclass domain models
        ├── simulators/           # Scenario data generators (where applicable)
        ├── guardrails/           # Input + output guardrails
        ├── utils/                # Config loader
        ├── api/                  # FastAPI backend
        │   ├── app.py            #   App entry with CORS + lifespan
        │   ├── routers/          #   API route handlers
        │   ├── schemas/          #   Pydantic request/response models
        │   └── streaming.py      #   SSE hooks + run state manager
        ├── frontend/             # React frontend (Vite + TypeScript)
        │   ├── src/
        │   │   ├── components/   #   UI components
        │   │   ├── pages/        #   Route-level views
        │   │   ├── hooks/        #   Custom hooks (useSSE, etc.)
        │   │   ├── stores/       #   Zustand state stores
        │   │   └── lib/          #   API client + utilities
        │   ├── package.json
        │   ├── vite.config.ts
        │   └── tsconfig.json
        ├── README.md
        ├── ARCHITECTURE.md
        └── CODE.md
```

---

## Architecture & Design Patterns

Every project in this lab follows a consistent set of agentic design patterns, distilled from [Agentic Design Patterns](https://www.manning.com/books/agentic-design-patterns) by Antonio Gulli:

| Pattern | Description | Applied In |
|---------|-------------|------------|
| **Default Agent Loop** | Goal → Context → Plan → Act → Reflect | All agents |
| **Prompt Chaining** | Sequential handoff chain where each agent's output feeds the next | All pipelines |
| **Routing** | Entry agent classifies input and routes to specialist | All entry agents |
| **Tool Use** | Typed function tools with JSON schemas, strict I/O | 71 tools total |
| **Multi-Agent** | Single-responsibility agents communicating via handoffs | 31 agents total |
| **Guardrails & Safety** | Input validation + output safety on entry/terminal agents | All projects |
| **Human-in-the-Loop** | Escalation paths for cases beyond automated resolution | Customer Support, Cybersecurity |
| **Reflection** | Self-evaluation of source quality and cross-referencing | Deep Research |
| **Evaluation & Monitoring** | AgentHooks for real-time observability of all actions | All projects |
| **Exception Handling** | Graceful degradation with error-as-return-values in tools | All tools |

### Shared Architectural Principles

- **Functional core, imperative shell** — Pure dataclasses and tool functions internally; orchestration in `main.py`
- **Composition over inheritance** — Agents composed from tools, handoffs, and guardrails
- **Errors as values** — Tools return JSON error objects, never raise exceptions
- **Immutable data models** — Frozen dataclasses for all domain types
- **Structured logging** — All tools and agents log via Python's `logging` module
- **OpenRouter as LLM provider** — Drop-in replacement for OpenAI API, supporting any model

---

## Documentation

Each project includes three documentation files:

| File | Purpose |
|------|---------|
| `README.md` | Setup instructions, features, usage examples, project structure |
| `ARCHITECTURE.md` | System design, agent responsibilities, handoff topology, data flow, guardrails |
| `CODE.md` | OpenAI Agents SDK constructs, tool patterns, model explanations, scoring algorithms |

---

## Contributing

Contributions are welcome! If you'd like to:

- **Add a new project** — Open an issue describing the agent system you'd like to build
- **Improve an existing project** — Open a PR with your changes
- **Report a bug** — Open an issue with reproduction steps

Please follow the coding conventions established in the workspace rules:
- Modern Python 3.12+ type annotations
- Dataclasses for domain models (prefer frozen)
- Literal types over string enums
- Global imports, early returns, match-case over if-elif-else
- Structured logging (no f-strings in log calls)
- Errors as return values (no try-except)

---

## License

This project is licensed under the MIT License.

---

<p align="center">
  <em>Built with ❤️ by <a href="https://github.com/ishandutta0098">Ishan Dutta</a></em>
</p>
