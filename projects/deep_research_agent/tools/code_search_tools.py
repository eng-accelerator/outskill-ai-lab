"""Code and technical search tools.

Provides access to GitHub repository search and StackExchange Q&A
for technical research, code discovery, and developer knowledge.
"""

import json
import logging
from datetime import datetime, timezone

import httpx

from agents import RunContextWrapper, function_tool

from deep_research_agent.models.research import ResearchContext

logger = logging.getLogger(__name__)


@function_tool
def github_search_repos(
    ctx: RunContextWrapper[ResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Search GitHub repositories matching the query (free, no API key).

    Finds open-source repositories by name, description, or topic.
    Useful for finding implementations, libraries, and tools.

    Args:
        ctx: Run context (unused but required by framework).
        query: The search query (supports GitHub search syntax).
        max_results: Maximum repositories to return (1-10).

    Returns:
        str: JSON string with repos including name, description, stars, and URL.
    """
    logger.info("GitHub search: query=%s, max_results=%d", query, max_results)

    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "per_page": min(max_results, 10),
        "sort": "stars",
        "order": "desc",
    }
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DeepResearchAgent/1.0",
    }

    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for repo in data.get("items", []):
        results.append({
            "name": repo.get("full_name", ""),
            "url": repo.get("html_url", ""),
            "description": (repo.get("description") or "")[:300],
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "language": repo.get("language", ""),
            "topics": repo.get("topics", [])[:5],
            "updated_at": repo.get("updated_at", ""),
        })

    output = {
        "query": query,
        "results": results,
        "result_count": len(results),
        "total_count": data.get("total_count", 0),
        "searched_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("GitHub search returned %d results for: %s", len(results), query)
    return json.dumps(output, indent=2)


@function_tool
def stackexchange_search(
    ctx: RunContextWrapper[ResearchContext],
    query: str,
    site: str = "stackoverflow",
    max_results: int = 5,
) -> str:
    """Search StackExchange sites for Q&A (free, no API key needed).

    Searches StackOverflow and other StackExchange sites for
    answered questions. Good for technical solutions and explanations.

    Args:
        ctx: Run context (unused but required by framework).
        query: The search query.
        site: StackExchange site to search ('stackoverflow', 'serverfault', 'superuser', etc.).
        max_results: Maximum questions to return (1-10).

    Returns:
        str: JSON string with questions including title, URL, score, and answer count.
    """
    logger.info("StackExchange search: query=%s, site=%s", query, site)

    url = "https://api.stackexchange.com/2.3/search/advanced"
    params = {
        "q": query,
        "site": site,
        "pagesize": min(max_results, 10),
        "order": "desc",
        "sort": "relevance",
        "filter": "withbody",
        "answers": 1,  # Only questions with answers
    }

    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("items", []):
        # Clean HTML from body
        body = item.get("body", "")
        # Simple HTML tag removal for preview
        import re
        body_clean = re.sub(r"<[^>]+>", "", body)[:500]

        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "score": item.get("score", 0),
            "answer_count": item.get("answer_count", 0),
            "is_answered": item.get("is_answered", False),
            "body_preview": body_clean,
            "tags": item.get("tags", [])[:5],
            "creation_date": item.get("creation_date", 0),
        })

    output = {
        "query": query,
        "site": site,
        "results": results,
        "result_count": len(results),
        "has_more": data.get("has_more", False),
        "searched_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("StackExchange search returned %d results for: %s", len(results), query)
    return json.dumps(output, indent=2)
