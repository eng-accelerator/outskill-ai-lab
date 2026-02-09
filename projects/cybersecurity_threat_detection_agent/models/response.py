"""Data models for containment actions and SOC incident reports.

Defines the structured output types for the containment agent
and the final SOC report agent.
"""

from dataclasses import dataclass, field
from typing import Literal

# Types of containment actions
ContainmentActionType = Literal[
    "block_ip",
    "disable_account",
    "revoke_api_key",
    "isolate_host",
    "quarantine_file",
]

# Risk level for a proposed containment action
RiskLevel = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True)
class ContainmentAction:
    """A single proposed containment action.

    Attributes:
        action_type: Type of containment action.
        target: Target of the action (IP, username, API key ID, hostname).
        reason: Justification for the action.
        risk_level: Risk assessment for this action.
        requires_approval: Whether human approval is needed.
        command: Simulated command to execute the action.
    """

    action_type: ContainmentActionType
    target: str
    reason: str
    risk_level: RiskLevel
    requires_approval: bool
    command: str


@dataclass(frozen=True)
class ThreatScore:
    """Computed threat score for an incident.

    Attributes:
        score: Numeric threat score from 0 (benign) to 100 (critical).
        confidence: Confidence in the score (0.0 to 1.0).
        factors: Contributing factors that influenced the score.
    """

    score: int
    confidence: float
    factors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SOCIncidentReport:
    """Complete SOC incident report.

    Attributes:
        title: Descriptive incident title.
        severity: Threat severity level.
        threat_score: Computed threat score.
        summary: Executive summary of the incident.
        mitre_mappings: MITRE ATT&CK technique references.
        affected_assets: List of affected asset identifiers.
        timeline: Chronological list of events.
        containment_actions: Proposed or executed containment actions.
        evidence: Supporting evidence items.
        status: Current incident status.
    """

    title: str
    severity: str
    threat_score: int
    summary: str
    mitre_mappings: list[str] = field(default_factory=list)
    affected_assets: list[str] = field(default_factory=list)
    timeline: list[str] = field(default_factory=list)
    containment_actions: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    status: str = "investigating"
