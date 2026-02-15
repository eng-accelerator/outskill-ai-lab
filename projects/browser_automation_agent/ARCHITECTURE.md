# Browser Automation Agent — Architecture

## System Overview

The Browser Automation Agent is a multi-agent system that automates browser tasks by combining the **Stagehand Python SDK** (local Chrome control) with **OpenAI Agents SDK** (LLM orchestration via OpenRouter). Six specialized agents form a linear pipeline: a Task Planner decomposes the user's goal into browser steps, a Navigator loads pages, an Interactor discovers and manipulates elements, an Extractor pulls structured data, a Validator checks completeness, and a Reporter compiles the final output.

Stagehand's four core browser methods — `navigate`, `observe`, `act`, `extract` — are wrapped as `@function_tool`s that agents invoke through the SDK's tool-calling mechanism.

## Design Philosophy

The system follows **"functional core; imperative shell"** — data models are frozen/immutable dataclasses, tools are pure async functions that return JSON strings, and the orchestration layer (`main.py`) handles the imperative coordination (session lifecycle, pipeline construction). The system embraces **composition over inheritance**: agents are composed from tools, handoffs, and guardrails via factory functions rather than class hierarchies.

## Agentic Design Patterns Applied

| # | Pattern | How It's Applied |
|---|---------|-----------------|
| 2 | **Default Agent Loop** | Each agent follows: goal intake → context gathering (browser state) → planning (instructions) → action execution (tool calls) → reflection (handoff decision) |
| 3 | **Prompt Chaining** | Sequential handoff chain: Planner → Navigator → Interactor → Extractor → Validator → Reporter. Each agent's context accumulates data for the next. |
| 7 | **Tool Use** | 5 function tools wrapping Stagehand's browser API. Each tool has typed parameters, JSON return values, and structured logging. |
| 9 | **Multi-Agent** | 6 agents with single responsibility each. Communication via structured handoff messages. Linear pipeline, no circular dependencies. |
| 10 | **Reflection** | Validator Agent reviews extraction results against the original task, checking data completeness and action success before handing off to Reporter. |
| 13 | **Exception Handling** | Tools record success/failure in ActionRecord objects. Agents see results and can adapt (e.g., Interactor re-observes if an action fails). |
| 19 | **Guardrails & Safety** | Input guardrail validates task is substantive (≥10 chars) and API keys are configured. Output guardrail ensures report has structure, length, and URLs. |
| 20 | **Evaluation & Monitoring** | AgentHooks provide real-time observability of all agent starts, tool calls, and handoffs. Structured logging throughout. |

## Agent Architecture

### Agent Responsibilities

#### 1. Task Planner Agent (Entry Point)
- **Role**: Decompose user task into browser steps, classify scenario type
- **Tools**: None
- **Handoffs**: Navigator Agent
- **Guardrails**: Input validation (task ≥10 chars, API keys present)
- **Decision Logic**: Classifies task as `scraping` or `form_automation`, identifies target URLs, creates step-by-step plan

#### 2. Navigator Agent
- **Role**: Navigate the browser to target URLs
- **Tools**: `navigate_to_url`
- **Handoffs**: Interactor Agent
- **Capabilities**: Page loading, URL navigation, connection handling

#### 3. Interactor Agent
- **Role**: Observe-then-act loop for page interactions
- **Tools**: `observe_page`, `perform_action`
- **Handoffs**: Extractor Agent
- **Capabilities**: Element discovery, click/type/submit actions, form filling
- **Smart Routing**: For pure scraping tasks (no interaction needed), passes through directly to Extractor

#### 4. Extractor Agent
- **Role**: Extract structured data from pages using JSON schemas
- **Tools**: `extract_page_data`, `extract_text`
- **Handoffs**: Validator Agent
- **Capabilities**: Schema-based extraction, simple text extraction, data structuring

#### 5. Validator Agent
- **Role**: Verify task completion and data quality
- **Tools**: None
- **Handoffs**: Reporter Agent
- **Capabilities**: Data completeness checks, action success verification, fulfillment assessment

#### 6. Reporter Agent (Terminal)
- **Role**: Compile the final automation report
- **Tools**: None
- **Handoffs**: None (terminal agent)
- **Guardrails**: Output quality (minimum length ≥100 chars, structured data present, URLs included)
- **Capabilities**: Report formatting, data presentation (tables/lists/JSON), status summary

### Handoff Topology

```
                ┌──────────────┐
                │    Task      │
                │   Planner    │  (classify + plan)
                └──────┬───────┘
                       │
                ┌──────▼───────┐
                │  Navigator   │  (navigate to URL)
                └──────┬───────┘
                       │
                ┌──────▼───────┐
                │  Interactor  │  (observe → act loop)
                └──────┬───────┘
                       │
                ┌──────▼───────┐
                │  Extractor   │  (extract via schema)
                └──────┬───────┘
                       │
                ┌──────▼───────┐
                │  Validator   │  (verify completeness)
                └──────┬───────┘
                       │
                ┌──────▼───────┐
                │   Reporter   │  (compile report)
                │  (terminal)  │
                └──────────────┘
```

