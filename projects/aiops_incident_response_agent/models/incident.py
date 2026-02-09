"""Data models for incident triage and classification.

Defines the core types used throughout the incident response pipeline
for representing alerts, triage results, and incident metadata.
"""

from dataclasses import dataclass, field
from typing import Literal

# Severity levels for incidents, from most to least critical
Severity = Literal["P0", "P1", "P2", "P3"]

# Categories of incidents the system can handle
IncidentCategory = Literal[
    "memory_leak",
    "deployment_regression",
    "database_exhaustion",
    "network_partition",
    "cpu_spike",
    "unknown",
]

# Types of signals that can trigger or inform an incident
SignalType = Literal["log", "metric", "alert", "trace"]


@dataclass(frozen=True)
class Alert:
    """An alert from the monitoring system.

    Attributes:
        alert_id: Unique identifier for the alert.
        service: Name of the affected service.
        severity: Alert severity level (critical, warning, info).
        message: Human-readable alert description.
        timestamp: ISO 8601 timestamp of when the alert fired.
        labels: Key-value metadata labels on the alert.
    """

    alert_id: str
    service: str
    severity: Literal["critical", "warning", "info"]
    message: str
    timestamp: str
    labels: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ServiceHealth:
    """Health summary for a single service.

    Attributes:
        service: Name of the service.
        status: Current health status.
        cpu_percent: Current CPU usage percentage.
        memory_percent: Current memory usage percentage.
        error_rate: Errors per second.
        latency_p99_ms: 99th percentile latency in milliseconds.
        active_alerts: Number of currently active alerts.
    """

    service: str
    status: Literal["healthy", "degraded", "critical", "unknown"]
    cpu_percent: float
    memory_percent: float
    error_rate: float
    latency_p99_ms: float
    active_alerts: int


@dataclass(frozen=True)
class TriageResult:
    """Result of the triage agent's analysis.

    Attributes:
        severity: Assessed incident severity (P0-P3).
        category: Classified incident category.
        affected_services: List of services impacted by the incident.
        summary: Brief description of the incident.
        recommended_analysis: Whether to route to log or metrics analysis first.
    """

    severity: Severity
    category: IncidentCategory
    affected_services: list[str]
    summary: str
    recommended_analysis: Literal["log_analysis", "metrics_analysis", "both"]
