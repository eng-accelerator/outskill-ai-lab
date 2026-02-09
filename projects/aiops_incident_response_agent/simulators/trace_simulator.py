"""Simulates distributed trace data for incident scenarios.

Generates trace spans showing request flow across microservices,
with errors and latency anomalies injected per scenario.
"""

import random
from datetime import datetime, timedelta

from aiops_incident_response_agent.models.analysis import Deployment, TraceSpan


def _make_span(
    trace_id: str,
    span_id: str,
    parent_span_id: str,
    service: str,
    operation: str,
    duration_ms: float,
    status: str,
    timestamp: datetime,
    error_message: str = "",
) -> TraceSpan:
    """Create a TraceSpan with the given parameters.

    Args:
        trace_id: Distributed trace ID.
        span_id: Unique span ID.
        parent_span_id: Parent span ID (empty for root).
        service: Service name.
        operation: Operation name.
        duration_ms: Span duration in milliseconds.
        status: Span status (ok, error, timeout).
        timestamp: Span start time.
        error_message: Error message if applicable.

    Returns:
        TraceSpan: Constructed trace span.
    """
    return TraceSpan(
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id,
        service=service,
        operation=operation,
        duration_ms=round(duration_ms, 1),
        status=status,
        timestamp=timestamp.isoformat(),
        error_message=error_message,
    )


def generate_memory_leak_traces(base_time: datetime) -> list[TraceSpan]:
    """Generate traces showing degradation from a memory leak.

    Args:
        base_time: Starting timestamp.

    Returns:
        list[TraceSpan]: Trace spans showing memory-related failures.
    """
    spans = []

    # Normal trace before incident
    t1 = base_time + timedelta(minutes=5)
    spans.extend([
        _make_span("trace-ml-001", "span-001", "", "api-gateway", "POST /orders", 180, "ok", t1),
        _make_span("trace-ml-001", "span-002", "span-001", "order-service", "createOrder", 120, "ok", t1 + timedelta(milliseconds=10)),
        _make_span("trace-ml-001", "span-003", "span-002", "database-proxy", "INSERT orders", 30, "ok", t1 + timedelta(milliseconds=50)),
        _make_span("trace-ml-001", "span-004", "span-002", "payment-service", "processPayment", 60, "ok", t1 + timedelta(milliseconds=85)),
    ])

    # Degrading trace during memory pressure
    t2 = base_time + timedelta(minutes=28)
    spans.extend([
        _make_span("trace-ml-002", "span-005", "", "api-gateway", "POST /orders", 2500, "ok", t2),
        _make_span("trace-ml-002", "span-006", "span-005", "order-service", "createOrder", 2200, "ok", t2 + timedelta(milliseconds=10)),
        _make_span("trace-ml-002", "span-007", "span-006", "database-proxy", "INSERT orders", 35, "ok", t2 + timedelta(milliseconds=50)),
        _make_span("trace-ml-002", "span-008", "span-006", "payment-service", "processPayment", 80, "ok", t2 + timedelta(milliseconds=1500)),
    ])

    # Failed trace after OOM
    t3 = base_time + timedelta(minutes=36)
    spans.extend([
        _make_span("trace-ml-003", "span-009", "", "api-gateway", "POST /orders", 5000, "error", t3, "503 Service Unavailable"),
        _make_span("trace-ml-003", "span-010", "span-009", "order-service", "createOrder", 0, "error", t3 + timedelta(milliseconds=10), "Connection refused"),
    ])

    return spans


def generate_deployment_regression_traces(base_time: datetime) -> list[TraceSpan]:
    """Generate traces showing a deployment regression.

    Args:
        base_time: Starting timestamp.

    Returns:
        list[TraceSpan]: Trace spans showing post-deploy failures.
    """
    spans = []
    deploy_time = base_time + timedelta(minutes=10)

    # Normal trace before deploy
    t1 = base_time + timedelta(minutes=5)
    spans.extend([
        _make_span("trace-dr-001", "span-101", "", "api-gateway", "GET /users/profile", 95, "ok", t1),
        _make_span("trace-dr-001", "span-102", "span-101", "user-service", "getProfile", 55, "ok", t1 + timedelta(milliseconds=10)),
        _make_span("trace-dr-001", "span-103", "span-102", "database-proxy", "SELECT users", 15, "ok", t1 + timedelta(milliseconds=25)),
        _make_span("trace-dr-001", "span-104", "span-102", "cache-service", "GET user:123", 5, "ok", t1 + timedelta(milliseconds=20)),
    ])

    # Error trace after deploy
    t2 = deploy_time + timedelta(minutes=5)
    spans.extend([
        _make_span("trace-dr-002", "span-105", "", "api-gateway", "GET /users/profile", 3200, "error", t2, "502 Bad Gateway"),
        _make_span("trace-dr-002", "span-106", "span-105", "user-service", "getProfile", 3100, "error", t2 + timedelta(milliseconds=10), "NullPointerException in UserController.getProfile()"),
        _make_span("trace-dr-002", "span-107", "span-106", "database-proxy", "SELECT users", 18, "ok", t2 + timedelta(milliseconds=25)),
    ])

    # Another error trace
    t3 = deploy_time + timedelta(minutes=8)
    spans.extend([
        _make_span("trace-dr-003", "span-108", "", "api-gateway", "POST /users/login", 5000, "timeout", t3, "Gateway Timeout"),
        _make_span("trace-dr-003", "span-109", "span-108", "user-service", "authenticate", 5000, "timeout", t3 + timedelta(milliseconds=10), "Request processing timeout"),
    ])

    return spans


