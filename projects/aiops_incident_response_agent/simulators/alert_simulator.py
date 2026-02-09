"""Simulates realistic alert data from a monitoring system.

Generates alerts with severity levels, service attribution,
and correlated alert patterns for each incident scenario.
"""

import random
from datetime import datetime, timedelta

from aiops_incident_response_agent.models.incident import Alert, ServiceHealth

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


def _healthy_service(service: str) -> ServiceHealth:
    """Generate a healthy service health record.

    Args:
        service: Service name.

    Returns:
        ServiceHealth: Health record with normal values.
    """
    return ServiceHealth(
        service=service,
        status="healthy",
        cpu_percent=round(random.uniform(15, 40), 1),
        memory_percent=round(random.uniform(30, 55), 1),
        error_rate=round(random.uniform(0.01, 0.3), 2),
        latency_p99_ms=round(random.uniform(50, 200), 1),
        active_alerts=0,
    )


def generate_memory_leak_alerts(base_time: datetime) -> tuple[list[Alert], list[ServiceHealth]]:
    """Generate alerts and health summaries for a memory leak scenario.

    Args:
        base_time: Starting timestamp for the incident window.

    Returns:
        tuple: (list of alerts, list of service health records).
    """
    alerts = [
        Alert(
            alert_id="alert-001",
            service="order-service",
            severity="warning",
            message="Memory usage exceeds 80% threshold on order-service",
            timestamp=(base_time + timedelta(minutes=15)).isoformat(),
            labels={"alertname": "HighMemoryUsage", "pod": "order-service-pod-1"},
        ),
        Alert(
            alert_id="alert-002",
            service="order-service",
            severity="warning",
            message="GC pause time exceeds 200ms on order-service",
            timestamp=(base_time + timedelta(minutes=22)).isoformat(),
            labels={"alertname": "HighGCPause", "pod": "order-service-pod-1"},
        ),
        Alert(
            alert_id="alert-003",
            service="order-service",
            severity="critical",
            message="OOM Kill detected on order-service-pod-1",
            timestamp=(base_time + timedelta(minutes=35)).isoformat(),
            labels={"alertname": "OOMKill", "pod": "order-service-pod-1"},
        ),
        Alert(
            alert_id="alert-004",
            service="api-gateway",
            severity="warning",
            message="Elevated error rate on api-gateway: 503 responses from order-service",
            timestamp=(base_time + timedelta(minutes=36)).isoformat(),
            labels={"alertname": "HighErrorRate", "upstream": "order-service"},
        ),
        Alert(
            alert_id="alert-005",
            service="payment-service",
            severity="warning",
            message="Increased latency on payment-service due to order-service dependency",
            timestamp=(base_time + timedelta(minutes=36)).isoformat(),
            labels={"alertname": "HighLatency", "dependency": "order-service"},
        ),
    ]

    health = [
        ServiceHealth("order-service", "critical", 35.0, 98.5, 45.2, 8500.0, 3),
        ServiceHealth("api-gateway", "degraded", 30.0, 42.0, 12.5, 3200.0, 1),
        ServiceHealth("payment-service", "degraded", 28.0, 45.0, 5.3, 2100.0, 1),
    ]
    for svc in SERVICES:
        if svc not in ("order-service", "api-gateway", "payment-service"):
            health.append(_healthy_service(svc))

    return alerts, health


