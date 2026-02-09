"""Simulates realistic system metrics data for incident scenarios.

Generates time-series metric data points (CPU, memory, latency, error rates,
request counts) for each microservice, with anomalies injected per scenario.
"""

import random
from datetime import datetime, timedelta

from aiops_incident_response_agent.models.analysis import AnomalyDetection, MetricDataPoint

SERVICES = [
    "api-gateway",
    "user-service",
    "order-service",
    "payment-service",
    "inventory-service",
    "notification-service",
    "database-proxy",
    "cache-service",
]

# Service dependency graph: service -> list of services it depends on
SERVICE_DEPENDENCIES: dict[str, list[str]] = {
    "api-gateway": ["user-service", "order-service", "payment-service", "inventory-service"],
    "user-service": ["database-proxy", "cache-service"],
    "order-service": ["database-proxy", "payment-service", "inventory-service"],
    "payment-service": ["database-proxy"],
    "inventory-service": ["database-proxy", "cache-service"],
    "notification-service": ["user-service"],
    "database-proxy": [],
    "cache-service": [],
}

# Baseline metric ranges for healthy services
BASELINE_METRICS: dict[str, tuple[float, float, str]] = {
    "cpu_percent": (15.0, 45.0, "%"),
    "memory_percent": (30.0, 55.0, "%"),
    "latency_p99_ms": (50.0, 200.0, "ms"),
    "error_rate": (0.01, 0.5, "errors/s"),
    "request_rate": (100.0, 500.0, "req/s"),
}


def _generate_baseline_metrics(
    base_time: datetime, service: str, duration_minutes: int = 30
) -> list[MetricDataPoint]:
    """Generate normal baseline metrics for a service.

    Args:
        base_time: Starting timestamp.
        service: Service name.
        duration_minutes: Duration of the metrics window.

    Returns:
        list[MetricDataPoint]: Baseline metric data points at 1-minute intervals.
    """
    points = []
    for minute in range(duration_minutes):
        ts = base_time + timedelta(minutes=minute)
        for metric_name, (low, high, unit) in BASELINE_METRICS.items():
            value = random.uniform(low, high)
            points.append(
                MetricDataPoint(
                    timestamp=ts.isoformat(),
                    service=service,
                    metric_name=metric_name,
                    value=round(value, 2),
                    unit=unit,
                )
            )
    return points


def generate_memory_leak_metrics(base_time: datetime) -> list[MetricDataPoint]:
    """Generate metrics consistent with a memory leak in order-service.

    Memory steadily climbs, GC pauses increase, latency degrades,
    then OOM causes error spike and request drop.

    Args:
        base_time: Starting timestamp for the metrics window.

    Returns:
        list[MetricDataPoint]: Time-series metric data showing memory leak.
    """
    points = []
    target = "order-service"

    # Baseline for non-affected services
    for svc in SERVICES:
        if svc != target:
            points.extend(_generate_baseline_metrics(base_time, svc))

    # Target service with memory climb
    for minute in range(40):
        ts = base_time + timedelta(minutes=minute)
        mem = min(40.0 + minute * 1.5, 98.0)
        cpu = 25.0 + (minute * 0.5 if minute < 30 else 15.0 + random.uniform(0, 10))
        latency = 100.0 + (minute ** 1.5 if minute < 35 else 5000 + random.uniform(0, 3000))
        error_rate = 0.1 if minute < 30 else (5.0 + minute - 30) * 3
        req_rate = 300.0 if minute < 33 else max(10.0, 300.0 - (minute - 33) * 50)

        for name, val, unit in [
            ("cpu_percent", cpu, "%"),
            ("memory_percent", mem, "%"),
            ("latency_p99_ms", latency, "ms"),
            ("error_rate", error_rate, "errors/s"),
            ("request_rate", req_rate, "req/s"),
        ]:
            points.append(
                MetricDataPoint(
                    timestamp=ts.isoformat(),
                    service=target,
                    metric_name=name,
                    value=round(val, 2),
                    unit=unit,
                )
            )

    return sorted(points, key=lambda p: p.timestamp)


