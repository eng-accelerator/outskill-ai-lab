"""Data models for source tracking, credibility evaluation, and citations.

Defines the structured types for tracking research sources, evaluating
their credibility, and generating properly formatted citations.
"""

from dataclasses import dataclass
from typing import Literal

SourceType = Literal[
    "web",
    "academic",
    "news",
    "wikipedia",
    "reddit",
    "github",
    "stackexchange",
    "youtube",
]

CredibilityLevel = Literal["high", "medium", "low", "unknown"]


@dataclass(frozen=True)
class Source:
    """A retrieved source document or page.

    Attributes:
        url: The source URL.
        title: Title of the source.
        source_type: Type classification of the source.
        snippet: Brief excerpt or summary.
        retrieved_at: ISO timestamp when retrieved.
    """

    url: str
    title: str
    source_type: SourceType
    snippet: str
    retrieved_at: str


@dataclass(frozen=True)
class SourceCredibility:
    """Credibility evaluation for a source.

    Attributes:
        url: The evaluated source URL.
        credibility_level: Overall credibility classification.
        score: Numeric credibility score (0-100).
        reasons: Explanation of the credibility assessment.
    """

    url: str
    credibility_level: CredibilityLevel
    score: int
    reasons: str


@dataclass(frozen=True)
class Citation:
    """A formatted citation for a source.

    Attributes:
        url: The source URL.
        title: Title of the cited work.
        author: Author name(s) or 'Unknown'.
        date: Publication date or 'n.d.'.
        source_type: Type of source.
        accessed_at: ISO timestamp of access.
    """

    url: str
    title: str
    author: str
    date: str
    source_type: SourceType
    accessed_at: str
