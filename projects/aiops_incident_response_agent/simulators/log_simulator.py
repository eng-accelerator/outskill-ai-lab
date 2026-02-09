"""Simulates realistic application log data for incident scenarios.

Generates structured JSON log entries with error patterns, stack traces,
and correlated events across microservices.
"""

import json
import random
from datetime import datetime, timedelta, timezone

from aiops_incident_response_agent.models.analysis import LogEntry

# Realistic service names for a microservice architecture
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

# Common log message templates by level
LOG_TEMPLATES: dict[str, list[str]] = {
    "INFO": [
        "Request processed successfully in %dms",
        "Health check passed for %s",
        "Connection pool stats: active=%d, idle=%d",
        "Cache hit ratio: %.2f%%",
        "Processed %d messages from queue",
    ],
    "WARN": [
        "Slow query detected: %dms (threshold: 500ms)",
        "Connection pool nearing capacity: %d/%d",
        "Retry attempt %d for downstream call to %s",
        "Memory usage at %.1f%% - approaching threshold",
        "Request queue depth increasing: %d pending",
    ],
    "ERROR": [
        "Connection refused to %s:%d",
        "Timeout after %dms waiting for response from %s",
        "OutOfMemoryError: Java heap space",
        "Database connection pool exhausted: max=%d, active=%d",
        "HTTP 503 from %s: Service Unavailable",
        "Failed to process request: %s",
        "Socket timeout connecting to %s",
        "NullPointerException in %s.%s()",
    ],
    "FATAL": [
        "OOM Kill: process %s exceeded memory limit (%dMB)",
        "Unrecoverable error in %s - shutting down",
        "Data corruption detected in %s",
        "Panic: runtime error in %s",
    ],
}

STACK_TRACES = [
    (
        "java.lang.OutOfMemoryError: Java heap space\n"
        "  at java.util.Arrays.copyOf(Arrays.java:3236)\n"
        "  at com.service.cache.InMemoryCache.put(InMemoryCache.java:142)\n"
        "  at com.service.handler.RequestHandler.process(RequestHandler.java:87)"
    ),
    (
        "ConnectionPoolExhaustedException: No available connections\n"
        "  at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:155)\n"
        "  at com.service.db.DatabaseClient.query(DatabaseClient.java:43)\n"
        "  at com.service.repository.OrderRepo.findById(OrderRepo.java:28)"
    ),
    (
        "java.net.SocketTimeoutException: connect timed out\n"
        "  at java.net.Socket.connect(Socket.java:589)\n"
        "  at com.service.http.HttpClient.execute(HttpClient.java:112)\n"
        "  at com.service.gateway.DownstreamProxy.forward(DownstreamProxy.java:67)"
    ),
    (
        "io.grpc.StatusRuntimeException: UNAVAILABLE: upstream connect error\n"
        "  at io.grpc.stub.ClientCalls.toStatusRuntimeException(ClientCalls.java:262)\n"
        "  at com.service.rpc.GrpcClient.call(GrpcClient.java:95)\n"
        "  at com.service.inventory.StockChecker.check(StockChecker.java:31)"
    ),
]


def _generate_baseline_logs(
    base_time: datetime, service: str, count: int
) -> list[LogEntry]:
    """Generate normal baseline log entries for a service.

    Args:
        base_time: Starting timestamp for log generation.
        service: Service name to generate logs for.
        count: Number of log entries to generate.

    Returns:
        list[LogEntry]: Generated baseline log entries.
    """
    entries = []
    for i in range(count):
        ts = base_time + timedelta(seconds=random.randint(0, 300))
        level = random.choices(
            ["DEBUG", "INFO", "WARN", "ERROR"],
            weights=[10, 70, 15, 5],
        )[0]
        template = random.choice(LOG_TEMPLATES.get(level, LOG_TEMPLATES["INFO"]))
        # Fill in template placeholders with realistic values
        msg = _fill_template(template, service)
        entries.append(
            LogEntry(
                timestamp=ts.isoformat(),
                service=service,
                level=level,
                message=msg,
                trace_id=f"trace-{random.randint(10000, 99999)}",
                metadata={"host": f"{service}-pod-{random.randint(1, 3)}"},
            )
        )
    return entries