def generate_deployment_regression_metrics(base_time: datetime) -> list[MetricDataPoint]:
    """Generate metrics consistent with a deployment regression in user-service.

    Args:
        base_time: Starting timestamp for the metrics window.

    Returns:
        list[MetricDataPoint]: Time-series data showing post-deploy regression.
    """
    points = []
    target = "user-service"
    deploy_minute = 10

    for svc in SERVICES:
        if svc != target:
            points.extend(_generate_baseline_metrics(base_time, svc))

    for minute in range(35):
        ts = base_time + timedelta(minutes=minute)
        is_post_deploy = minute > deploy_minute

        cpu = random.uniform(20, 40) if not is_post_deploy else random.uniform(50, 75)
        mem = random.uniform(35, 50) if not is_post_deploy else random.uniform(45, 65)
        latency = random.uniform(80, 150) if not is_post_deploy else random.uniform(800, 3000)
        error_rate = random.uniform(0.01, 0.3) if not is_post_deploy else random.uniform(5.0, 25.0)
        req_rate = random.uniform(200, 400) if not is_post_deploy else random.uniform(150, 350)

        for name, val, unit in [
            ("cpu_percent", cpu, "%"),
            ("memory_percent", mem, "%"),
            ("latency_p99_ms", latency, "ms"),
            ("error_rate", error_rate, "errors/s"),
            ("request_rate", req_rate, "req/s"),
        ]:
            points.append(
                MetricDataPoint(
                    timestamp=ts.isoformat(),
                    service=target,
                    metric_name=name,
                    value=round(val, 2),
                    unit=unit,
                )
            )

    return sorted(points, key=lambda p: p.timestamp)


def generate_database_exhaustion_metrics(base_time: datetime) -> list[MetricDataPoint]:
    """Generate metrics consistent with database connection pool exhaustion.

    Args:
        base_time: Starting timestamp for the metrics window.

    Returns:
        list[MetricDataPoint]: Time-series data showing DB pool exhaustion.
    """
    points = []
    target = "database-proxy"

    for svc in SERVICES:
        if svc not in (target, "order-service", "user-service", "payment-service"):
            points.extend(_generate_baseline_metrics(base_time, svc))

    # database-proxy metrics
    for minute in range(35):
        ts = base_time + timedelta(minutes=minute)
        conn_usage = min(30.0 + minute * 2.0, 100.0)
        latency = 20.0 + (minute ** 1.3 if minute < 25 else 5000 + random.uniform(0, 10000))
        error_rate = 0.05 if minute < 22 else (minute - 22) * 4.0
        cpu = random.uniform(15, 35) + (minute * 0.3 if minute > 15 else 0)

        for name, val, unit in [
            ("cpu_percent", cpu, "%"),
            ("memory_percent", conn_usage, "%"),
            ("latency_p99_ms", latency, "ms"),
            ("error_rate", error_rate, "errors/s"),
            ("request_rate", 400.0 if minute < 25 else max(50, 400 - (minute - 25) * 30), "req/s"),
        ]:
            points.append(
                MetricDataPoint(
                    timestamp=ts.isoformat(),
                    service=target,
                    metric_name=name,
                    value=round(val, 2),
                    unit=unit,
                )
            )

    # Cascading impact on dependent services
    for svc in ["order-service", "user-service", "payment-service"]:
        for minute in range(35):
            ts = base_time + timedelta(minutes=minute)
            is_impacted = minute > 24
            latency = random.uniform(80, 200) if not is_impacted else random.uniform(3000, 15000)
            error_rate = random.uniform(0.01, 0.3) if not is_impacted else random.uniform(8.0, 30.0)

            for name, val, unit in [
                ("latency_p99_ms", latency, "ms"),
                ("error_rate", error_rate, "errors/s"),
            ]:
                points.append(
                    MetricDataPoint(
                        timestamp=ts.isoformat(),
                        service=svc,
                        metric_name=name,
                        value=round(val, 2),
                        unit=unit,
                    )
                )

    return sorted(points, key=lambda p: p.timestamp)


