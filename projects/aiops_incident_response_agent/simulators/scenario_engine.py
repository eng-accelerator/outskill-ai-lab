"""Scenario engine that orchestrates realistic incident scenarios.

Coordinates all simulators to produce correlated observability data
(logs, metrics, alerts, traces, deployments) for a given incident type.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from aiops_incident_response_agent.models.analysis import (
    Deployment,
    LogEntry,
    MetricDataPoint,
    TraceSpan,
)
from aiops_incident_response_agent.models.incident import Alert, ServiceHealth
from aiops_incident_response_agent.simulators.alert_simulator import (
    generate_cpu_spike_alerts,
    generate_database_exhaustion_alerts,
    generate_deployment_regression_alerts,
    generate_memory_leak_alerts,
    generate_network_partition_alerts,
)
from aiops_incident_response_agent.simulators.log_simulator import (
    generate_cpu_spike_logs,
    generate_database_exhaustion_logs,
    generate_deployment_regression_logs,
    generate_memory_leak_logs,
    generate_network_partition_logs,
)
from aiops_incident_response_agent.simulators.metrics_simulator import (
    generate_cpu_spike_metrics,
    generate_database_exhaustion_metrics,
    generate_deployment_regression_metrics,
    generate_memory_leak_metrics,
    generate_network_partition_metrics,
)
from aiops_incident_response_agent.simulators.trace_simulator import (
    generate_cpu_spike_deployments,
    generate_cpu_spike_traces,
    generate_database_exhaustion_deployments,
    generate_database_exhaustion_traces,
    generate_deployment_regression_deployments,
    generate_deployment_regression_traces,
    generate_memory_leak_deployments,
    generate_memory_leak_traces,
    generate_network_partition_deployments,
    generate_network_partition_traces,
)

logger = logging.getLogger(__name__)

# Supported scenario types
ScenarioType = Literal[
    "memory_leak",
    "deployment_regression",
    "database_exhaustion",
    "network_partition",
    "cpu_spike",
]

SCENARIO_DESCRIPTIONS: dict[ScenarioType, str] = {
    "memory_leak": (
        "Memory leak in order-service causing gradual degradation, "
        "GC pressure, OOM kills, and cascading failures to api-gateway and payment-service."
    ),
    "deployment_regression": (
        "Deployment of user-service v2.5.0 introduced a regression causing "
        "NullPointerExceptions, elevated error rates, and latency spikes."
    ),
    "database_exhaustion": (
        "Database connection pool on database-proxy gradually exhausted, "
        "causing timeouts cascading to order-service, user-service, and payment-service."
    ),
    "network_partition": (
        "Network partition isolating inventory-service from the rest of the cluster, "
        "causing connection refused errors and order processing failures."
    ),
    "cpu_spike": (
        "CPU spike on payment-service-pod-2 causing request queue buildup, "
        "processing timeouts, and degraded payment processing."
    ),
}


@dataclass
class ScenarioData:
    """Complete observability data for a simulated incident scenario.

    Attributes:
        scenario_type: The type of incident scenario.
        description: Human-readable description of the scenario.
        base_time: Starting timestamp for the scenario.
        logs: Simulated application log entries.
        metrics: Simulated metric data points.
        alerts: Simulated monitoring alerts.
        service_health: Current health status of all services.
        traces: Simulated distributed trace spans.
        deployments: Recent deployment records.
    """

    scenario_type: ScenarioType
    description: str
    base_time: datetime
    logs: list[LogEntry] = field(default_factory=list)
    metrics: list[MetricDataPoint] = field(default_factory=list)
    alerts: list[Alert] = field(default_factory=list)
    service_health: list[ServiceHealth] = field(default_factory=list)
    traces: list[TraceSpan] = field(default_factory=list)
    deployments: list[Deployment] = field(default_factory=list)


def generate_scenario(scenario_type: ScenarioType) -> ScenarioData:
    """Generate a complete incident scenario with correlated observability data.

    Coordinates all simulators to produce logs, metrics, alerts, traces,
    and deployment records for the specified scenario type.

    Args:
        scenario_type: The type of incident to simulate.

    Returns:
        ScenarioData: Complete observability data for the scenario.

    Raises:
        ValueError: If scenario_type is not a supported scenario.
    """
    base_time = datetime.now(timezone.utc)
    logger.info("Generating scenario: %s", scenario_type)

    generators: dict[ScenarioType, tuple] = {
        "memory_leak": (
            generate_memory_leak_logs,
            generate_memory_leak_metrics,
            generate_memory_leak_alerts,
            generate_memory_leak_traces,
            generate_memory_leak_deployments,
        ),
        "deployment_regression": (
            generate_deployment_regression_logs,
            generate_deployment_regression_metrics,
            generate_deployment_regression_alerts,
            generate_deployment_regression_traces,
            generate_deployment_regression_deployments,
        ),
        "database_exhaustion": (
            generate_database_exhaustion_logs,
            generate_database_exhaustion_metrics,
            generate_database_exhaustion_alerts,
            generate_database_exhaustion_traces,
            generate_database_exhaustion_deployments,
        ),
        "network_partition": (
            generate_network_partition_logs,
            generate_network_partition_metrics,
            generate_network_partition_alerts,
            generate_network_partition_traces,
            generate_network_partition_deployments,
        ),
        "cpu_spike": (
            generate_cpu_spike_logs,
            generate_cpu_spike_metrics,
            generate_cpu_spike_alerts,
            generate_cpu_spike_traces,
            generate_cpu_spike_deployments,
        ),
    }

    assert scenario_type in generators, f"Unknown scenario: {scenario_type}"

    log_gen, metric_gen, alert_gen, trace_gen, deploy_gen = generators[scenario_type]

    logs = log_gen(base_time)
    metrics = metric_gen(base_time)
    alerts_list, health_list = alert_gen(base_time)
    traces = trace_gen(base_time)
    deployments = deploy_gen(base_time)

    logger.info(
        "Scenario generated: logs=%d, metrics=%d, alerts=%d, traces=%d, deployments=%d",
        len(logs), len(metrics), len(alerts_list), len(traces), len(deployments),
    )

    return ScenarioData(
        scenario_type=scenario_type,
        description=SCENARIO_DESCRIPTIONS[scenario_type],
        base_time=base_time,
        logs=logs,
        metrics=metrics,
        alerts=alerts_list,
        service_health=health_list,
        traces=traces,
        deployments=deployments,
    )


def list_scenarios() -> list[tuple[ScenarioType, str]]:
    """List all available incident scenarios.

    Returns:
        list[tuple[ScenarioType, str]]: List of (scenario_type, description) tuples.
    """
    return [(k, v) for k, v in SCENARIO_DESCRIPTIONS.items()]
