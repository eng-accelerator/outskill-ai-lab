"""Report generation tools.

Provides tools for formatting citations, structuring report sections,
compiling bibliographies, and generating report outlines.
"""

import json
import logging
from datetime import datetime, timezone

from agents import RunContextWrapper, function_tool

from deep_research_agent.models.research import ResearchContext

logger = logging.getLogger(__name__)


@function_tool
def generate_citation(
    ctx: RunContextWrapper[ResearchContext],
    url: str,
    title: str,
    author: str,
    date: str,
    source_type: str,
) -> str:
    """Generate a formatted citation in APA style.

    Creates a properly formatted citation string for use in the
    research report bibliography.

    Args:
        ctx: Run context (unused but required by framework).
        url: The source URL.
        title: Title of the cited work.
        author: Author name(s) or 'Unknown'.
        date: Publication date (any format) or 'n.d.' if unknown.
        source_type: Type of source ('web', 'academic', 'news', etc.).

    Returns:
        str: JSON string with the formatted citation.
    """
    logger.info("Generating citation for: %s", title)

    accessed = datetime.now(timezone.utc).strftime("%B %d, %Y")

    # Format APA-style citation
    author_str = author if author and author != "Unknown" else ""
    date_str = f"({date})" if date and date != "n.d." else "(n.d.)"

    match source_type:
        case "academic":
            citation = f"{author_str} {date_str}. {title}. Retrieved from {url}"
        case "news":
            citation = f"{author_str} {date_str}. {title}. Retrieved {accessed}, from {url}"
        case "wikipedia":
            citation = f"{title}. (n.d.). In Wikipedia. Retrieved {accessed}, from {url}"
        case _:
            citation = f"{author_str} {date_str}. {title}. Retrieved {accessed}, from {url}"

    # Clean up extra spaces
    citation = " ".join(citation.split())

    output = {
        "citation": citation,
        "url": url,
        "title": title,
        "author": author,
        "date": date,
        "source_type": source_type,
        "accessed_at": accessed,
    }

    logger.info("Citation generated for: %s", title[:50])
    return json.dumps(output, indent=2)


@function_tool
def format_report_section(
    ctx: RunContextWrapper[ResearchContext],
    title: str,
    content: str,
    citation_urls: str,
    order: int,
) -> str:
    """Format a single section of the research report.

    Structures content with proper heading, body text, and inline
    citation references.

    Args:
        ctx: Run context (unused but required by framework).
        title: Section heading.
        content: Section body text (markdown supported).
        citation_urls: Comma-separated URLs referenced in this section.
        order: Display order of this section (1-based).

    Returns:
        str: JSON string with the formatted section.
    """
    logger.info("Formatting report section: %s (order=%d)", title, order)

    urls = [u.strip() for u in citation_urls.split(",") if u.strip()]

    formatted = f"## {title}\n\n{content}"

    if urls:
        formatted += "\n\n**Sources:**\n"
        for i, u in enumerate(urls, 1):
            formatted += f"- [{i}] {u}\n"

    output = {
        "title": title,
        "content": content,
        "formatted": formatted,
        "citation_urls": urls,
        "order": order,
    }

    logger.info("Section formatted: %s (%d citations)", title, len(urls))
    return json.dumps(output, indent=2)


@function_tool
def compile_bibliography(
    ctx: RunContextWrapper[ResearchContext],
    citations_json: str,
) -> str:
    """Compile all citations into a formatted bibliography.

    Deduplicates and sorts citations alphabetically to produce
    the final bibliography section of the report.

    Args:
        ctx: Run context (unused but required by framework).
        citations_json: JSON string of citation objects with 'citation' and 'url' fields.

    Returns:
        str: JSON string with the compiled bibliography.
    """
    logger.info("Compiling bibliography")

    citations = json.loads(citations_json)

    # Deduplicate by URL
    seen_urls = set()
    unique = []
    for c in citations:
        url = c.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique.append(c)

    # Sort alphabetically by citation text
    unique.sort(key=lambda c: c.get("citation", "").lower())

    # Format as numbered list
    bib_entries = []
    for i, c in enumerate(unique, 1):
        bib_entries.append(f"[{i}] {c.get('citation', '')}")

    formatted_bibliography = "\n".join(bib_entries)

    output = {
        "entries": bib_entries,
        "formatted": f"## Bibliography\n\n{formatted_bibliography}",
        "total_citations": len(unique),
        "compiled_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Bibliography compiled: %d unique citations", len(unique))
    return json.dumps(output, indent=2)


@function_tool
def generate_report_outline(
    ctx: RunContextWrapper[ResearchContext],
    query: str,
    sub_questions_json: str,
    findings_count: int,
) -> str:
    """Generate a structured outline for the research report.

    Creates a logical section structure based on the research query,
    sub-questions, and the volume of findings.

    Args:
        ctx: Run context (unused but required by framework).
        query: The original research query.
        sub_questions_json: JSON string of sub-question objects.
        findings_count: Total number of research findings collected.

    Returns:
        str: JSON string with the recommended report structure.
    """
    logger.info("Generating report outline for: %s", query[:50])

    sub_questions = json.loads(sub_questions_json)

    sections = [
        {"title": "Executive Summary", "order": 1, "description": "High-level overview of findings and conclusions"},
    ]

    # Add a section for each sub-question group
    for i, sq in enumerate(sub_questions, 2):
        question = sq.get("question", f"Research Area {i}")
        sections.append({
            "title": question if len(question) < 60 else question[:57] + "...",
            "order": i,
            "description": f"Detailed findings for: {question}",
        })

    # Add analysis and conclusion sections
    next_order = len(sections) + 1
    sections.extend([
        {"title": "Analysis & Cross-References", "order": next_order, "description": "Synthesis of findings, agreements, and conflicts across sources"},
        {"title": "Confidence Assessment", "order": next_order + 1, "description": "Overall confidence score and methodology notes"},
        {"title": "Conclusion", "order": next_order + 2, "description": "Final summary and key takeaways"},
    ])

    output = {
        "query": query,
        "sections": sections,
        "total_sections": len(sections),
        "findings_count": findings_count,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Report outline generated: %d sections", len(sections))
    return json.dumps(output, indent=2)
