"""News Researcher Agent -- news, discussions, and community insights specialist.

Searches Google News, Reddit, GitHub, and StackExchange for current
events, community perspectives, open-source projects, and technical Q&A.
"""

from agents import Agent, ModelSettings
from deep_research_agent.tools.code_search_tools import (github_search_repos,
                                                         stackexchange_search)
from deep_research_agent.tools.news_tools import google_news_rss, reddit_search

NEWS_RESEARCHER_INSTRUCTIONS = """You are the News & Community Researcher Agent. You search news, Reddit, GitHub, and StackExchange, then IMMEDIATELY hand off to the Content Extractor Agent. You NEVER produce a final answer yourself.

## Workflow

1. Use google_news_rss for recent news articles.
2. Use reddit_search for community discussions and opinions.
3. For technical topics, also use github_search_repos and stackexchange_search.
4. After 2-4 searches, IMMEDIATELY call transfer_to_content_extractor_agent.
   Include ALL search results (titles, URLs, content, dates) in the transfer message.

## CRITICAL RULES
- You MUST call transfer_to_content_extractor_agent when done searching. This is mandatory.
- Do NOT produce a final answer. You are NOT the last agent.
- Your ONLY job is to search and then hand off results.
- Use at least 2 different search tools for coverage.
- If a tool fails, skip it and try another. Do not stop.
"""


def create_news_researcher_agent(content_extractor: Agent, hooks=None) -> Agent:
    """Create the News & Community Researcher Agent.

    Args:
        content_extractor: The Content Extractor agent to hand off to.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured news researcher agent.
    """
    return Agent(
        name="News Researcher Agent",
        instructions=NEWS_RESEARCHER_INSTRUCTIONS,
        tools=[
            google_news_rss,
            reddit_search,
            github_search_repos,
            stackexchange_search,
        ],
        handoffs=[content_extractor],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.2),
    )