def _fill_template(template: str, service: str) -> str:
    """Fill a log message template with realistic random values.

    Args:
        template: Log message template with format specifiers.
        service: Service name for context.

    Returns:
        str: Filled log message.
    """
    count = template.count("%")
    if count == 0:
        return template
    args: list[object] = []
    for spec in _extract_format_specs(template):
        match spec:
            case "d":
                args.append(random.randint(1, 5000))
            case "s":
                args.append(random.choice(SERVICES))
            case ".1f" | ".2f":
                args.append(random.uniform(10.0, 99.0))
            case _:
                args.append(random.randint(1, 100))
    return template % tuple(args)


def _extract_format_specs(template: str) -> list[str]:
    """Extract format specifiers from a printf-style template.

    Args:
        template: Printf-style format string.

    Returns:
        list[str]: List of format specifier characters.
    """
    specs = []
    i = 0
    while i < len(template):
        if template[i] == "%":
            i += 1
            spec = ""
            while i < len(template) and template[i] not in "dsfx%":
                spec += template[i]
                i += 1
            if i < len(template) and template[i] != "%":
                specs.append(spec + template[i])
            i += 1
        else:
            i += 1
    return specs


def generate_memory_leak_logs(base_time: datetime) -> list[LogEntry]:
    """Generate logs consistent with a memory leak scenario.

    Produces gradually increasing WARN/ERROR logs about memory,
    followed by OOM kills on the affected service.

    Args:
        base_time: Starting timestamp for the incident window.

    Returns:
        list[LogEntry]: Correlated log entries showing memory leak progression.
    """
    entries = []
    target_service = "order-service"

    # Normal logs from other services
    for svc in SERVICES:
        if svc != target_service:
            entries.extend(_generate_baseline_logs(base_time, svc, 8))

    # Escalating memory warnings
    for i in range(6):
        ts = base_time + timedelta(minutes=i * 5)
        mem_pct = 60.0 + i * 7.0
        entries.append(
            LogEntry(
                timestamp=ts.isoformat(),
                service=target_service,
                level="WARN",
                message=f"Memory usage at {mem_pct:.1f}% - approaching threshold",
                trace_id=f"trace-{random.randint(10000, 99999)}",
                metadata={
                    "host": "order-service-pod-1",
                    "heap_mb": str(int(mem_pct * 20)),
                },
            )
        )

    # GC pressure logs
    for i in range(4):
        ts = base_time + timedelta(minutes=20 + i * 3)
        entries.append(
            LogEntry(
                timestamp=ts.isoformat(),
                service=target_service,
                level="WARN",
                message=f"GC pause exceeded threshold: {200 + i * 150}ms (limit: 200ms)",
                trace_id=f"trace-{random.randint(10000, 99999)}",
                metadata={"host": "order-service-pod-1", "gc_type": "full"},
            )
        )

    # OOM errors
    ts_oom = base_time + timedelta(minutes=35)
    entries.append(
        LogEntry(
            timestamp=ts_oom.isoformat(),
            service=target_service,
            level="ERROR",
            message="OutOfMemoryError: Java heap space",
            trace_id=f"trace-{random.randint(10000, 99999)}",
            metadata={
                "host": "order-service-pod-1",
                "stack_trace": STACK_TRACES[0],
            },
        )
    )
    entries.append(
        LogEntry(
            timestamp=(ts_oom + timedelta(seconds=5)).isoformat(),
            service=target_service,
            level="FATAL",
            message="OOM Kill: process order-service exceeded memory limit (2048MB)",
            trace_id=f"trace-{random.randint(10000, 99999)}",
            metadata={"host": "order-service-pod-1", "exit_code": "137"},
        )
    )

    # Cascading errors on dependent services
    for svc in ["api-gateway", "payment-service"]:
        ts_cascade = ts_oom + timedelta(seconds=random.randint(10, 30))
        entries.append(
            LogEntry(
                timestamp=ts_cascade.isoformat(),
                service=svc,
                level="ERROR",
                message=f"HTTP 503 from order-service: Service Unavailable",
                trace_id=f"trace-{random.randint(10000, 99999)}",
                metadata={"host": f"{svc}-pod-1"},
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_deployment_regression_logs(base_time: datetime) -> list[LogEntry]:
    """Generate logs consistent with a deployment regression scenario.

    Produces a spike in errors shortly after a deployment event.

    Args:
        base_time: Starting timestamp for the incident window.

    Returns:
        list[LogEntry]: Correlated log entries showing deployment regression.
    """
    entries = []
    target_service = "user-service"

    # Normal baseline before deploy
    for svc in SERVICES:
        entries.extend(_generate_baseline_logs(base_time, svc, 6))

    # Deployment event
    deploy_time = base_time + timedelta(minutes=10)
    entries.append(
        LogEntry(
            timestamp=deploy_time.isoformat(),
            service=target_service,
            level="INFO",
            message="Deployment started: version v2.4.1 -> v2.5.0",
            metadata={"deploy_id": "deploy-2847", "deployed_by": "ci-pipeline"},
        )
    )
    entries.append(
        LogEntry(
            timestamp=(deploy_time + timedelta(seconds=45)).isoformat(),
            service=target_service,
            level="INFO",
            message="Deployment completed: v2.5.0 rolling update finished",
            metadata={"deploy_id": "deploy-2847"},
        )
    )

    # Post-deploy errors
    for i in range(10):
        ts = deploy_time + timedelta(minutes=2 + i)
        entries.append(
            LogEntry(
                timestamp=ts.isoformat(),
                service=target_service,
                level="ERROR",
                message=random.choice(
                    [
                        "NullPointerException in UserController.getProfile()",
                        "Failed to process request: invalid auth token format",
                        f"Timeout after {random.randint(5000, 15000)}ms waiting for response from database-proxy",
                    ]
                ),
                trace_id=f"trace-{random.randint(10000, 99999)}",
                metadata={
                    "host": f"user-service-pod-{random.randint(1, 3)}",
                    "version": "v2.5.0",
                    "stack_trace": STACK_TRACES[2] if i % 3 == 0 else "",
                },
            )
        )

    # Latency warnings on gateway
    for i in range(5):
        ts = deploy_time + timedelta(minutes=3 + i * 2)
        entries.append(
            LogEntry(
                timestamp=ts.isoformat(),
                service="api-gateway",
                level="WARN",
                message=f"Slow query detected: {2000 + i * 500}ms (threshold: 500ms)",
                trace_id=f"trace-{random.randint(10000, 99999)}",
                metadata={"upstream": "user-service"},
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_database_exhaustion_logs(base_time: datetime) -> list[LogEntry]:
    """Generate logs consistent with database connection pool exhaustion.

    Args:
        base_time: Starting timestamp for the incident window.

    Returns:
        list[LogEntry]: Correlated log entries showing DB pool exhaustion.
    """
    entries = []

    for svc in SERVICES:
        entries.extend(_generate_baseline_logs(base_time, svc, 5))

    # Gradual pool warnings
    for i in range(8):
        ts = base_time + timedelta(minutes=i * 3)
        active = 15 + i * 3
        entries.append(
            LogEntry(
                timestamp=ts.isoformat(),
                service="database-proxy",
                level="WARN",
                message=f"Connection pool nearing capacity: {active}/40",
                trace_id=f"trace-{random.randint(10000, 99999)}",
                metadata={"host": "database-proxy-pod-1", "pool": "primary"},
            )
        )

    # Pool exhausted errors
    exhaust_time = base_time + timedelta(minutes=25)
    for i in range(6):
        ts = exhaust_time + timedelta(seconds=i * 10)
        entries.append(
            LogEntry(
                timestamp=ts.isoformat(),
                service="database-proxy",
                level="ERROR",
                message="Database connection pool exhausted: max=40, active=40",
                trace_id=f"trace-{random.randint(10000, 99999)}",
                metadata={
                    "host": "database-proxy-pod-1",
                    "stack_trace": STACK_TRACES[1],
                    "waiting_threads": str(5 + i * 3),
                },
            )
        )

    # Cascading timeouts
    for svc in ["order-service", "user-service", "payment-service"]:
        for i in range(3):
            ts = exhaust_time + timedelta(seconds=30 + i * 15)
            entries.append(
                LogEntry(
                    timestamp=ts.isoformat(),
                    service=svc,
                    level="ERROR",
                    message=f"Timeout after {5000 + random.randint(0, 5000)}ms waiting for response from database-proxy",
                    trace_id=f"trace-{random.randint(10000, 99999)}",
                    metadata={"host": f"{svc}-pod-{random.randint(1, 3)}"},
                )
            )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_network_partition_logs(base_time: datetime) -> list[LogEntry]:
    """Generate logs consistent with a network partition scenario.

    Args:
        base_time: Starting timestamp for the incident window.

    Returns:
        list[LogEntry]: Correlated log entries showing network partition.
    """
    entries = []

    for svc in SERVICES:
        entries.extend(_generate_baseline_logs(base_time, svc, 5))

    partition_time = base_time + timedelta(minutes=8)
    affected_pairs = [
        ("api-gateway", "inventory-service"),
        ("order-service", "inventory-service"),
        ("notification-service", "inventory-service"),
    ]

    for src, dst in affected_pairs:
        for i in range(6):
            ts = partition_time + timedelta(seconds=i * random.randint(5, 20))
            entries.append(
                LogEntry(
                    timestamp=ts.isoformat(),
                    service=src,
                    level="ERROR",
                    message=f"Connection refused to {dst}:8080",
                    trace_id=f"trace-{random.randint(10000, 99999)}",
                    metadata={"host": f"{src}-pod-1", "error_code": "ECONNREFUSED"},
                )
            )
            # Retries
            entries.append(
                LogEntry(
                    timestamp=(ts + timedelta(seconds=2)).isoformat(),
                    service=src,
                    level="WARN",
                    message=f"Retry attempt {i + 1} for downstream call to {dst}",
                    trace_id=f"trace-{random.randint(10000, 99999)}",
                    metadata={"host": f"{src}-pod-1"},
                )
            )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_cpu_spike_logs(base_time: datetime) -> list[LogEntry]:
    """Generate logs consistent with a CPU spike scenario.

    Args:
        base_time: Starting timestamp for the incident window.

    Returns:
        list[LogEntry]: Correlated log entries showing CPU saturation.
    """
    entries = []
    target_service = "payment-service"

    for svc in SERVICES:
        entries.extend(_generate_baseline_logs(base_time, svc, 5))

    spike_time = base_time + timedelta(minutes=5)

    # CPU warnings
    for i in range(5):
        ts = spike_time + timedelta(minutes=i)
        entries.append(
            LogEntry(
                timestamp=ts.isoformat(),
                service=target_service,
                level="WARN",
                message=f"Request queue depth increasing: {50 + i * 40} pending",
                trace_id=f"trace-{random.randint(10000, 99999)}",
                metadata={
                    "host": "payment-service-pod-2",
                    "cpu_percent": str(75 + i * 5),
                },
            )
        )

    # Timeout errors due to CPU saturation
    for i in range(8):
        ts = spike_time + timedelta(minutes=3, seconds=i * 15)
        entries.append(
            LogEntry(
                timestamp=ts.isoformat(),
                service=target_service,
                level="ERROR",
                message=f"Timeout after {8000 + random.randint(0, 7000)}ms waiting for response from payment-service",
                trace_id=f"trace-{random.randint(10000, 99999)}",
                metadata={
                    "host": "payment-service-pod-2",
                    "thread_count": str(200 + i * 10),
                },
            )
        )

    # Gateway sees slow responses
    for i in range(4):
        ts = spike_time + timedelta(minutes=4, seconds=i * 20)
        entries.append(
            LogEntry(
                timestamp=ts.isoformat(),
                service="api-gateway",
                level="WARN",
                message=f"Slow query detected: {3000 + i * 1000}ms (threshold: 500ms)",
                trace_id=f"trace-{random.randint(10000, 99999)}",
                metadata={"upstream": "payment-service"},
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)