def generate_network_partition_metrics(base_time: datetime) -> list[MetricDataPoint]:
    """Generate metrics consistent with a network partition affecting inventory-service.

    Args:
        base_time: Starting timestamp for the metrics window.

    Returns:
        list[MetricDataPoint]: Time-series data showing network partition.
    """
    points = []
    target = "inventory-service"
    partition_minute = 8

    for svc in SERVICES:
        if svc not in (target, "api-gateway", "order-service"):
            points.extend(_generate_baseline_metrics(base_time, svc))

    # inventory-service goes dark
    for minute in range(30):
        ts = base_time + timedelta(minutes=minute)
        is_partitioned = minute > partition_minute
        req_rate = random.uniform(150, 300) if not is_partitioned else random.uniform(0, 5)
        error_rate = random.uniform(0.01, 0.2) if not is_partitioned else random.uniform(0, 0.5)

        for name, val, unit in [
            ("request_rate", req_rate, "req/s"),
            ("error_rate", error_rate, "errors/s"),
            ("latency_p99_ms", random.uniform(50, 150) if not is_partitioned else 0, "ms"),
        ]:
            points.append(
                MetricDataPoint(
                    timestamp=ts.isoformat(),
                    service=target,
                    metric_name=name,
                    value=round(val, 2),
                    unit=unit,
                )
            )

    # Upstream services see connection errors
    for svc in ["api-gateway", "order-service"]:
        for minute in range(30):
            ts = base_time + timedelta(minutes=minute)
            is_impacted = minute > partition_minute
            error_rate = random.uniform(0.01, 0.3) if not is_impacted else random.uniform(10.0, 40.0)
            latency = random.uniform(80, 200) if not is_impacted else random.uniform(5000, 30000)

            for name, val, unit in [
                ("error_rate", error_rate, "errors/s"),
                ("latency_p99_ms", latency, "ms"),
            ]:
                points.append(
                    MetricDataPoint(
                        timestamp=ts.isoformat(),
                        service=svc,
                        metric_name=name,
                        value=round(val, 2),
                        unit=unit,
                    )
                )

    return sorted(points, key=lambda p: p.timestamp)


def generate_cpu_spike_metrics(base_time: datetime) -> list[MetricDataPoint]:
    """Generate metrics consistent with a CPU spike on payment-service.

    Args:
        base_time: Starting timestamp for the metrics window.

    Returns:
        list[MetricDataPoint]: Time-series data showing CPU saturation.
    """
    points = []
    target = "payment-service"
    spike_minute = 5

    for svc in SERVICES:
        if svc != target:
            points.extend(_generate_baseline_metrics(base_time, svc))

    for minute in range(30):
        ts = base_time + timedelta(minutes=minute)
        is_spiked = minute > spike_minute
        cpu = random.uniform(20, 40) if not is_spiked else min(60 + (minute - spike_minute) * 4, 99)
        latency = random.uniform(80, 200) if not is_spiked else random.uniform(2000, 10000)
        error_rate = random.uniform(0.01, 0.3) if not is_spiked else random.uniform(3.0, 15.0)
        req_rate = random.uniform(200, 400) if not is_spiked else max(20, 300 - (minute - spike_minute) * 15)

        for name, val, unit in [
            ("cpu_percent", cpu, "%"),
            ("memory_percent", random.uniform(35, 55), "%"),
            ("latency_p99_ms", latency, "ms"),
            ("error_rate", error_rate, "errors/s"),
            ("request_rate", req_rate, "req/s"),
        ]:
            points.append(
                MetricDataPoint(
                    timestamp=ts.isoformat(),
                    service=target,
                    metric_name=name,
                    value=round(val, 2),
                    unit=unit,
                )
            )

    return sorted(points, key=lambda p: p.timestamp)