def generate_database_exhaustion_traces(base_time: datetime) -> list[TraceSpan]:
    """Generate traces showing database connection pool exhaustion.

    Args:
        base_time: Starting timestamp.

    Returns:
        list[TraceSpan]: Trace spans showing DB pool exhaustion.
    """
    spans = []

    # Normal trace
    t1 = base_time + timedelta(minutes=5)
    spans.extend([
        _make_span("trace-db-001", "span-201", "", "api-gateway", "POST /orders", 150, "ok", t1),
        _make_span("trace-db-001", "span-202", "span-201", "order-service", "createOrder", 100, "ok", t1 + timedelta(milliseconds=10)),
        _make_span("trace-db-001", "span-203", "span-202", "database-proxy", "INSERT orders", 25, "ok", t1 + timedelta(milliseconds=40)),
    ])

    # Slow trace during pool pressure
    t2 = base_time + timedelta(minutes=22)
    spans.extend([
        _make_span("trace-db-002", "span-204", "", "api-gateway", "POST /orders", 5800, "ok", t2),
        _make_span("trace-db-002", "span-205", "span-204", "order-service", "createOrder", 5500, "ok", t2 + timedelta(milliseconds=10)),
        _make_span("trace-db-002", "span-206", "span-205", "database-proxy", "INSERT orders", 5200, "ok", t2 + timedelta(milliseconds=40)),
    ])

    # Failed trace after exhaustion
    t3 = base_time + timedelta(minutes=26)
    spans.extend([
        _make_span("trace-db-003", "span-207", "", "api-gateway", "GET /orders/123", 15000, "timeout", t3, "Gateway Timeout"),
        _make_span("trace-db-003", "span-208", "span-207", "order-service", "getOrder", 15000, "timeout", t3 + timedelta(milliseconds=10), "Database query timeout"),
        _make_span("trace-db-003", "span-209", "span-208", "database-proxy", "SELECT orders", 15000, "timeout", t3 + timedelta(milliseconds=20), "Connection pool exhausted: no available connections"),
    ])

    return spans


def generate_network_partition_traces(base_time: datetime) -> list[TraceSpan]:
    """Generate traces showing a network partition.

    Args:
        base_time: Starting timestamp.

    Returns:
        list[TraceSpan]: Trace spans showing network partition effects.
    """
    spans = []
    partition_time = base_time + timedelta(minutes=8)

    # Normal trace before partition
    t1 = base_time + timedelta(minutes=3)
    spans.extend([
        _make_span("trace-np-001", "span-301", "", "api-gateway", "GET /inventory/check", 120, "ok", t1),
        _make_span("trace-np-001", "span-302", "span-301", "inventory-service", "checkStock", 80, "ok", t1 + timedelta(milliseconds=10)),
        _make_span("trace-np-001", "span-303", "span-302", "database-proxy", "SELECT inventory", 20, "ok", t1 + timedelta(milliseconds=30)),
    ])

    # Failed trace during partition
    t2 = partition_time + timedelta(minutes=2)
    spans.extend([
        _make_span("trace-np-002", "span-304", "", "api-gateway", "GET /inventory/check", 30000, "error", t2, "Connection refused to inventory-service:8080"),
    ])

    # Order service also fails
    t3 = partition_time + timedelta(minutes=3)
    spans.extend([
        _make_span("trace-np-003", "span-305", "", "api-gateway", "POST /orders", 30000, "error", t3, "Partial failure: inventory check failed"),
        _make_span("trace-np-003", "span-306", "span-305", "order-service", "createOrder", 30000, "error", t3 + timedelta(milliseconds=10), "Failed to reach inventory-service"),
    ])

    return spans


