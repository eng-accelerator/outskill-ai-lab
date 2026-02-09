"""Content Extractor Agent -- deep content extraction from URLs.

Receives URLs from the search agents and extracts full-text content
using Jina Reader, web scraping, and YouTube transcript extraction.
Hands off extracted content to the Synthesizer.
"""

from agents import Agent, ModelSettings
from deep_research_agent.tools.content_tools import (jina_read_url,
                                                     scrape_webpage,
                                                     youtube_get_transcript)

CONTENT_EXTRACTOR_INSTRUCTIONS = """You are the Content Extractor Agent. You extract content from the most promising URLs, then IMMEDIATELY hand off to the Synthesizer Agent. You NEVER produce a final answer yourself.

## Workflow

1. From the search results given to you, pick the top 2-3 most promising URLs.
2. For each URL, extract content:
   - jina_read_url: Best for most web pages (returns clean markdown).
   - scrape_webpage: Fallback if Jina fails.
   - youtube_get_transcript: For YouTube URLs.
3. After 2-3 extractions, IMMEDIATELY call transfer_to_synthesizer_agent.
   Include ALL findings: search snippets from researchers + extracted content + all URLs.

## CRITICAL RULES
- You MUST call transfer_to_synthesizer_agent when done extracting. This is mandatory.
- Do NOT produce a final answer. You are NOT the last agent.
- If jina_read_url fails, try scrape_webpage as fallback.
- Include source URLs with all content for citation.
"""


def create_content_extractor_agent(synthesizer: Agent, hooks=None) -> Agent:
    """Create the Content Extractor Agent.

    Args:
        synthesizer: The Synthesizer agent to hand off to.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured content extractor agent.
    """
    return Agent(
        name="Content Extractor Agent",
        instructions=CONTENT_EXTRACTOR_INSTRUCTIONS,
        tools=[jina_read_url, scrape_webpage, youtube_get_transcript],
        handoffs=[synthesizer],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.1),
    )
