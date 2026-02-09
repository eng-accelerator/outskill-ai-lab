"""Data models for research planning and findings.

Defines the structured types for research plans, sub-questions,
findings, and the shared research context passed through the pipeline.
"""

from dataclasses import dataclass, field
from typing import Literal

QueryType = Literal[
    "factual",
    "comparison",
    "analysis",
    "current_events",
    "technical",
    "general",
]

SourceTypeHint = Literal[
    "web",
    "academic",
    "news",
    "wikipedia",
    "reddit",
    "github",
    "stackexchange",
    "youtube",
]


@dataclass(frozen=True)
class SubQuestion:
    """A single sub-question decomposed from the main research query.

    Attributes:
        question: The sub-question text.
        priority: Priority level (1=highest).
        source_types: Suggested source types to search.
        answered: Whether this sub-question has been answered.
    """

    question: str
    priority: int
    source_types: list[SourceTypeHint]
    answered: bool = False


@dataclass
class ResearchPlan:
    """A structured plan for conducting research on a query.

    Attributes:
        query: The original research query.
        query_type: Classification of the query type.
        sub_questions: Decomposed sub-questions to investigate.
        search_strategy: High-level approach description.
        depth: Research depth ('shallow', 'moderate', 'deep').
    """

    query: str
    query_type: QueryType
    sub_questions: list[SubQuestion]
    search_strategy: str
    depth: Literal["shallow", "moderate", "deep"] = "moderate"


@dataclass(frozen=True)
class ResearchFinding:
    """A single research finding from any source.

    Attributes:
        source_url: URL of the source.
        title: Title of the source content.
        content_snippet: Relevant excerpt from the source.
        relevance_score: How relevant this finding is (0.0-1.0).
        finding_type: Type of source that produced this finding.
    """

    source_url: str
    title: str
    content_snippet: str
    relevance_score: float
    finding_type: SourceTypeHint


@dataclass
class ResearchContext:
    """Shared context object passed through the agent pipeline via RunContextWrapper.

    Accumulates findings, sources, and citations as agents work.

    Attributes:
        query: The original user research query.
        config: API keys and model settings.
        research_plan: The generated research plan (populated by planner).
        findings: Accumulated research findings from all searchers.
        raw_contents: URL -> extracted content mapping for deep reads.
    """

    query: str
    config: dict[str, str | None]
    research_plan: ResearchPlan | None = None
    findings: list[ResearchFinding] = field(default_factory=list)
    raw_contents: dict[str, str] = field(default_factory=dict)