def generate_deployment_regression_alerts(
    base_time: datetime,
) -> tuple[list[Alert], list[ServiceHealth]]:
    """Generate alerts and health summaries for a deployment regression scenario.

    Args:
        base_time: Starting timestamp for the incident window.

    Returns:
        tuple: (list of alerts, list of service health records).
    """
    deploy_time = base_time + timedelta(minutes=10)
    alerts = [
        Alert(
            alert_id="alert-101",
            service="user-service",
            severity="info",
            message="Deployment completed: user-service v2.5.0",
            timestamp=deploy_time.isoformat(),
            labels={"alertname": "DeploymentComplete", "version": "v2.5.0"},
        ),
        Alert(
            alert_id="alert-102",
            service="user-service",
            severity="warning",
            message="Error rate spike detected on user-service after deployment",
            timestamp=(deploy_time + timedelta(minutes=3)).isoformat(),
            labels={"alertname": "ErrorRateSpike", "version": "v2.5.0"},
        ),
        Alert(
            alert_id="alert-103",
            service="user-service",
            severity="critical",
            message="Error rate exceeds critical threshold: 25 errors/s on user-service",
            timestamp=(deploy_time + timedelta(minutes=8)).isoformat(),
            labels={"alertname": "CriticalErrorRate", "version": "v2.5.0"},
        ),
        Alert(
            alert_id="alert-104",
            service="api-gateway",
            severity="warning",
            message="Elevated p99 latency on api-gateway for user-service routes",
            timestamp=(deploy_time + timedelta(minutes=5)).isoformat(),
            labels={"alertname": "HighLatency", "upstream": "user-service"},
        ),
    ]

    health = [
        ServiceHealth("user-service", "critical", 65.0, 58.0, 22.5, 2800.0, 2),
        ServiceHealth("api-gateway", "degraded", 32.0, 40.0, 8.0, 1500.0, 1),
    ]
    for svc in SERVICES:
        if svc not in ("user-service", "api-gateway"):
            health.append(_healthy_service(svc))

    return alerts, health


def generate_database_exhaustion_alerts(
    base_time: datetime,
) -> tuple[list[Alert], list[ServiceHealth]]:
    """Generate alerts and health summaries for DB connection pool exhaustion.

    Args:
        base_time: Starting timestamp for the incident window.

    Returns:
        tuple: (list of alerts, list of service health records).
    """
    alerts = [
        Alert(
            alert_id="alert-201",
            service="database-proxy",
            severity="warning",
            message="Connection pool usage at 85% on database-proxy",
            timestamp=(base_time + timedelta(minutes=18)).isoformat(),
            labels={"alertname": "HighPoolUsage", "pool": "primary"},
        ),
        Alert(
            alert_id="alert-202",
            service="database-proxy",
            severity="critical",
            message="Connection pool exhausted on database-proxy: 40/40 connections in use",
            timestamp=(base_time + timedelta(minutes=25)).isoformat(),
            labels={"alertname": "PoolExhausted", "pool": "primary"},
        ),
        Alert(
            alert_id="alert-203",
            service="order-service",
            severity="critical",
            message="Database query timeouts exceeding threshold on order-service",
            timestamp=(base_time + timedelta(minutes=26)).isoformat(),
            labels={"alertname": "DBQueryTimeout", "dependency": "database-proxy"},
        ),
        Alert(
            alert_id="alert-204",
            service="user-service",
            severity="warning",
            message="Elevated error rate on user-service due to database timeouts",
            timestamp=(base_time + timedelta(minutes=27)).isoformat(),
            labels={"alertname": "HighErrorRate", "dependency": "database-proxy"},
        ),
        Alert(
            alert_id="alert-205",
            service="payment-service",
            severity="warning",
            message="Payment processing failures due to database connectivity",
            timestamp=(base_time + timedelta(minutes=27)).isoformat(),
            labels={"alertname": "PaymentFailure", "dependency": "database-proxy"},
        ),
    ]

    health = [
        ServiceHealth("database-proxy", "critical", 45.0, 95.0, 38.0, 15000.0, 2),
        ServiceHealth("order-service", "critical", 30.0, 48.0, 28.0, 12000.0, 1),
        ServiceHealth("user-service", "degraded", 25.0, 42.0, 15.0, 5000.0, 1),
        ServiceHealth("payment-service", "degraded", 22.0, 40.0, 10.0, 8000.0, 1),
    ]
    for svc in SERVICES:
        if svc not in ("database-proxy", "order-service", "user-service", "payment-service"):
            health.append(_healthy_service(svc))

    return alerts, health


