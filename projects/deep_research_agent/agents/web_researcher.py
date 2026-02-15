"""Web Researcher Agent -- general web search specialist.

Executes web searches using Tavily and DuckDuckGo to find relevant
web pages, articles, and documentation for the research query.
"""

from agents import Agent, ModelSettings
from deep_research_agent.tools.web_search_tools import (
    duckduckgo_news_search,
    duckduckgo_text_search,
    tavily_web_search,
)

WEB_RESEARCHER_INSTRUCTIONS = """You are the Web Researcher Agent. You search the web using Tavily and DuckDuckGo, then IMMEDIATELY hand off to the Content Extractor Agent. You NEVER produce a final answer yourself.

## Workflow

1. Use tavily_web_search for the main query and key sub-questions.
2. Use duckduckgo_text_search for complementary results.
3. Use duckduckgo_news_search for current events aspects.
4. After 2-4 searches, IMMEDIATELY call transfer_to_content_extractor_agent.
   Include ALL search results (titles, URLs, content snippets) in the transfer message.

## CRITICAL RULES
- You MUST call transfer_to_content_extractor_agent when done searching. This is mandatory.
- Do NOT produce a final answer. You are NOT the last agent.
- Your ONLY job is to search and then hand off results.
- Use at least 2 different search tools for coverage.
- If a tool fails, skip it and try another. Do not stop.
"""


def create_web_researcher_agent(content_extractor: Agent, hooks=None) -> Agent:
    """Create the Web Researcher Agent.

    Args:
        content_extractor: The Content Extractor agent to hand off to.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured web researcher agent.
    """
    return Agent(
        name="Web Researcher Agent",
        instructions=WEB_RESEARCHER_INSTRUCTIONS,
        tools=[tavily_web_search, duckduckgo_text_search, duckduckgo_news_search],
        handoffs=[content_extractor],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.2),
    )
