"""Pydantic schemas for the AI Ops Incident Response Agent API.

Defines request/response models and phase types for incident pipeline
endpoints and SSE payloads.
"""

from typing import Literal

from pydantic import BaseModel, Field

from aiops_incident_response_agent.simulators.scenario_engine import ScenarioType

RunStatus = Literal["pending", "running", "completed", "failed"]

PhaseType = Literal[
    "triage",
    "log_analysis",
    "metrics_analysis",
    "root_cause_analysis",
    "remediation",
    "reporting",
    "completed",
]


class IncidentRequest(BaseModel):
    """Request body to start a new incident response run.

    Attributes:
        scenario_type: Which simulated incident scenario to generate and run.
    """

    scenario_type: ScenarioType


class IncidentRunResponse(BaseModel):
    """Response after initiating an incident run.

    Attributes:
        run_id: Unique identifier for this run.
        status: Current status of the run.
    """

    run_id: str
    status: RunStatus


class ScenarioInfo(BaseModel):
    """Metadata for one available incident scenario.

    Attributes:
        scenario_type: Scenario identifier.
        description: Human-readable description of the scenario.
    """

    scenario_type: ScenarioType
    description: str


class IncidentResultResponse(BaseModel):
    """Response for fetching an incident run result.

    Attributes:
        run_id: Unique identifier for this run.
        status: Current run status.
        scenario_type: The scenario that was simulated.
        report: Final incident report output (empty until completed).
    """

    run_id: str
    status: RunStatus
    scenario_type: ScenarioType
    report: str = Field(default="")
