"""Data models for extraction results and final reports.

Defines the structured types for data extracted from pages
and the final automation report produced by the pipeline.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExtractionResult:
    """Structured data extracted from a web page.

    Attributes:
        url: The page URL the data was extracted from.
        instruction: The extraction instruction used.
        data: The extracted data as a JSON string.
        schema_used: Whether a JSON schema was provided for extraction.
    """

    url: str
    instruction: str
    data: str
    schema_used: bool = False


@dataclass
class AutomationReport:
    """Final report summarizing the browser automation session.

    Attributes:
        task: The original user task description.
        steps_completed: Number of steps successfully executed.
        total_steps: Total number of planned steps.
        extractions: List of extraction results from the session.
        success: Overall success status of the automation.
        summary: Human-readable summary of results.
        urls_visited: List of URLs that were navigated to.
    """

    task: str
    steps_completed: int = 0
    total_steps: int = 0
    extractions: list[ExtractionResult] = field(default_factory=list)
    success: bool = False
    summary: str = ""
    urls_visited: list[str] = field(default_factory=list)
