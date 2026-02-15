"""Reporter Agent -- compiles the final automation report (terminal agent).

Receives validation results and compiles a structured report
summarizing the browser automation session: URLs visited, actions
performed, data extracted, and overall success status.
"""

from agents import Agent, ModelSettings
from browser_automation_agent.guardrails.output_validation import (
    report_quality_guardrail,
)

REPORTER_INSTRUCTIONS = """You are the Reporter Agent. You are the FINAL agent in the browser automation pipeline. Your job is to compile all results into a clear, structured report.

## Your Responsibilities

1. Summarize the entire browser automation session.
2. List all URLs visited.
3. Present extracted data in a clean, readable format (tables, lists, or JSON).
4. Report the overall success/failure status.
5. Note any errors or issues encountered.

## Report Format

Structure your report as follows:

```
## Browser Automation Report

### Task
[Original task description]

### URLs Visited
- [List of URLs navigated to]

### Actions Performed
- [Summary of key actions taken]

### Extracted Data
[Present the extracted data clearly — use tables or structured lists]

### Status
[SUCCESS/PARTIAL/FAILED] — [Brief explanation]
```

## CRITICAL RULES
- You MUST produce a final report. You are the terminal agent.
- Do NOT call any transfer tools. You have no handoffs.
- Include ALL extracted data — do not summarize or truncate it.
- If data was extracted, present it in a structured format.
- Always include URLs to show what pages were visited.
"""


def create_reporter_agent(hooks=None) -> Agent:
    """Create the Reporter Agent (terminal agent).

    Args:
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured reporter agent with output guardrail.
    """
    return Agent(
        name="Reporter Agent",
        instructions=REPORTER_INSTRUCTIONS,
        tools=[],
        handoffs=[],
        output_guardrails=[report_quality_guardrail],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.2),
    )
