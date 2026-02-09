"""Data models for log analysis, metrics analysis, and root cause analysis results.

These models capture the structured outputs of the analysis agents
in the incident response pipeline.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class LogEntry:
    """A single log entry from the application.

    Attributes:
        timestamp: ISO 8601 timestamp.
        service: Service that emitted the log.
        level: Log level.
        message: Log message content.
        trace_id: Optional distributed trace ID.
        metadata: Additional structured fields.
    """

    timestamp: str
    service: str
    level: Literal["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
    message: str
    trace_id: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ErrorPattern:
    """A detected error pattern in logs.

    Attributes:
        pattern: The error pattern string or regex.
        count: Number of occurrences in the queried window.
        first_seen: Timestamp of first occurrence.
        last_seen: Timestamp of most recent occurrence.
        services: Services where this pattern was observed.
        sample_message: A representative log message.
    """

    pattern: str
    count: int
    first_seen: str
    last_seen: str
    services: list[str]
    sample_message: str


@dataclass(frozen=True)
class MetricDataPoint:
    """A single metric data point.

    Attributes:
        timestamp: ISO 8601 timestamp.
        service: Service the metric belongs to.
        metric_name: Name of the metric (e.g. cpu_percent, memory_percent).
        value: Numeric value of the metric.
        unit: Unit of measurement.
    """

    timestamp: str
    service: str
    metric_name: str
    value: float
    unit: str


@dataclass(frozen=True)
class AnomalyDetection:
    """A detected anomaly in metrics.

    Attributes:
        service: Affected service.
        metric_name: The metric that is anomalous.
        current_value: Current observed value.
        expected_range_low: Lower bound of expected range.
        expected_range_high: Upper bound of expected range.
        anomaly_type: Type of anomaly detected.
        confidence: Confidence score 0.0 to 1.0.
        started_at: When the anomaly began.
    """

    service: str
    metric_name: str
    current_value: float
    expected_range_low: float
    expected_range_high: float
    anomaly_type: Literal["spike", "drop", "trend_up", "trend_down", "flatline"]
    confidence: float
    started_at: str


@dataclass(frozen=True)
class TraceSpan:
    """A single span in a distributed trace.

    Attributes:
        trace_id: The distributed trace ID.
        span_id: Unique span identifier.
        parent_span_id: Parent span ID (empty for root spans).
        service: Service that produced this span.
        operation: Operation name.
        duration_ms: Duration in milliseconds.
        status: Span status.
        timestamp: ISO 8601 start timestamp.
        error_message: Error message if status is error.
    """

    trace_id: str
    span_id: str
    parent_span_id: str
    service: str
    operation: str
    duration_ms: float
    status: Literal["ok", "error", "timeout"]
    timestamp: str
    error_message: str = ""


@dataclass(frozen=True)
class Deployment:
    """A recent deployment record.

    Attributes:
        deploy_id: Unique deployment identifier.
        service: Service that was deployed.
        version: Version string of the deployment.
        timestamp: ISO 8601 timestamp of deployment.
        deployed_by: Who initiated the deployment.
        change_summary: Brief summary of changes.
        rollback_available: Whether rollback is possible.
    """

    deploy_id: str
    service: str
    version: str
    timestamp: str
    deployed_by: str
    change_summary: str
    rollback_available: bool


@dataclass(frozen=True)
class LogAnalysisResult:
    """Structured result from the Log Analyzer agent.

    Attributes:
        error_patterns: Detected error patterns.
        anomalous_services: Services with anomalous log patterns.
        key_findings: Summary findings from log analysis.
        log_volume_change: Percentage change in log volume vs baseline.
        correlation_hints: Hints about correlated events across services.
    """

    error_patterns: list[str]
    anomalous_services: list[str]
    key_findings: list[str]
    log_volume_change: float
    correlation_hints: list[str]


@dataclass(frozen=True)
class MetricsAnalysisResult:
    """Structured result from the Metrics Analyzer agent.

    Attributes:
        anomalies_detected: List of detected anomaly descriptions.
        affected_services: Services with metric anomalies.
        key_findings: Summary findings from metrics analysis.
        service_dependency_impact: Which downstream services are impacted.
        timeline: Ordered list of significant metric events.
    """

    anomalies_detected: list[str]
    affected_services: list[str]
    key_findings: list[str]
    service_dependency_impact: list[str]
    timeline: list[str]


@dataclass(frozen=True)
class RCAResult:
    """Structured result from the Root Cause Analyzer agent.

    Attributes:
        root_cause: Identified root cause description.
        confidence: Confidence in the root cause assessment (0.0 to 1.0).
        contributing_factors: Additional factors that contributed.
        evidence: Evidence supporting the root cause conclusion.
        affected_services: Full list of affected services.
        timeline: Chronological timeline of the incident.
        category: Classified incident category.
    """

    root_cause: str
    confidence: float
    contributing_factors: list[str]
    evidence: list[str]
    affected_services: list[str]
    timeline: list[str]
    category: str
