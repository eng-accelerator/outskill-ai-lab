"""Pydantic schemas for the Cybersecurity Threat Detection Agent API.

Defines request and response models, run status, and pipeline phase literals
used by REST endpoints and SSE clients.
"""

from typing import Literal

from pydantic import BaseModel, Field

from cybersecurity_threat_detection_agent.simulators.scenario_engine import ScenarioType

RunStatus = Literal["pending", "running", "completed", "failed"]

PhaseType = Literal[
    "alert_intake",
    "auth_analysis",
    "network_analysis",
    "threat_intel",
    "containment",
    "soc_reporting",
    "completed",
]


class ThreatRequest(BaseModel):
    """Request body to start a new threat detection run.

    Attributes:
        scenario_type: Which simulated threat scenario to generate and analyze.
    """

    scenario_type: ScenarioType


class ThreatRunResponse(BaseModel):
    """Response after initiating a threat detection run.

    Attributes:
        run_id: Unique identifier for this run.
        status: Current status of the run.
    """

    run_id: str
    status: RunStatus


class ScenarioInfo(BaseModel):
    """Metadata for one available threat scenario.

    Attributes:
        scenario_type: Scenario identifier.
        description: Human-readable description of the scenario.
    """

    scenario_type: ScenarioType
    description: str


class ThreatResultResponse(BaseModel):
    """Response for fetching a threat run result snapshot.

    Attributes:
        run_id: Unique identifier for this run.
        status: Current run status.
        scenario_type: The scenario that was simulated.
        report: Final SOC report output (empty until completed).
    """

    run_id: str
    status: RunStatus
    scenario_type: ScenarioType
    report: str = Field(default="")
