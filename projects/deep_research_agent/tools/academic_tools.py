"""Academic and knowledge search tools.

Provides access to Wikipedia, arXiv, and Semantic Scholar for
academic papers, encyclopedic knowledge, and citation data.
"""

import json
import logging
from datetime import datetime, timezone

import arxiv
import httpx
import wikipediaapi

from agents import RunContextWrapper, function_tool

from deep_research_agent.models.research import ResearchContext

logger = logging.getLogger(__name__)

_WIKI = wikipediaapi.Wikipedia(
    user_agent="DeepResearchAgent/1.0 (research@example.com)",
    language="en",
)

_SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"


@function_tool
def wikipedia_search(
    ctx: RunContextWrapper[ResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Search Wikipedia for articles matching the query.

    Returns article titles and summaries. Use wikipedia_get_page to
    retrieve full content for a specific article.

    Args:
        ctx: Run context (unused but required by framework).
        query: The search query.
        max_results: Maximum results to return (1-10).

    Returns:
        str: JSON string with matching Wikipedia article titles and summaries.
    """
    logger.info("Wikipedia search: query=%s", query)

    # Use the MediaWiki API search endpoint directly for better results
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": min(max_results, 10),
        "format": "json",
        "utf8": 1,
    }
    headers = {
        "User-Agent": "DeepResearchAgent/1.0 (research@example.com)",
    }

    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("query", {}).get("search", []):
        title = item.get("title", "")
        # Get summary via wikipedia-api
        page = _WIKI.page(title)
        summary = page.summary[:500] if page.exists() else item.get("snippet", "")

        results.append({
            "title": title,
            "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
            "summary": summary,
        })

    output = {
        "query": query,
        "results": results,
        "result_count": len(results),
        "searched_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Wikipedia search returned %d results for: %s", len(results), query)
    return json.dumps(output, indent=2)


@function_tool
def wikipedia_get_page(
    ctx: RunContextWrapper[ResearchContext],
    title: str,
) -> str:
    """Get the full content of a specific Wikipedia page.

    Retrieves the complete text content of a Wikipedia article.
    Use wikipedia_search first to find the correct title.

    Args:
        ctx: Run context (unused but required by framework).
        title: The exact Wikipedia article title.

    Returns:
        str: JSON string with the full article text (truncated to 5000 chars).
    """
    logger.info("Wikipedia get page: title=%s", title)

    page = _WIKI.page(title)

    if not page.exists():
        return json.dumps({"error": f"Wikipedia page '{title}' not found"})

    # Truncate very long articles to keep context manageable
    full_text = page.text
    truncated = len(full_text) > 5000
    content = full_text[:5000] if truncated else full_text

    output = {
        "title": page.title,
        "url": page.fullurl,
        "content": content,
        "truncated": truncated,
        "full_length": len(full_text),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Wikipedia page retrieved: %s (%d chars)", title, len(content))
    return json.dumps(output, indent=2)


@function_tool
def arxiv_search(
    ctx: RunContextWrapper[ResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Search arXiv for academic papers matching the query.

    Returns paper titles, abstracts, authors, and links. Useful for
    scientific and technical research topics.

    Args:
        ctx: Run context (unused but required by framework).
        query: The academic search query.
        max_results: Maximum papers to return (1-10).

    Returns:
        str: JSON string with paper details including title, abstract, authors, and URL.
    """
    logger.info("arXiv search: query=%s, max_results=%d", query, max_results)

    search = arxiv.Search(
        query=query,
        max_results=min(max_results, 10),
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results = []
    for paper in search.results():
        results.append({
            "title": paper.title,
            "url": paper.entry_id,
            "pdf_url": paper.pdf_url,
            "abstract": paper.summary[:500],
            "authors": [a.name for a in paper.authors[:5]],
            "published": paper.published.isoformat() if paper.published else "",
            "categories": paper.categories,
        })

    output = {
        "query": query,
        "results": results,
        "result_count": len(results),
        "searched_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("arXiv search returned %d results for: %s", len(results), query)
    return json.dumps(output, indent=2)


@function_tool
def semantic_scholar_search(
    ctx: RunContextWrapper[ResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Search Semantic Scholar for academic papers and their citation data.

    Returns papers with citation counts, influential citations, and
    links. Good for finding highly-cited and influential research.

    Args:
        ctx: Run context (unused but required by framework).
        query: The academic search query.
        max_results: Maximum papers to return (1-10).

    Returns:
        str: JSON string with papers including title, abstract, citation count, and URL.
    """
    logger.info("Semantic Scholar search: query=%s, max_results=%d", query, max_results)

    url = f"{_SEMANTIC_SCHOLAR_BASE}/paper/search"
    params = {
        "query": query,
        "limit": min(max_results, 10),
        "fields": "title,abstract,url,year,citationCount,authors,externalIds",
    }

    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for paper in data.get("data", []):
        abstract = paper.get("abstract") or ""
        results.append({
            "title": paper.get("title", ""),
            "url": paper.get("url", ""),
            "abstract": abstract[:500],
            "year": paper.get("year"),
            "citation_count": paper.get("citationCount", 0),
            "authors": [a.get("name", "") for a in (paper.get("authors") or [])[:5]],
            "paper_id": paper.get("paperId", ""),
        })

    output = {
        "query": query,
        "results": results,
        "result_count": len(results),
        "searched_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Semantic Scholar returned %d results for: %s", len(results), query)
    return json.dumps(output, indent=2)


@function_tool
def semantic_scholar_get_paper(
    ctx: RunContextWrapper[ResearchContext],
    paper_id: str,
) -> str:
    """Get detailed information about a specific paper from Semantic Scholar.

    Retrieves full details including abstract, references, and citations.
    Use semantic_scholar_search first to find the paper_id.

    Args:
        ctx: Run context (unused but required by framework).
        paper_id: The Semantic Scholar paper ID.

    Returns:
        str: JSON string with full paper details, references, and citations.
    """
    logger.info("Semantic Scholar get paper: paper_id=%s", paper_id)

    url = f"{_SEMANTIC_SCHOLAR_BASE}/paper/{paper_id}"
    params = {
        "fields": "title,abstract,url,year,citationCount,referenceCount,authors,references.title,references.url,citations.title,citations.url",
    }

    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    abstract = data.get("abstract") or ""
    references = [
        {"title": r.get("title", ""), "url": r.get("url", "")}
        for r in (data.get("references") or [])[:10]
    ]
    citations = [
        {"title": c.get("title", ""), "url": c.get("url", "")}
        for c in (data.get("citations") or [])[:10]
    ]

    output = {
        "paper_id": paper_id,
        "title": data.get("title", ""),
        "abstract": abstract[:1000],
        "url": data.get("url", ""),
        "year": data.get("year"),
        "citation_count": data.get("citationCount", 0),
        "reference_count": data.get("referenceCount", 0),
        "authors": [a.get("name", "") for a in (data.get("authors") or [])[:10]],
        "top_references": references,
        "top_citations": citations,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Semantic Scholar paper retrieved: %s", data.get("title", paper_id))
    return json.dumps(output, indent=2)
