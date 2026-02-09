from typing import List, Optional

from agents import function_tool
from tavily import TavilyClient


# Global client instance (lazy loaded)
_tavily_client = None


def get_tavily_client() -> TavilyClient:
    """Get or create Tavily client instance."""
    global _tavily_client
    if _tavily_client is None:
        from deep_research_agent.utils.config import load_config

        config = load_config()
        api_key = config.get("tavily_api_key")
        if not api_key:
            raise ValueError(
                "TAVILY_API_KEY not found in configuration. "
                "Please add it to your .env file."
            )
        _tavily_client = TavilyClient(api_key)
    return _tavily_client


@function_tool
def tavily_search(
    query: str, topic: str = "general", time_range: str = None, max_results: int = 2
) -> str:
    """
    Search the web using Tavily API.

    Args:
        query: The search query string
        topic: Search topic type - "general" or "news" (default: "general")
        time_range: Filter by time - "day", "week", "month", or None for all time
        max_results: Maximum number of results to return (default: 2)

    Returns:
        JSON string containing search results with titles, URLs, content snippets, and scores.
        Each result includes: title, url, content (snippet), score, published_date.

    Example:
        tavily_search("latest AI research", topic="news", time_range="week")
    """
    client = get_tavily_client()

    # Build search parameters with configs from tavily_provider
    search_params = {
        "topic": topic,
        "auto_parameters": True,
        "search_depth": "basic",
    }
    if time_range:
        search_params["time_range"] = time_range

    # Perform search
    response = client.search(query, **search_params)

    # Convert to output format
    output = []
    for r in response.get("results", [])[:max_results]:
        result_dict = {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0.0),
        }
        if r.get("published_date"):
            result_dict["published_date"] = r["published_date"]
        output.append(result_dict)

    return str(output)


@function_tool
def tavily_extract(urls: List[str]) -> str:
    """
    Extract full content from URLs using Tavily Extract API.

    Use this tool AFTER tavily_search to get complete article content.
    Tavily search returns only snippets; use this to get full text.
    Content is automatically truncated to prevent context overflow.

    Args:
        urls: List of URLs to extract content from

    Returns:
        JSON string containing extracted content for each URL.
        Each result includes: url, title, raw_content (truncated to 5000 chars), success (bool).
        If success=False, extraction failed for that URL.

    Example:
        tavily_extract(["https://example.com/article1", "https://example.com/article2"])
    """
    if not urls:
        return str([])

    client = get_tavily_client()

    # Call Tavily extract API
    response = client.extract(urls)

    # Convert to output format with truncation
    MAX_CONTENT_LENGTH = 5000
    output = []

    # Process successful extractions
    for r in response.get("results", []):
        content = r.get("raw_content", "")
        # Truncate long content to prevent context overflow
        if len(content) > MAX_CONTENT_LENGTH:
            content = (
                content[:MAX_CONTENT_LENGTH]
                + f"\n\n[Content truncated. Original length: {len(content)} chars]"
            )

        output.append(
            {
                "url": r["url"],
                "title": r.get("title", ""),
                "raw_content": content,
                "success": True,
            }
        )

    # Process failed extractions
    for r in response.get("failed_results", []):
        output.append(
            {
                "url": r["url"],
                "title": "",
                "raw_content": "",
                "success": False,
            }
        )

    return str(output)


def create_tavily_tools() -> List:
    """
    Create all Tavily tools for agent use.

    Returns:
        List of Tavily tool functions
    """
    return [tavily_search, tavily_extract]
