"""News and discussion search tools.

Provides access to Google News (via RSS) and Reddit discussions
for current events and community insights.
"""

import json
import logging
from datetime import datetime, timezone

import feedparser
import httpx

from agents import RunContextWrapper, function_tool

from deep_research_agent.models.research import ResearchContext

logger = logging.getLogger(__name__)


@function_tool
def google_news_rss(
    ctx: RunContextWrapper[ResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Search Google News via RSS feed (free, no API key required).

    Retrieves recent news headlines and links matching the query.
    Good for current events and breaking news.

    Args:
        ctx: Run context (unused but required by framework).
        query: The news search query.
        max_results: Maximum number of results (1-10).

    Returns:
        str: JSON string with news headlines, URLs, and publication dates.
    """
    logger.info("Google News RSS: query=%s, max_results=%d", query, max_results)

    encoded_query = query.replace(" ", "+")
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    feed = feedparser.parse(rss_url)

    results = []
    for entry in feed.entries[:min(max_results, 10)]:
        results.append({
            "title": entry.get("title", ""),
            "url": entry.get("link", ""),
            "published": entry.get("published", ""),
            "source": entry.get("source", {}).get("title", "") if isinstance(entry.get("source"), dict) else "",
        })

    output = {
        "query": query,
        "results": results,
        "result_count": len(results),
        "searched_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Google News RSS returned %d results for: %s", len(results), query)
    return json.dumps(output, indent=2)


@function_tool
def reddit_search(
    ctx: RunContextWrapper[ResearchContext],
    query: str,
    subreddit: str = "",
    max_results: int = 5,
) -> str:
    """Search Reddit discussions (free, via public JSON API).

    Finds relevant Reddit posts and discussions. Useful for getting
    community perspectives, experiences, and opinions on a topic.

    Args:
        ctx: Run context (unused but required by framework).
        query: The search query.
        subreddit: Optional subreddit to search within (e.g., 'technology').
        max_results: Maximum number of results (1-10).

    Returns:
        str: JSON string with Reddit posts including title, URL, score, and comments.
    """
    logger.info("Reddit search: query=%s, subreddit=%s", query, subreddit)

    if subreddit:
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {"q": query, "limit": min(max_results, 10), "sort": "relevance", "restrict_sr": "on"}
    else:
        url = "https://www.reddit.com/search.json"
        params = {"q": query, "limit": min(max_results, 10), "sort": "relevance"}

    headers = {"User-Agent": "DeepResearchAgent/1.0"}

    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for child in data.get("data", {}).get("children", []):
        post = child.get("data", {})
        results.append({
            "title": post.get("title", ""),
            "url": f"https://www.reddit.com{post.get('permalink', '')}",
            "subreddit": post.get("subreddit", ""),
            "score": post.get("score", 0),
            "num_comments": post.get("num_comments", 0),
            "selftext": (post.get("selftext") or "")[:500],
            "created_utc": post.get("created_utc", 0),
        })

    output = {
        "query": query,
        "subreddit": subreddit or "all",
        "results": results,
        "result_count": len(results),
        "searched_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Reddit search returned %d results for: %s", len(results), query)
    return json.dumps(output, indent=2)
