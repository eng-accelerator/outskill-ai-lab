"""Tools for querying and analyzing system metrics.

These tools are used by the Metrics Analyzer Agent to detect
anomalies, analyze trends, and understand service dependencies.
"""

import json
import logging
from dataclasses import asdict

from agents import RunContextWrapper, function_tool
from aiops_incident_response_agent.simulators.metrics_simulator import (
    SERVICE_DEPENDENCIES,
)
from aiops_incident_response_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


@function_tool
def query_metrics(
    ctx: RunContextWrapper[ScenarioData],
    service: str = "",
    metric_name: str = "",
    limit: int = 100,
) -> str:
    """Query system metrics, optionally filtered by service and metric name.

    Returns time-series metric data points. Available metric names:
    cpu_percent, memory_percent, latency_p99_ms, error_rate, request_rate.

    Args:
        ctx: Run context containing the scenario data.
        service: Filter by service name (empty for all services).
        metric_name: Filter by metric name (empty for all metrics).
        limit: Maximum number of data points to return (default 100).

    Returns:
        str: JSON string of metric data points.
    """
    scenario = ctx.context
    metrics = scenario.metrics

    if service:
        metrics = [m for m in metrics if m.service == service]
    if metric_name:
        metrics = [m for m in metrics if m.metric_name == metric_name]

    metrics = metrics[:limit]
    logger.info(
        "Queried %d metrics (service=%s, metric=%s)", len(metrics), service, metric_name
    )
    return json.dumps([asdict(m) for m in metrics], indent=2)


@function_tool
def detect_anomalies(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Detect anomalies across all service metrics.

    Analyzes metric data to find values significantly outside normal ranges.
    Checks for spikes, drops, and trend changes in CPU, memory, latency,
    error rate, and request rate.

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string of detected anomalies with service, metric,
             current value, expected range, and anomaly type.
    """
    scenario = ctx.context

    # Compute per-service, per-metric stats
    service_metrics: dict[str, dict[str, list[float]]] = {}
    for m in scenario.metrics:
        if m.service not in service_metrics:
            service_metrics[m.service] = {}
        if m.metric_name not in service_metrics[m.service]:
            service_metrics[m.service][m.metric_name] = []
        service_metrics[m.service][m.metric_name].append(m.value)

    anomalies = []
    for service, metrics_map in service_metrics.items():
        for metric_name, values in metrics_map.items():
            if len(values) < 5:
                continue

            # Use first half as baseline, check second half for anomalies
            mid = len(values) // 2
            baseline = values[:mid]
            recent = values[mid:]

            baseline_mean = sum(baseline) / len(baseline)
            baseline_std = max(
                (sum((v - baseline_mean) ** 2 for v in baseline) / len(baseline))
                ** 0.5,
                0.01,
            )

            recent_mean = sum(recent) / len(recent)
            recent_max = max(recent)
            recent_min = min(recent)

            # Detect significant deviations
            z_score = abs(recent_mean - baseline_mean) / baseline_std
            if z_score > 2.0:
                anomaly_type = "spike" if recent_mean > baseline_mean else "drop"
                if (
                    metric_name in ("error_rate", "latency_p99_ms")
                    and recent_mean > baseline_mean
                ):
                    anomaly_type = "spike"
                elif metric_name == "request_rate" and recent_mean < baseline_mean:
                    anomaly_type = "drop"

                anomalies.append(
                    {
                        "service": service,
                        "metric_name": metric_name,
                        "current_value": round(recent_mean, 2),
                        "expected_range_low": round(
                            baseline_mean - 2 * baseline_std, 2
                        ),
                        "expected_range_high": round(
                            baseline_mean + 2 * baseline_std, 2
                        ),
                        "anomaly_type": anomaly_type,
                        "confidence": round(min(z_score / 5.0, 1.0), 2),
                        "peak_value": round(recent_max, 2),
                    }
                )

    anomalies.sort(key=lambda a: a["confidence"], reverse=True)
    logger.info("Detected %d anomalies", len(anomalies))
    return json.dumps(anomalies, indent=2)


@function_tool
def get_service_dependencies(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Get the service dependency graph.

    Returns a map of each service to the services it depends on.
    Use this to understand blast radius and cascading failure paths.

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string of service dependency map.
    """
    logger.info("Returning service dependency graph")
    return json.dumps(SERVICE_DEPENDENCIES, indent=2)