def generate_network_partition_alerts(
    base_time: datetime,
) -> tuple[list[Alert], list[ServiceHealth]]:
    """Generate alerts and health summaries for a network partition scenario.

    Args:
        base_time: Starting timestamp for the incident window.

    Returns:
        tuple: (list of alerts, list of service health records).
    """
    partition_time = base_time + timedelta(minutes=8)
    alerts = [
        Alert(
            alert_id="alert-301",
            service="inventory-service",
            severity="critical",
            message="inventory-service unreachable from api-gateway",
            timestamp=partition_time.isoformat(),
            labels={"alertname": "ServiceUnreachable", "source": "api-gateway"},
        ),
        Alert(
            alert_id="alert-302",
            service="inventory-service",
            severity="critical",
            message="inventory-service unreachable from order-service",
            timestamp=(partition_time + timedelta(seconds=15)).isoformat(),
            labels={"alertname": "ServiceUnreachable", "source": "order-service"},
        ),
        Alert(
            alert_id="alert-303",
            service="api-gateway",
            severity="warning",
            message="Connection refused errors to inventory-service",
            timestamp=(partition_time + timedelta(seconds=30)).isoformat(),
            labels={"alertname": "ConnectionRefused", "target": "inventory-service"},
        ),
        Alert(
            alert_id="alert-304",
            service="order-service",
            severity="warning",
            message="Order processing degraded: inventory checks failing",
            timestamp=(partition_time + timedelta(minutes=2)).isoformat(),
            labels={"alertname": "DependencyFailure", "dependency": "inventory-service"},
        ),
    ]

    health = [
        ServiceHealth("inventory-service", "unknown", 0.0, 0.0, 0.0, 0.0, 2),
        ServiceHealth("api-gateway", "degraded", 35.0, 40.0, 25.0, 8000.0, 1),
        ServiceHealth("order-service", "degraded", 28.0, 45.0, 18.0, 12000.0, 1),
    ]
    for svc in SERVICES:
        if svc not in ("inventory-service", "api-gateway", "order-service"):
            health.append(_healthy_service(svc))

    return alerts, health


def generate_cpu_spike_alerts(base_time: datetime) -> tuple[list[Alert], list[ServiceHealth]]:
    """Generate alerts and health summaries for a CPU spike scenario.

    Args:
        base_time: Starting timestamp for the incident window.

    Returns:
        tuple: (list of alerts, list of service health records).
    """
    spike_time = base_time + timedelta(minutes=5)
    alerts = [
        Alert(
            alert_id="alert-401",
            service="payment-service",
            severity="warning",
            message="CPU usage exceeds 80% on payment-service-pod-2",
            timestamp=spike_time.isoformat(),
            labels={"alertname": "HighCPU", "pod": "payment-service-pod-2"},
        ),
        Alert(
            alert_id="alert-402",
            service="payment-service",
            severity="critical",
            message="CPU usage at 95% on payment-service-pod-2 - request queue growing",
            timestamp=(spike_time + timedelta(minutes=5)).isoformat(),
            labels={"alertname": "CriticalCPU", "pod": "payment-service-pod-2"},
        ),
        Alert(
            alert_id="alert-403",
            service="payment-service",
            severity="critical",
            message="Payment processing timeout rate exceeds 50%",
            timestamp=(spike_time + timedelta(minutes=7)).isoformat(),
            labels={"alertname": "HighTimeoutRate", "pod": "payment-service-pod-2"},
        ),
        Alert(
            alert_id="alert-404",
            service="api-gateway",
            severity="warning",
            message="Elevated latency for payment routes on api-gateway",
            timestamp=(spike_time + timedelta(minutes=6)).isoformat(),
            labels={"alertname": "HighLatency", "upstream": "payment-service"},
        ),
    ]

    health = [
        ServiceHealth("payment-service", "critical", 95.0, 48.0, 12.0, 9500.0, 3),
        ServiceHealth("api-gateway", "degraded", 30.0, 40.0, 5.0, 4500.0, 1),
    ]
    for svc in SERVICES:
        if svc not in ("payment-service", "api-gateway"):
            health.append(_healthy_service(svc))

    return alerts, health
