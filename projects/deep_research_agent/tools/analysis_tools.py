"""Analysis tools for source evaluation and research synthesis.

Provides local computation tools for evaluating source credibility,
extracting claims, cross-referencing findings, identifying knowledge
gaps, and calculating confidence scores.
"""

import json
import logging
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from agents import RunContextWrapper, function_tool
from deep_research_agent.models.research import ResearchContext

logger = logging.getLogger(__name__)

# Domain credibility tiers (well-known sources)
_HIGH_CREDIBILITY_DOMAINS = {
    "wikipedia.org",
    "arxiv.org",
    "nature.com",
    "science.org",
    "ieee.org",
    "acm.org",
    "nih.gov",
    "gov",
    "edu",
    "bbc.com",
    "reuters.com",
    "apnews.com",
    "nytimes.com",
    "washingtonpost.com",
    "theguardian.com",
    "github.com",
    "stackoverflow.com",
    "semanticscholar.org",
}

_MEDIUM_CREDIBILITY_DOMAINS = {
    "medium.com",
    "substack.com",
    "dev.to",
    "hackernews.com",
    "reddit.com",
    "quora.com",
    "youtube.com",
    "techcrunch.com",
    "theverge.com",
    "arstechnica.com",
    "wired.com",
}


@function_tool
def evaluate_source_credibility(
    ctx: RunContextWrapper[ResearchContext],
    url: str,
    title: str,
    content_snippet: str,
) -> str:
    """Evaluate the credibility of a source based on its URL and content.

    Uses domain reputation, content quality signals, and structural
    analysis to assign a credibility score.

    Args:
        ctx: Run context (unused but required by framework).
        url: The source URL.
        title: The source title.
        content_snippet: A snippet of the source's content.

    Returns:
        str: JSON string with credibility level, score (0-100), and reasons.
    """
    logger.info("Evaluating credibility: %s", url)

    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")

    score = 50  # Base score
    reasons = []

    # Domain-based scoring
    if any(d in domain for d in _HIGH_CREDIBILITY_DOMAINS):
        score += 30
        reasons.append(f"High-credibility domain: {domain}")
    elif any(d in domain for d in _MEDIUM_CREDIBILITY_DOMAINS):
        score += 15
        reasons.append(f"Medium-credibility domain: {domain}")
    else:
        reasons.append(f"Unknown domain credibility: {domain}")

    # HTTPS check
    if parsed.scheme == "https":
        score += 5
        reasons.append("Uses HTTPS")

    # Content quality signals
    if len(content_snippet) > 200:
        score += 5
        reasons.append("Substantial content length")

    if title and len(title) > 10:
        score += 5
        reasons.append("Has descriptive title")

    # Check for citation-like patterns in content
    citation_patterns = [r"\[\d+\]", r"\(\d{4}\)", r"et al\.", r"doi:", r"ISBN"]
    has_citations = any(re.search(p, content_snippet) for p in citation_patterns)
    if has_citations:
        score += 10
        reasons.append("Content contains citations/references")

    # Clamp score
    score = max(0, min(100, score))

    # Determine level
    if score >= 75:
        level = "high"
    elif score >= 50:
        level = "medium"
    elif score >= 25:
        level = "low"
    else:
        level = "unknown"

    output = {
        "url": url,
        "domain": domain,
        "credibility_level": level,
        "score": score,
        "reasons": reasons,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Credibility for %s: %s (score=%d)", domain, level, score)
    return json.dumps(output, indent=2)


@function_tool
def extract_key_claims(
    ctx: RunContextWrapper[ResearchContext],
    text: str,
    source_url: str,
) -> str:
    """Extract factual claims and key statements from a text.

    Identifies sentences that contain factual assertions, statistics,
    dates, or notable claims that can be cross-referenced.

    Args:
        ctx: Run context (unused but required by framework).
        text: The text to extract claims from.
        source_url: URL of the source for attribution.

    Returns:
        str: JSON string with a list of extracted claims.
    """
    logger.info("Extracting claims from source: %s", source_url)

    sentences = re.split(r"(?<=[.!?])\s+", text)
    claims = []

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:
            continue

        # Heuristic: sentences with numbers, dates, or assertive patterns
        has_number = bool(re.search(r"\d+", sentence))
        has_date = bool(re.search(r"\b(19|20)\d{2}\b", sentence))
        has_percentage = bool(re.search(r"\d+%", sentence))
        has_comparison = any(
            w in sentence.lower()
            for w in [
                "more than",
                "less than",
                "greater",
                "higher",
                "lower",
                "increased",
                "decreased",
                "according to",
                "found that",
                "showed that",
                "demonstrated",
                "reported",
            ]
        )

        claim_score = sum([has_number, has_date, has_percentage, has_comparison])

        if claim_score >= 1:
            claims.append(
                {
                    "claim": sentence[:300],
                    "has_statistics": has_number or has_percentage,
                    "has_date": has_date,
                    "has_attribution": has_comparison,
                    "strength": "strong" if claim_score >= 2 else "moderate",
                    "source_url": source_url,
                }
            )

    # Limit to top 10 most notable claims
    claims = sorted(claims, key=lambda c: c["strength"] == "strong", reverse=True)[:10]

    output = {
        "source_url": source_url,
        "claims": claims,
        "claim_count": len(claims),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Extracted %d claims from: %s", len(claims), source_url)
    return json.dumps(output, indent=2)


@function_tool
def cross_reference_findings(
    ctx: RunContextWrapper[ResearchContext],
    claim: str,
    sources_json: str,
) -> str:
    """Cross-reference a claim against multiple source snippets.

    Checks whether multiple sources agree, disagree, or are neutral
    on a specific claim. Helps identify consensus and conflicts.

    Args:
        ctx: Run context (unused but required by framework).
        claim: The claim to cross-reference.
        sources_json: JSON string of source objects with 'url' and 'content' fields.

    Returns:
        str: JSON string with agreement analysis across sources.
    """
    logger.info("Cross-referencing claim: %s", claim[:80])

    sources = json.loads(sources_json)

    # Simple keyword overlap analysis
    claim_words = set(re.findall(r"\b\w{4,}\b", claim.lower()))

    analysis = []
    for source in sources:
        content = source.get("content", "").lower()
        source_words = set(re.findall(r"\b\w{4,}\b", content))

        overlap = claim_words & source_words
        overlap_ratio = len(overlap) / max(len(claim_words), 1)

        if overlap_ratio > 0.5:
            stance = "supporting"
        elif overlap_ratio > 0.2:
            stance = "neutral"
        else:
            stance = "unrelated"

        analysis.append(
            {
                "source_url": source.get("url", ""),
                "stance": stance,
                "overlap_ratio": round(overlap_ratio, 2),
                "matching_terms": list(overlap)[:10],
            }
        )

    supporting = sum(1 for a in analysis if a["stance"] == "supporting")
    neutral = sum(1 for a in analysis if a["stance"] == "neutral")

    output = {
        "claim": claim[:200],
        "source_analysis": analysis,
        "summary": {
            "total_sources": len(analysis),
            "supporting": supporting,
            "neutral": neutral,
            "unrelated": len(analysis) - supporting - neutral,
            "consensus": (
                "strong"
                if supporting >= 2
                else "moderate" if supporting >= 1 else "weak"
            ),
        },
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Cross-reference: %d supporting, %d neutral for claim", supporting, neutral
    )
    return json.dumps(output, indent=2)


@function_tool
def identify_knowledge_gaps(
    ctx: RunContextWrapper[ResearchContext],
    sub_questions_json: str,
    findings_summary: str,
) -> str:
    """Identify unanswered sub-questions and knowledge gaps.

    Compares the research plan's sub-questions against the findings
    summary to determine what has been answered and what remains.

    Args:
        ctx: Run context (unused but required by framework).
        sub_questions_json: JSON string of sub-question objects with 'question' field.
        findings_summary: A text summary of all findings so far.

    Returns:
        str: JSON string with answered/unanswered questions and gap analysis.
    """
    logger.info("Identifying knowledge gaps")

    sub_questions = json.loads(sub_questions_json)
    findings_lower = findings_summary.lower()

    analysis = []
    for sq in sub_questions:
        question = sq.get("question", "")
        q_words = set(re.findall(r"\b\w{4,}\b", question.lower()))
        f_words = set(re.findall(r"\b\w{4,}\b", findings_lower))

        overlap = q_words & f_words
        coverage = len(overlap) / max(len(q_words), 1)

        analysis.append(
            {
                "question": question,
                "coverage": round(coverage, 2),
                "likely_answered": coverage > 0.4,
                "matching_terms": list(overlap)[:5],
            }
        )

    answered = sum(1 for a in analysis if a["likely_answered"])
    unanswered = len(analysis) - answered

    output = {
        "questions": analysis,
        "summary": {
            "total_questions": len(analysis),
            "answered": answered,
            "unanswered": unanswered,
            "completion_pct": round(answered / max(len(analysis), 1) * 100),
        },
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Knowledge gaps: %d/%d questions answered", answered, len(analysis))
    return json.dumps(output, indent=2)


@function_tool
def calculate_confidence_score(
    ctx: RunContextWrapper[ResearchContext],
    total_sources: int,
    high_credibility_count: int,
    agreeing_sources: int,
    coverage_pct: int,
) -> str:
    """Calculate an overall confidence score for the research findings.

    Considers source count, credibility distribution, agreement level,
    and topic coverage to produce a 0-100 confidence score.

    Args:
        ctx: Run context (unused but required by framework).
        total_sources: Total number of sources consulted.
        high_credibility_count: Number of high-credibility sources.
        agreeing_sources: Number of sources in agreement on key claims.
        coverage_pct: Percentage of sub-questions covered (0-100).

    Returns:
        str: JSON string with confidence score and contributing factors.
    """
    logger.info(
        "Calculating confidence: sources=%d, high_cred=%d, agreeing=%d, coverage=%d%%",
        total_sources,
        high_credibility_count,
        agreeing_sources,
        coverage_pct,
    )

    factors = []
    score = 0.0

    # Source quantity (0-25 points)
    source_score = min(total_sources * 5, 25)
    score += source_score
    factors.append(f"Source quantity: {source_score}/25 ({total_sources} sources)")

    # Source quality (0-25 points)
    quality_ratio = high_credibility_count / max(total_sources, 1)
    quality_score = quality_ratio * 25
    score += quality_score
    factors.append(
        f"Source quality: {quality_score:.0f}/25 ({high_credibility_count} high-credibility)"
    )

    # Agreement (0-25 points)
    agree_ratio = agreeing_sources / max(total_sources, 1)
    agree_score = agree_ratio * 25
    score += agree_score
    factors.append(
        f"Source agreement: {agree_score:.0f}/25 ({agreeing_sources} agreeing)"
    )

    # Coverage (0-25 points)
    coverage_score = coverage_pct * 0.25
    score += coverage_score
    factors.append(f"Topic coverage: {coverage_score:.0f}/25 ({coverage_pct}% covered)")

    final_score = max(0, min(100, round(score)))

    if final_score >= 80:
        level = "high"
    elif final_score >= 60:
        level = "moderate"
    elif final_score >= 40:
        level = "low"
    else:
        level = "very_low"

    output = {
        "confidence_score": final_score,
        "confidence_level": level,
        "factors": factors,
        "total_sources": total_sources,
        "high_credibility_count": high_credibility_count,
        "agreeing_sources": agreeing_sources,
        "coverage_pct": coverage_pct,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("Confidence score: %d (%s)", final_score, level)
    return json.dumps(output, indent=2)
