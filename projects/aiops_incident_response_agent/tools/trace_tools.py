"""Tools for querying distributed traces and deployment records.

These tools are used by the Root Cause Analyzer Agent to correlate
signals across services and identify temporal relationships.
"""

import json
import logging
from dataclasses import asdict

from agents import RunContextWrapper, function_tool

from aiops_incident_response_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


@function_tool
def query_traces(
    ctx: RunContextWrapper[ScenarioData],
    service: str = "",
    status: str = "",
) -> str:
    """Query distributed trace spans, optionally filtered by service and status.

    Returns trace spans showing request flow across microservices.
    Each span includes trace_id, service, operation, duration, status,
    and error messages.

    Args:
        ctx: Run context containing the scenario data.
        service: Filter by service name (empty for all).
        status: Filter by span status - ok, error, timeout (empty for all).

    Returns:
        str: JSON string of trace spans.
    """
    scenario = ctx.context
    traces = scenario.traces

    if service:
        traces = [t for t in traces if t.service == service]
    if status:
        traces = [t for t in traces if t.status == status]

    logger.info("Queried %d trace spans (service=%s, status=%s)", len(traces), service, status)
    return json.dumps([asdict(t) for t in traces], indent=2)


@function_tool
def get_recent_deployments(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Get recent deployment records across all services.

    Returns deployment records including service, version, timestamp,
    change summary, and whether rollback is available. Use this to
    check if a recent deployment may have caused the incident.

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string of recent deployments.
    """
    scenario = ctx.context
    logger.info("Fetching %d recent deployments", len(scenario.deployments))
    return json.dumps([asdict(d) for d in scenario.deployments], indent=2)


@function_tool
def correlate_signals(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Correlate signals across logs, metrics, alerts, and traces.

    Produces a cross-signal correlation summary identifying:
    - Services appearing in multiple signal types
    - Temporal correlations between alerts and errors
    - Trace errors matching log patterns

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string of correlation findings.
    """
    scenario = ctx.context

    # Services with errors in logs
    log_error_services = set()
    for log in scenario.logs:
        if log.level in ("ERROR", "FATAL"):
            log_error_services.add(log.service)

    # Services with critical/warning alerts
    alert_services = set()
    for alert in scenario.alerts:
        if alert.severity in ("critical", "warning"):
            alert_services.add(alert.service)

    # Services with trace errors
    trace_error_services = set()
    for trace in scenario.traces:
        if trace.status in ("error", "timeout"):
            trace_error_services.add(trace.service)

    # Services in critical/degraded health
    unhealthy_services = set()
    for health in scenario.service_health:
        if health.status in ("critical", "degraded"):
            unhealthy_services.add(health.service)

    # Find services appearing across multiple signal types
    all_services = log_error_services | alert_services | trace_error_services | unhealthy_services
    correlations = []
    for svc in all_services:
        signals = []
        if svc in log_error_services:
            signals.append("log_errors")
        if svc in alert_services:
            signals.append("alerts")
        if svc in trace_error_services:
            signals.append("trace_errors")
        if svc in unhealthy_services:
            signals.append("unhealthy")
        correlations.append({
            "service": svc,
            "signal_types": signals,
            "signal_count": len(signals),
        })

    correlations.sort(key=lambda c: c["signal_count"], reverse=True)

    # Timeline of significant events
    events = []
    for alert in scenario.alerts:
        events.append({
            "timestamp": alert.timestamp,
            "type": "alert",
            "service": alert.service,
            "severity": alert.severity,
            "message": alert.message,
        })
    for deploy in scenario.deployments:
        events.append({
            "timestamp": deploy.timestamp,
            "type": "deployment",
            "service": deploy.service,
            "message": f"Deployed {deploy.version}: {deploy.change_summary}",
        })
    events.sort(key=lambda e: e["timestamp"])

    result = {
        "service_correlations": correlations,
        "event_timeline": events,
        "most_affected_service": correlations[0]["service"] if correlations else "unknown",
    }

    logger.info("Correlated signals across %d services", len(correlations))
    return json.dumps(result, indent=2)
