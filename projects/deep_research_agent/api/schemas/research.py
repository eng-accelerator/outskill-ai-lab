"""Pydantic schemas for the Deep Research Agent API.

Defines request/response models and SSE event payloads for the
research pipeline endpoints.
"""

from typing import Literal

from pydantic import BaseModel, Field

RunStatus = Literal["pending", "running", "completed", "failed"]

PhaseType = Literal[
    "planning",
    "searching",
    "reading",
    "synthesizing",
    "writing",
    "completed",
]

SSEEventType = Literal[
    "phase_change",
    "agent_start",
    "agent_end",
    "tool_start",
    "tool_end",
    "handoff",
    "finding",
    "report",
    "done",
    "error",
]


class ResearchRequest(BaseModel):
    """Request body to start a new research run.

    Attributes:
        query: The user's research question.
    """

    query: str = Field(..., min_length=1, max_length=2000)


class ResearchRunResponse(BaseModel):
    """Response after initiating a research run.

    Attributes:
        run_id: Unique identifier for this research run.
        status: Current status of the run.
    """

    run_id: str
    status: RunStatus


class SourcePayload(BaseModel):
    """A discovered source sent via SSE.

    Attributes:
        url: Source URL.
        title: Source title.
        source_type: Category of source.
        snippet: Brief excerpt.
        relevance_score: Relevance to the query (0.0-1.0).
    """

    url: str
    title: str
    source_type: str
    snippet: str
    relevance_score: float = 0.0


class AgentEventPayload(BaseModel):
    """Agent lifecycle event payload.

    Attributes:
        agent_name: Name of the agent.
        detail: Optional detail string (tool name, target agent, etc.).
    """

    agent_name: str
    detail: str = ""


class PhaseChangePayload(BaseModel):
    """Phase transition event payload.

    Attributes:
        phase: The new active phase.
    """

    phase: PhaseType


class ReportPayload(BaseModel):
    """Final report payload.

    Attributes:
        content: The full research report text (markdown).
        sources: All sources referenced in the report.
    """

    content: str
    sources: list[SourcePayload] = Field(default_factory=list)


class ErrorPayload(BaseModel):
    """Error event payload.

    Attributes:
        message: Human-readable error message.
    """

    message: str


class ResearchResultResponse(BaseModel):
    """Response for fetching a completed research result.

    Attributes:
        run_id: Unique identifier for this research run.
        status: Current status of the run.
        query: The original research query.
        report: The final report content (empty if not yet completed).
        sources: Discovered sources.
    """

    run_id: str
    status: RunStatus
    query: str
    report: str = ""
    sources: list[SourcePayload] = Field(default_factory=list)
