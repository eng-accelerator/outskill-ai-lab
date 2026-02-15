# Browser Automation Agent

A multi-agent browser automation system that navigates web pages, interacts with elements, and extracts structured data using the **Stagehand Python SDK** for browser control and **OpenAI Agents SDK** for LLM orchestration.

The agent decomposes a high-level task (like "extract the top posts from Hacker News") into browser-level steps, executes them through a local Chrome instance, and produces a structured report with the extracted data.

## Key Features

- **6 Specialized Agents**: Task Planner, Navigator, Interactor, Extractor, Validator, Reporter
- **5 Browser Tools**: Navigate, observe, act, extract (structured), extract (text) — each wrapping a Stagehand SDK method
- **Local Chrome Mode**: Runs headless Chrome locally via Stagehand — no cloud browser service needed
- **Observe-Then-Act Pattern**: Discovers page elements before interacting (no blind clicking)
- **Structured Extraction**: Pulls typed data from pages using JSON Schema definitions
- **2 Predefined Scenarios**: Web scraping (Hacker News) and form automation (Google Search)
- **Input/Output Guardrails**: Validates tasks and ensures report quality
- **Full Observability**: AgentHooks + structured logging for every agent, tool, and handoff

## Setup Instructions

### 1. Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Google Chrome or Chromium installed locally

### 2. Install Dependencies

From the repository root:

```bash
uv add stagehand
```

The following are already included:
- `openai-agents` (OpenAI Agents SDK)
- `python-dotenv` (Environment variable loading)

### 3. Configure API Keys

Create or update the `.env` file in the repository root:

```env
# Required: OpenRouter API key for agent orchestration
OPENROUTER_API_KEY=your_openrouter_key_here

# Required: API key for Stagehand's internal LLM (OpenAI, Anthropic, or OpenRouter key)
MODEL_API_KEY=your_model_api_key_here

# Optional: Override the default model
OPENROUTER_MODEL=openai/gpt-4.1-mini
```

**API Keys:**
- OpenRouter: [https://openrouter.ai/](https://openrouter.ai/)
- MODEL_API_KEY: Any OpenAI-compatible key (Stagehand uses it for element identification)

### 4. Run the Agent

```bash
cd projects
PYTHONPATH=. uv run python -m browser_automation_agent.main
```

Or programmatically:

```python
import asyncio
from browser_automation_agent.main import run_browser_automation

async def automate():
    report = await run_browser_automation(
        "Extract the top 10 posts from Hacker News including title, URL, and points"
    )
    print(report)

asyncio.run(automate())
```

## Usage

### Interactive Mode

Run the agent and select a scenario:

```
============================================================
  BROWSER AUTOMATION AGENT
============================================================

Select a predefined scenario or enter a custom task:

  [1] Web Scraping — Hacker News
      Extract the top 10 posts from Hacker News including title, URL, and points for each post.

  [2] Form Automation — Google Search
      Go to Google, search for 'Python browser automation', and extract the first 5 search results with title and URL.

  [3] Enter a custom task

Select (1/2/3):
```

### Scenario 1: Web Scraping

**Task**: Extract top 10 posts from Hacker News

Pipeline: Planner → Navigator (navigate to HN) → Interactor (skip, no interaction needed) → Extractor (extract posts via schema) → Validator → Reporter

### Scenario 2: Form Automation

**Task**: Search Google and extract results

Pipeline: Planner → Navigator (navigate to Google) → Interactor (type query, press Enter) → Extractor (extract search results) → Validator → Reporter

## Stagehand Integration

| Stagehand Method | Wrapped Tool | Used By |
|------------------|-------------|---------|
| `session.navigate(url=...)` | `navigate_to_url` | Navigator Agent |
| `session.observe(instruction=...)` | `observe_page` | Interactor Agent |
| `session.act(input=...)` | `perform_action` | Interactor Agent |
| `session.extract(instruction=..., schema=...)` | `extract_page_data` | Extractor Agent |
| `session.extract(instruction=..., schema=text)` | `extract_text` | Extractor Agent |

## Project Structure

```
browser_automation_agent/
├── __init__.py
├── __main__.py                    # Module entry point
├── main.py                        # Pipeline orchestration, hooks, scenarios
├── utils/
│   └── config.py                  # Env vars: MODEL_API_KEY, OPENROUTER_*
├── models/
│   ├── __init__.py                # Re-exports all models
│   ├── task.py                    # TaskStep, TaskPlan, BrowserContext
│   ├── page.py                    # PageObservation, ActionRecord
│   └── result.py                  # ExtractionResult, AutomationReport
├── tools/
│   ├── navigation_tools.py        # navigate_to_url
│   ├── observation_tools.py       # observe_page
│   ├── interaction_tools.py       # perform_action
│   └── extraction_tools.py        # extract_page_data, extract_text
├── guardrails/
│   ├── input_validation.py        # Task + API key validation
│   └── output_validation.py       # Report quality validation
└── agents/
    ├── task_planner.py            # Decomposes task, classifies scenario type
    ├── navigator.py               # Navigates to target URLs
    ├── interactor.py              # Observe-then-act loop for interactions
    ├── extractor.py               # Structured data extraction via schemas
    ├── validator.py               # Verifies task completion
    └── reporter.py                # Compiles final report (terminal)
```