def generate_cpu_spike_traces(base_time: datetime) -> list[TraceSpan]:
    """Generate traces showing CPU spike effects.

    Args:
        base_time: Starting timestamp.

    Returns:
        list[TraceSpan]: Trace spans showing CPU saturation effects.
    """
    spans = []
    spike_time = base_time + timedelta(minutes=5)

    # Normal trace before spike
    t1 = base_time + timedelta(minutes=2)
    spans.extend([
        _make_span("trace-cs-001", "span-401", "", "api-gateway", "POST /payments", 200, "ok", t1),
        _make_span("trace-cs-001", "span-402", "span-401", "payment-service", "processPayment", 150, "ok", t1 + timedelta(milliseconds=10)),
        _make_span("trace-cs-001", "span-403", "span-402", "database-proxy", "INSERT payments", 30, "ok", t1 + timedelta(milliseconds=80)),
    ])

    # Slow trace during spike
    t2 = spike_time + timedelta(minutes=5)
    spans.extend([
        _make_span("trace-cs-002", "span-404", "", "api-gateway", "POST /payments", 8500, "ok", t2),
        _make_span("trace-cs-002", "span-405", "span-404", "payment-service", "processPayment", 8200, "ok", t2 + timedelta(milliseconds=10)),
        _make_span("trace-cs-002", "span-406", "span-405", "database-proxy", "INSERT payments", 35, "ok", t2 + timedelta(milliseconds=6000)),
    ])

    # Timeout trace
    t3 = spike_time + timedelta(minutes=8)
    spans.extend([
        _make_span("trace-cs-003", "span-407", "", "api-gateway", "POST /payments", 30000, "timeout", t3, "Gateway Timeout"),
        _make_span("trace-cs-003", "span-408", "span-407", "payment-service", "processPayment", 30000, "timeout", t3 + timedelta(milliseconds=10), "Request processing timeout - CPU saturated"),
    ])

    return spans


# Deployment records per scenario

def generate_memory_leak_deployments(base_time: datetime) -> list[Deployment]:
    """Generate deployment records for memory leak scenario (no recent deploys).

    Args:
        base_time: Incident start time.

    Returns:
        list[Deployment]: Recent deployment records.
    """
    return [
        Deployment(
            deploy_id="deploy-2840",
            service="order-service",
            version="v3.2.1",
            timestamp=(base_time - timedelta(days=3)).isoformat(),
            deployed_by="ci-pipeline",
            change_summary="Minor logging improvements and dependency updates",
            rollback_available=True,
        ),
        Deployment(
            deploy_id="deploy-2838",
            service="api-gateway",
            version="v1.8.0",
            timestamp=(base_time - timedelta(days=5)).isoformat(),
            deployed_by="ci-pipeline",
            change_summary="Rate limiting configuration update",
            rollback_available=True,
        ),
    ]


def generate_deployment_regression_deployments(base_time: datetime) -> list[Deployment]:
    """Generate deployment records for deployment regression scenario.

    Args:
        base_time: Incident start time.

    Returns:
        list[Deployment]: Recent deployment records including the bad deploy.
    """
    deploy_time = base_time + timedelta(minutes=10)
    return [
        Deployment(
            deploy_id="deploy-2847",
            service="user-service",
            version="v2.5.0",
            timestamp=deploy_time.isoformat(),
            deployed_by="ci-pipeline",
            change_summary="Refactored authentication module, updated token validation logic",
            rollback_available=True,
        ),
        Deployment(
            deploy_id="deploy-2846",
            service="user-service",
            version="v2.4.1",
            timestamp=(base_time - timedelta(days=2)).isoformat(),
            deployed_by="ci-pipeline",
            change_summary="Bug fix for profile image upload",
            rollback_available=True,
        ),
    ]


def generate_database_exhaustion_deployments(base_time: datetime) -> list[Deployment]:
    """Generate deployment records for DB exhaustion scenario.

    Args:
        base_time: Incident start time.

    Returns:
        list[Deployment]: Recent deployment records.
    """
    return [
        Deployment(
            deploy_id="deploy-2845",
            service="database-proxy",
            version="v1.3.0",
            timestamp=(base_time - timedelta(days=7)).isoformat(),
            deployed_by="ci-pipeline",
            change_summary="Connection pool size update and query optimization",
            rollback_available=True,
        ),
    ]


def generate_network_partition_deployments(base_time: datetime) -> list[Deployment]:
    """Generate deployment records for network partition scenario.

    Args:
        base_time: Incident start time.

    Returns:
        list[Deployment]: Recent deployment records.
    """
    return [
        Deployment(
            deploy_id="deploy-2844",
            service="inventory-service",
            version="v2.1.0",
            timestamp=(base_time - timedelta(days=4)).isoformat(),
            deployed_by="ci-pipeline",
            change_summary="Added new stock reservation endpoint",
            rollback_available=True,
        ),
    ]


def generate_cpu_spike_deployments(base_time: datetime) -> list[Deployment]:
    """Generate deployment records for CPU spike scenario.

    Args:
        base_time: Incident start time.

    Returns:
        list[Deployment]: Recent deployment records.
    """
    return [
        Deployment(
            deploy_id="deploy-2843",
            service="payment-service",
            version="v4.0.2",
            timestamp=(base_time - timedelta(days=1)).isoformat(),
            deployed_by="ci-pipeline",
            change_summary="Added retry logic for failed payment processing",
            rollback_available=True,
        ),
    ]
