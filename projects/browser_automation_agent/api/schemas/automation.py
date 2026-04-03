"""Pydantic schemas for the Browser Automation Agent API.

Defines request/response models and SSE event payloads for the
browser automation pipeline endpoints.
"""

from typing import Literal

from pydantic import BaseModel, Field

RunStatus = Literal["pending", "running", "completed", "failed"]

PhaseType = Literal[
    "planning",
    "navigating",
    "interacting",
    "extracting",
    "validating",
    "reporting",
    "completed",
]


class AutomationRequest(BaseModel):
    """Request body to start a browser automation run.

    Attributes:
        task: The automation task description.
        scenario: Optional predefined scenario key.
    """

    task: str = Field(..., min_length=1, max_length=2000)
    scenario: str | None = None


class AutomationRunResponse(BaseModel):
    """Response after initiating an automation run.

    Attributes:
        run_id: Unique identifier for this run.
        status: Current status of the run.
    """

    run_id: str
    status: RunStatus


class ScenarioInfo(BaseModel):
    """Info about a predefined automation scenario.

    Attributes:
        key: Scenario key.
        name: Human-readable name.
        task: The task description.
    """

    key: str
    name: str
    task: str


class StepPayload(BaseModel):
    """A single automation step event.

    Attributes:
        step_number: Step ordinal.
        action: Action type.
        instruction: What the step does.
        status: Step completion status.
    """

    step_number: int
    action: str
    instruction: str
    status: str = "running"


class AutomationResultResponse(BaseModel):
    """Response for fetching a completed automation result.

    Attributes:
        run_id: Unique identifier.
        status: Current run status.
        task: The original task.
        report: Final report content.
        urls_visited: URLs navigated during the run.
        steps_completed: Number of completed steps.
        total_steps: Total planned steps.
    """

    run_id: str
    status: RunStatus
    task: str
    report: str = ""
    urls_visited: list[str] = Field(default_factory=list)
    steps_completed: int = 0
    total_steps: int = 0
