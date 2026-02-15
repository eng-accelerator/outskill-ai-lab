# Browser Automation Agent — Code Guide

## AI Agent Concepts

### What is a Browser Automation Agent?

A Browser Automation Agent is an autonomous system that mimics how a human uses a web browser:
1. **Understand the goal** — decompose a high-level task into browser-level steps
2. **Navigate** — go to the right page
3. **Observe** — identify interactive elements (buttons, inputs, links)
4. **Interact** — click, type, submit forms
5. **Extract** — pull structured data from the page
6. **Report** — present the results in a clean format

Unlike a simple web scraper with hardcoded selectors, this agent uses an LLM to understand page content and adapt to any website.

### Multi-Agent Orchestration

The system uses 6 specialized agents in a linear pipeline:

| Agent | Responsibility | Handoff Target |
|-------|---------------|----------------|
| Task Planner | Classify task, create step plan | Navigator |
| Navigator | Load target URLs | Interactor |
| Interactor | Observe elements, perform actions | Extractor |
| Extractor | Pull structured data via schemas | Validator |
| Validator | Verify data completeness | Reporter |
| Reporter | Compile final report | (terminal) |

Each agent has a single responsibility and communicates through handoffs.

---

## OpenAI Agents SDK Constructs

### Agent

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Task Planner Agent",
    instructions="...",           # System prompt
    tools=[],                     # Function tools
    handoffs=[navigator],         # Agents to hand off to
    input_guardrails=[guard],     # Validate input
    hooks=hooks,                  # Lifecycle callbacks
    model_settings=ModelSettings(temperature=0.3),
)
```

The `Agent` class wraps an LLM with instructions, tools, and handoffs. The SDK automatically generates `transfer_to_<agent_name>` functions for each handoff target.

### Function Tools

```python
from agents import RunContextWrapper, function_tool
from browser_automation_agent.models.task import BrowserContext

@function_tool
async def navigate_to_url(
    ctx: RunContextWrapper[BrowserContext],
    url: str,
) -> str:
    """Navigate the browser to the specified URL."""
    session = ctx.context.session
    response = await session.navigate(url=url)
    return json.dumps({"success": response.success, "url": url})
```

Tools are async functions decorated with `@function_tool`. They receive a typed `RunContextWrapper[BrowserContext]` context and return JSON strings. The SDK extracts parameter schemas from type annotations.

### Guardrails

```python
from agents import GuardrailFunctionOutput, InputGuardrail

