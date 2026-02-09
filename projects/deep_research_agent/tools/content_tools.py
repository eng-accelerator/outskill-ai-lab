"""Content extraction tools for deep page reading.

Provides capabilities to extract clean text content from web pages
using Jina Reader API, direct scraping with BeautifulSoup, and
YouTube transcript extraction.
"""

import json
import logging
import re
from datetime import datetime, timezone

import httpx
from agents import RunContextWrapper, function_tool
from bs4 import BeautifulSoup
from deep_research_agent.models.research import ResearchContext
from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger(__name__)


@function_tool
def jina_read_url(
    ctx: RunContextWrapper[ResearchContext],
    url: str,
) -> str:
    """Extract clean markdown content from a URL using Jina Reader API.

    Jina Reader converts any web page into clean, readable markdown.
    Best for articles, blog posts, and documentation pages.

    Args:
        ctx: Run context for storing extracted content.
        url: The URL to extract content from.

    Returns:
        str: JSON string with extracted markdown content (truncated to 5000 chars).
    """
    logger.info("Jina Reader extracting: %s", url)

    jina_url = f"https://r.jina.ai/{url}"
    headers = {"Accept": "text/markdown"}

    with httpx.Client(timeout=30) as client:
        resp = client.get(jina_url, headers=headers)
        resp.raise_for_status()
        content = resp.text

    # Truncate if very long
    truncated = len(content) > 5000
    extracted = content[:5000] if truncated else content

    # Store in context for later use
    ctx.context.raw_contents[url] = extracted

    output = {
        "url": url,
        "content": extracted,
        "truncated": truncated,
        "full_length": len(content),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Jina Reader extracted %d chars from: %s", len(extracted), url)
    return json.dumps(output, indent=2)


@function_tool
def scrape_webpage(
    ctx: RunContextWrapper[ResearchContext],
    url: str,
) -> str:
    """Scrape and extract text content from a web page using BeautifulSoup.

    Direct HTML scraping as a fallback when Jina Reader is unavailable
    or for pages that need specific parsing. Extracts text from
    paragraphs, headings, and list items.

    Args:
        ctx: Run context for storing extracted content.
        url: The URL to scrape.

    Returns:
        str: JSON string with extracted text content (truncated to 5000 chars).
    """
    logger.info("Scraping webpage: %s", url)

    headers = {
        "User-Agent": "Mozilla/5.0 (DeepResearchAgent/1.0; Research Bot)",
    }

    with httpx.Client(timeout=20, follow_redirects=True) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, nav, footer elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Extract title
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Extract main content from paragraphs, headings, list items
    content_parts = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        text = tag.get_text(strip=True)
        if len(text) > 20:  # Skip very short fragments
            prefix = f"## " if tag.name.startswith("h") else ""
            content_parts.append(f"{prefix}{text}")

    content = "\n\n".join(content_parts)

    # Clean up excessive whitespace
    content = re.sub(r"\n{3,}", "\n\n", content)

    truncated = len(content) > 5000
    extracted = content[:5000] if truncated else content

    ctx.context.raw_contents[url] = extracted

    output = {
        "url": url,
        "title": title,
        "content": extracted,
        "truncated": truncated,
        "full_length": len(content),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Scraped %d chars from: %s", len(extracted), url)
    return json.dumps(output, indent=2)


def _extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats.

    Args:
        url: A YouTube URL in any common format.

    Returns:
        str | None: The video ID, or None if not found.
    """
    patterns = [
        r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
        r"(?:shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


@function_tool
def youtube_get_transcript(
    ctx: RunContextWrapper[ResearchContext],
    video_url: str,
) -> str:
    """Get the transcript of a YouTube video.

    Extracts the auto-generated or manual transcript from a YouTube
    video. Useful for researching video content, lectures, and talks.

    Args:
        ctx: Run context for storing extracted content.
        video_url: The YouTube video URL.

    Returns:
        str: JSON string with the video transcript text (truncated to 5000 chars).
    """
    logger.info("YouTube transcript: %s", video_url)

    video_id = _extract_video_id(video_url)
    if not video_id:
        return json.dumps({"error": f"Could not extract video ID from: {video_url}"})

    ytt_api = YouTubeTranscriptApi()
    transcript_data = ytt_api.fetch(video_id)

    # Combine all transcript segments
    full_text = " ".join(snippet.text for snippet in transcript_data.snippets)

    truncated = len(full_text) > 5000
    content = full_text[:5000] if truncated else full_text

    ctx.context.raw_contents[video_url] = content

    output = {
        "video_url": video_url,
        "video_id": video_id,
        "transcript": content,
        "truncated": truncated,
        "full_length": len(full_text),
        "segment_count": len(transcript_data.snippets),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "YouTube transcript extracted: %d chars from video %s", len(content), video_id
    )
    return json.dumps(output, indent=2)
