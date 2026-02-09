"""Data models for research reports.

Defines the structured types for report sections, confidence scoring,
and the final research report output.
"""

from dataclasses import dataclass, field


@dataclass
class ReportSection:
    """A single section of the research report.

    Attributes:
        title: Section heading.
        content: Section body text.
        citations: List of source URLs cited in this section.
        order: Display order (1-based).
    """

    title: str
    content: str
    citations: list[str]
    order: int


@dataclass(frozen=True)
class ConfidenceScore:
    """Overall confidence assessment for the research findings.

    Attributes:
        score: Confidence score (0-100).
        total_sources: Number of sources consulted.
        agreeing_sources: Number of sources in agreement.
        factors: Explanation of confidence factors.
    """

    score: int
    total_sources: int
    agreeing_sources: int
    factors: str


@dataclass
class ResearchReport:
    """The final structured research report.

    Attributes:
        title: Report title.
        query: Original research query.
        executive_summary: High-level summary of findings.
        sections: Ordered report sections.
        bibliography: List of formatted citation strings.
        confidence: Overall confidence assessment.
        generated_at: ISO timestamp of report generation.
    """

    title: str
    query: str
    executive_summary: str
    sections: list[ReportSection] = field(default_factory=list)
    bibliography: list[str] = field(default_factory=list)
    confidence: ConfidenceScore | None = None
    generated_at: str = ""
