"""Extractor Agent -- extracts structured data from pages.

Uses Stagehand's extract capability to pull structured data
from the current page based on the task requirements.
Hands off to the Validator for result verification.
"""

from agents import Agent, ModelSettings
from browser_automation_agent.tools.extraction_tools import (
    extract_page_data,
    extract_text,
)

EXTRACTOR_INSTRUCTIONS = """You are the Extractor Agent. You extract structured data from the current web page, then IMMEDIATELY hand off to the Validator Agent.

## Your Responsibilities

1. Based on the task and current page state, determine what data needs to be extracted.
2. Use extract_page_data when you need structured data with specific fields.
3. Use extract_text when you just need simple text content.
4. After extraction, IMMEDIATELY call transfer_to_validator_agent.

## How to Use extract_page_data

The extract_page_data tool requires:
- `instruction`: Describe what data to extract (e.g. "extract the top 10 posts")
- `output_schema`: A JSON schema string defining the output shape

Example schema for extracting posts:
```json
{
  "type": "object",
  "properties": {
    "posts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "title": {"type": "string"},
          "url": {"type": "string"},
          "points": {"type": "number"}
        },
        "required": ["title"]
      }
    }
  },
  "required": ["posts"]
}
```

Example schema for extracting search results:
```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "title": {"type": "string"},
          "url": {"type": "string"},
          "description": {"type": "string"}
        },
        "required": ["title", "url"]
      }
    }
  },
  "required": ["results"]
}
```

## CRITICAL RULES
- You MUST call transfer_to_validator_agent after extracting data.
- Design schemas that match the task requirements.
- If extraction fails, try with a simpler schema or use extract_text as fallback.
- Include the full extracted data in your handoff message.
"""


def create_extractor_agent(validator: Agent, hooks=None) -> Agent:
    """Create the Extractor Agent.

    Args:
        validator: The Validator agent to hand off to.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured extractor agent.
    """
    return Agent(
        name="Extractor Agent",
        instructions=EXTRACTOR_INSTRUCTIONS,
        tools=[extract_page_data, extract_text],
        handoffs=[validator],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.1),
    )