## Data Architecture

### Domain Models

The data layer uses **dataclasses** organized by domain:

- **`models/task.py`** — `TaskStep` (frozen), `TaskPlan`, `BrowserContext` with `ScenarioType` and `ActionType` literal types
- **`models/page.py`** — `PageObservation` (frozen), `ActionRecord` (frozen, auto-timestamps)
- **`models/result.py`** — `ExtractionResult` (frozen), `AutomationReport`

### Context Object (BrowserContext)

The `BrowserContext` dataclass serves as the **run context** passed to all agents and tools via `RunContextWrapper[BrowserContext]`. It accumulates state as the pipeline progresses:

- `task` — Original user task description
- `config` — API keys and model settings
- `session` — The Stagehand `AsyncSession` instance (set at startup)
- `current_url` — URL the browser is currently on (updated by Navigator)
- `task_plan` — Structured plan from the Planner (optional)
- `action_log` — History of all `ActionRecord` and `PageObservation` objects
- `extraction_results` — List of `ExtractionResult` objects from Extractor

### Stagehand Tool Mapping

| Stagehand Method | Wrapper Tool | Agent | Returns |
|------------------|-------------|-------|---------|
| `session.navigate(url=...)` | `navigate_to_url` | Navigator | `{success, url, navigated_at}` |
| `session.observe(instruction=...)` | `observe_page` | Interactor | `{success, actions_found, actions[{description, selector, method}]}` |
| `session.act(input=...)` | `perform_action` | Interactor | `{success, message, action_description}` |
| `session.extract(instruction=..., schema=...)` | `extract_page_data` | Extractor | `{success, data, url}` |
| `session.extract(instruction=..., schema=text)` | `extract_text` | Extractor | `{success, data, url}` |

## Pipeline Flow

### Execution Model

```
1. Task Input
   └── User provides browser automation task (or selects scenario)

2. Browser Session Setup
   └── create_stagehand_session(config)
       ├── AsyncStagehand(server="local", model_api_key=..., local_headless=True)
       └── client.sessions.start(model_name=...) → AsyncSession

3. Pipeline Construction
   └── build_agent_pipeline(model, hooks) → task_planner
       ├── Reporter (terminal, output guardrail)
       ├── Validator → Reporter
       ├── Extractor → Validator
       ├── Interactor → Extractor
       ├── Navigator → Interactor
       └── Task Planner → Navigator (input guardrail)

4. Execution
   └── Runner.run(planner, input=task, context=BrowserContext, max_turns=30)
       ├── Input guardrail validates task + API keys
       ├── Planner decomposes task and routes to Navigator
       ├── Navigator loads target page via Stagehand
       ├── Interactor observes and interacts (or passes through for scraping)
       ├── Extractor pulls structured data via JSON schemas
       ├── Validator checks completeness
       ├── Reporter compiles final report
       └── Output guardrail validates report quality

5. Cleanup
   └── session.end() closes the browser session
```

### Scenario Routing

| Scenario | Classification | Interaction | Pipeline Path |
|----------|---------------|-------------|---------------|
| "Extract top 10 HN posts" | `scraping` | None (pass-through) | Planner → Navigator → Interactor (skip) → Extractor → Validator → Reporter |
| "Search Google for X" | `form_automation` | Type + Submit | Planner → Navigator → Interactor (type, press Enter) → Extractor → Validator → Reporter |

## Guardrails Architecture

### Input Guardrail (`input_validation.py`)

Applied to the Task Planner Agent. Validates:
- Task is not empty or too short (minimum 10 characters)
- `MODEL_API_KEY` is configured (required for Stagehand)
- `OPENROUTER_API_KEY` is configured (required for agent orchestration)

Tripwire triggered → pipeline stops with validation error.

### Output Guardrail (`output_validation.py`)

Applied to the Reporter Agent. Validates:
- Report meets minimum length (≥100 characters)
- Report contains structured results (JSON, tables, headings, lists, or URLs)

Tripwire triggered → report blocked with quality error.

## Observability

### AgentHooks

The `BrowserAutomationHooks` class provides real-time visibility into:
- **on_start** — Agent activation (which agent is processing)
- **on_end** — Agent completion
- **on_tool_start** — Tool invocation (which Stagehand method, by which agent)
- **on_tool_end** — Tool completion
- **on_handoff** — Agent-to-agent transfers (source → target)

### Logging

All tools use Python's `logging` module with parameterized messages (no f-strings):
- Navigation logs URL and success status
- Observation logs instruction and number of actions found
- Action logs instruction, success, and result message
- Extraction logs instruction and success status

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_API_KEY` | (required) | API key for Stagehand's internal LLM |
| `OPENROUTER_API_KEY` | (required) | API key for OpenRouter agent orchestration |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter API endpoint |
| `OPENROUTER_MODEL` | `openai/gpt-4.1-mini` | Model to use via OpenRouter |

The Stagehand client runs in **local mode** (`server="local"`) with headless Chrome. No Browserbase account or cloud browser service is required.