async def validate_automation_input(ctx, agent, input_data):
    if len(ctx.context.task.strip()) < 10:
        return GuardrailFunctionOutput(
            output_info="Task too short.",
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(
        output_info="Task validated.",
        tripwire_triggered=False,
    )

automation_input_guardrail = InputGuardrail(
    guardrail_function=validate_automation_input,
    name="automation_input_validation",
)
```

Guardrails validate inputs/outputs. When `tripwire_triggered=True`, the pipeline stops.

### Runner

```python
from agents import Runner, RunConfig

result = await Runner.run(
    starting_agent=planner_agent,
    input="BROWSER AUTOMATION TASK\nTask: ...",
    context=browser_context,
    max_turns=30,
    run_config=RunConfig(workflow_name="browser_automation", tracing_disabled=True),
)
```

The `Runner` executes the agent pipeline, handling tool calls and handoffs automatically.

---

## Stagehand Python SDK

### Session Lifecycle

```python
from stagehand import AsyncStagehand

# 1. Create client in local mode (headless Chrome)
client = AsyncStagehand(
    server="local",
    model_api_key="your-key",
    local_headless=True,
)

# 2. Start a session
session = await client.sessions.start(model_name="openai/gpt-4.1-mini")

# 3. Use the session
await session.navigate(url="https://example.com")
result = await session.observe(instruction="find the search input")
await session.act(input="type 'hello' into the search box")
data = await session.extract(instruction="extract the title", schema={...})

# 4. End the session
await session.end()
```

### Stagehand Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `session.navigate(url=...)` | Load a URL | `SessionNavigateResponse` with `success` |
| `session.observe(instruction=...)` | Find interactive elements | `SessionObserveResponse` with `data.result[]` (description, selector, method) |
| `session.act(input=...)` | Perform browser action | `SessionActResponse` with `data.result` (success, message) |
| `session.extract(instruction=..., schema=...)` | Extract structured data | `SessionExtractResponse` with `data.result` (matches schema) |

---

## File-by-File Walkthrough

### `main.py` — Entry Point

The orchestration center. Contains:
- `BrowserAutomationHooks(AgentHooks)` — lifecycle logging for all agent events
- `create_openrouter_model(config)` — creates OpenRouter-backed LLM
- `create_stagehand_session(config)` — creates local Chrome session via Stagehand
- `build_agent_pipeline(model, hooks)` — builds the 6-agent chain in reverse order
- `run_browser_automation(task)` — full pipeline execution: create session → build pipeline → run → end session
- `main()` — interactive CLI with scenario selection

### `utils/config.py` — Configuration

Loads environment variables via `python-dotenv`:
- `MODEL_API_KEY` — for Stagehand's internal LLM
- `OPENROUTER_API_KEY` — for agent orchestration
- `OPENROUTER_BASE_URL` — defaults to `https://openrouter.ai/api/v1`
- `OPENROUTER_MODEL` — defaults to `openai/gpt-4.1-mini`

### `models/task.py` — Task Data Models

- `ScenarioType = Literal["scraping", "form_automation"]` — task classification
- `ActionType = Literal["navigate", "observe", "click", ...]` — browser action types
- `TaskStep` — frozen dataclass for a single browser step (step_number, action, target_url, instruction, completed)
- `TaskPlan` — mutable dataclass for the full plan (task, scenario_type, steps, target_urls)
- `BrowserContext` — the shared context object passed through the pipeline, holding the Stagehand session, action log, extraction results, and current URL

### `models/page.py` — Page State Models

- `PageObservation` — frozen dataclass recording what elements were found on a page (url, instruction, actions_found, raw_response)
- `ActionRecord` — frozen dataclass recording a browser action (action_type, instruction, success, message, timestamp with auto-UTC default)

### `models/result.py` — Result Models

- `ExtractionResult` — frozen dataclass for extracted data (url, instruction, data as JSON string, schema_used flag)
- `AutomationReport` — mutable dataclass for the final report (task, steps_completed, total_steps, extractions, success, summary, urls_visited)

### `tools/navigation_tools.py` — Navigate Tool

`navigate_to_url(ctx, url)` — wraps `session.navigate(url=url)`. Updates `ctx.context.current_url` and appends an `ActionRecord` to the action log. Returns JSON with success status and URL.

### `tools/observation_tools.py` — Observe Tool

`observe_page(ctx, instruction)` — wraps `session.observe(instruction=instruction)`. Iterates over `response.data.result` to build a list of actions (description, selector, method, arguments). Appends a `PageObservation` to context. Returns JSON with actions found.

### `tools/interaction_tools.py` — Act Tool

`perform_action(ctx, instruction)` — wraps `session.act(input=instruction)`. Reads `response.data.result` for success/message. Appends an `ActionRecord` to context. Returns JSON with action result.

### `tools/extraction_tools.py` — Extract Tools

Two tools:
- `extract_page_data(ctx, instruction, output_schema)` — wraps `session.extract(instruction=..., schema=json.loads(output_schema))`. The agent passes a JSON schema string defining the expected output shape. Appends `ExtractionResult` to context.
- `extract_text(ctx, instruction)` — convenience wrapper that uses a simple `{"type":"object","properties":{"text":{"type":"string"}}}` schema for plain text extraction.

### `guardrails/input_validation.py` — Input Guardrail

`validate_automation_input(ctx, agent, input_data)`:
- Checks task is ≥10 characters
- Checks `MODEL_API_KEY` is set
- Checks `OPENROUTER_API_KEY` is set
- Returns `GuardrailFunctionOutput(tripwire_triggered=True)` on failure

Attached to the Task Planner Agent as `automation_input_guardrail`.

### `guardrails/output_validation.py` — Output Guardrail

`validate_report_quality(ctx, agent, output)`:
- Checks report is ≥100 characters
- Checks for structured results (JSON objects/arrays, markdown tables, headings, numbered/bullet lists, URLs)
- Returns `GuardrailFunctionOutput(tripwire_triggered=True)` on failure

Attached to the Reporter Agent as `report_quality_guardrail`.

### `agents/task_planner.py` — Task Planner

Entry point agent. Analyzes the task, classifies as scraping or form_automation, identifies target URLs, creates a step plan, and hands off to the Navigator. Has the input guardrail attached.

### `agents/navigator.py` — Navigator

Uses `navigate_to_url` to load the target page. After successful navigation, hands off to the Interactor.

### `agents/interactor.py` — Interactor

The observe-then-act agent. For form automation tasks: uses `observe_page` to find elements, then `perform_action` to interact. For scraping tasks: passes through directly. Hands off to the Extractor.

### `agents/extractor.py` — Extractor

Uses `extract_page_data` with JSON schemas to pull structured data, or `extract_text` for simple text. The instructions include example schemas for posts and search results. Hands off to the Validator.

### `agents/validator.py` — Validator

Reviews the extracted data against the original task. Checks data completeness, quality, and action success. Hands off to the Reporter with validation findings.

### `agents/reporter.py` — Reporter (Terminal)

The terminal agent. Compiles a structured report with sections: Task, URLs Visited, Actions Performed, Extracted Data, and Status. Has the output guardrail attached.
