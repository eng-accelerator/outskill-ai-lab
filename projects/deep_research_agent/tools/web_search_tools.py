"""Web search tools using Tavily and DuckDuckGo.

Provides general-purpose web search capabilities via two complementary
services: Tavily (AI-optimized, API key required) and DuckDuckGo
(free, no API key).
"""

import json
import logging
from datetime import datetime, timezone

from agents import RunContextWrapper, function_tool
from duckduckgo_search import DDGS
from tavily import TavilyClient

from deep_research_agent.models.research import ResearchContext

logger = logging.getLogger(__name__)


@function_tool
def tavily_web_search(
    ctx: RunContextWrapper[ResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Search the web using Tavily Search API (AI-optimized search).

    Tavily provides high-quality, AI-optimized search results with
    content snippets. Best for comprehensive factual queries.

    Args:
        ctx: Run context containing API keys.
        query: The search query string.
        max_results: Maximum number of results to return (1-10).

    Returns:
        str: JSON string with search results including title, url, and content.
    """
    config = ctx.context.config
    api_key = config.get("tavily_api_key")
    if not api_key:
        logger.warning("TAVILY_API_KEY not set, falling back to empty results")
        return json.dumps({"error": "TAVILY_API_KEY not configured", "results": []})

    logger.info("Tavily search: query=%s, max_results=%d", query, max_results)
    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        max_results=min(max_results, 10),
        include_answer=True,
    )

    results = []
    for r in response.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0.0),
        })

    output = {
        "query": query,
        "answer": response.get("answer", ""),
        "results": results,
        "result_count": len(results),
        "searched_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Tavily search returned %d results for: %s", len(results), query)
    return json.dumps(output, indent=2)


@function_tool
def duckduckgo_text_search(
    ctx: RunContextWrapper[ResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Search the web using DuckDuckGo (free, no API key required).

    DuckDuckGo provides privacy-focused web search results. Good as
    a complementary or fallback search engine.

    Args:
        ctx: Run context (unused but required by framework).
        query: The search query string.
        max_results: Maximum number of results to return (1-10).

    Returns:
        str: JSON string with search results including title, url, and body.
    """
    logger.info("DuckDuckGo text search: query=%s, max_results=%d", query, max_results)

    ddgs = DDGS()
    raw_results = list(ddgs.text(query, max_results=min(max_results, 10)))

    results = []
    for r in raw_results:
        results.append({
            "title": r.get("title", ""),
            "url": r.get("href", ""),
            "content": r.get("body", ""),
        })

    output = {
        "query": query,
        "results": results,
        "result_count": len(results),
        "searched_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("DuckDuckGo text search returned %d results for: %s", len(results), query)
    return json.dumps(output, indent=2)


@function_tool
def duckduckgo_news_search(
    ctx: RunContextWrapper[ResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Search recent news using DuckDuckGo News (free, no API key).

    Retrieves recent news articles matching the query. Useful for
    current events and trending topics.

    Args:
        ctx: Run context (unused but required by framework).
        query: The news search query string.
        max_results: Maximum number of results to return (1-10).

    Returns:
        str: JSON string with news results including title, url, date, and body.
    """
    logger.info("DuckDuckGo news search: query=%s, max_results=%d", query, max_results)

    ddgs = DDGS()
    raw_results = list(ddgs.news(query, max_results=min(max_results, 10)))

    results = []
    for r in raw_results:
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("body", ""),
            "date": r.get("date", ""),
            "source": r.get("source", ""),
        })

    output = {
        "query": query,
        "results": results,
        "result_count": len(results),
        "searched_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("DuckDuckGo news search returned %d results for: %s", len(results), query)
    return json.dumps(output, indent=2)
