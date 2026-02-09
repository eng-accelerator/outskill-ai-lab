"""Data models for remediation plans and actions.

Defines the structured output types for the remediation agent,
including proposed actions, runbook steps, and the overall plan.
"""

from dataclasses import dataclass, field
from typing import Literal

# Risk level for a proposed remediation action
RiskLevel = Literal["low", "medium", "high", "critical"]

# Type of remediation action
ActionType = Literal[
    "rollback",
    "scale_up",
    "scale_down",
    "restart_service",
    "config_change",
    "database_fix",
    "network_fix",
    "manual_intervention",
]


@dataclass(frozen=True)
class RemediationAction:
    """A single proposed remediation action.

    Attributes:
        action_type: Category of the remediation action.
        description: Human-readable description of what this action does.
        target_service: Service this action targets.
        risk_level: Risk assessment for this action.
        estimated_impact: Expected impact of performing this action.
        requires_approval: Whether human approval is needed before execution.
        runbook_steps: Ordered steps to execute this action.
    """

    action_type: ActionType
    description: str
    target_service: str
    risk_level: RiskLevel
    estimated_impact: str
    requires_approval: bool
    runbook_steps: list[str]


@dataclass(frozen=True)
class RemediationPlan:
    """Complete remediation plan for an incident.

    Attributes:
        incident_summary: Brief summary of the incident being remediated.
        root_cause: The identified root cause.
        actions: Ordered list of remediation actions to take.
        estimated_resolution_time: Estimated time to resolve in minutes.
        rollback_plan: Steps to rollback if remediation fails.
        communication_needed: Whether stakeholder communication is required.
        post_incident_tasks: Tasks to perform after resolution.
    """

    incident_summary: str
    root_cause: str
    actions: list[RemediationAction] = field(default_factory=list)
    estimated_resolution_time: int = 30
    rollback_plan: list[str] = field(default_factory=list)
    communication_needed: bool = True
    post_incident_tasks: list[str] = field(default_factory=list)
