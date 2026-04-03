"""Pydantic schemas for the Customer Support Agent API.

Defines request/response models and phase types for the support
pipeline endpoints and SSE payloads.
"""

from typing import Literal

from pydantic import BaseModel, Field

from customer_support_agent.simulators.scenario_engine import ScenarioType

RunStatus = Literal["pending", "running", "completed", "failed"]

PhaseType = Literal[
    "intake",
    "order_support",
    "billing_support",
    "technical_support",
    "escalation",
    "resolution",
    "completed",
]


class SupportRequest(BaseModel):
    """Request body to start a new customer support run.

    Attributes:
        scenario_type: Which simulated scenario to generate and run.
    """

    scenario_type: ScenarioType


class SupportRunResponse(BaseModel):
    """Response after initiating a support run.

    Attributes:
        run_id: Unique identifier for this run.
        status: Current status of the run.
    """

    run_id: str
    status: RunStatus


class ScenarioInfo(BaseModel):
    """Metadata for one available support scenario.

    Attributes:
        scenario_type: Scenario identifier.
        description: Human-readable description of the scenario.
    """

    scenario_type: ScenarioType
    description: str


class SupportResultResponse(BaseModel):
    """Response for fetching a support run result.

    Attributes:
        run_id: Unique identifier for this run.
        status: Current run status.
        scenario_type: The scenario that was simulated.
        report: Final resolution output (empty until completed).
    """

    run_id: str
    status: RunStatus
    scenario_type: ScenarioType
    report: str = Field(default="")
