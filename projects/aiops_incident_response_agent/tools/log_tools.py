"""Tools for querying and analyzing application logs.

These tools are used by the Log Analyzer Agent to investigate
error patterns, log volumes, and anomalies in application logs.
"""

import json
import logging
from collections import Counter
from dataclasses import asdict

from agents import RunContextWrapper, function_tool
from aiops_incident_response_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


@function_tool
def query_logs(
    ctx: RunContextWrapper[ScenarioData],
    service: str = "",
    level: str = "",
    limit: int = 50,
) -> str:
    """Query application logs, optionally filtered by service and log level.

    Returns recent log entries matching the filters. Each entry includes
    timestamp, service, level, message, trace_id, and metadata.

    Args:
        ctx: Run context containing the scenario data.
        service: Filter by service name (empty string for all services).
        level: Filter by log level - DEBUG, INFO, WARN, ERROR, FATAL (empty for all).
        limit: Maximum number of log entries to return (default 50).

    Returns:
        str: JSON string of matching log entries.
    """
    scenario = ctx.context
    logs = scenario.logs

    if service:
        logs = [l for l in logs if l.service == service]
    if level:
        logs = [l for l in logs if l.level == level]

    logs = logs[:limit]
    logger.info("Queried %d logs (service=%s, level=%s)", len(logs), service, level)
    return json.dumps([asdict(l) for l in logs], indent=2)


@function_tool
def search_error_patterns(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Search for recurring error patterns across all services.

    Analyzes ERROR and FATAL log entries to identify common error patterns,
    their frequency, affected services, and time ranges.

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string of detected error patterns with counts and details.
    """
    scenario = ctx.context
    error_logs = [l for l in scenario.logs if l.level in ("ERROR", "FATAL")]

    # Group by message prefix (first 60 chars) to detect patterns
    pattern_groups: dict[str, list] = {}
    for log in error_logs:
        key = log.message[:60]
        if key not in pattern_groups:
            pattern_groups[key] = []
        pattern_groups[key].append(log)

    patterns = []
    for pattern, entries in pattern_groups.items():
        services = list(set(e.service for e in entries))
        timestamps = [e.timestamp for e in entries]
        patterns.append(
            {
                "pattern": pattern,
                "count": len(entries),
                "first_seen": min(timestamps),
                "last_seen": max(timestamps),
                "services": services,
                "sample_message": entries[0].message,
            }
        )

    patterns.sort(key=lambda p: p["count"], reverse=True)
    logger.info("Found %d error patterns", len(patterns))
    return json.dumps(patterns, indent=2)


@function_tool
def get_log_statistics(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Get log volume statistics broken down by service and level.

    Provides aggregate counts of log entries per service per level,
    useful for identifying unusual log volume changes.

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string of log statistics per service.
    """
    scenario = ctx.context
    stats: dict[str, Counter] = {}

    for log in scenario.logs:
        if log.service not in stats:
            stats[log.service] = Counter()
        stats[log.service][log.level] += 1

    result = {}
    for service, counts in stats.items():
        result[service] = {
            "total": sum(counts.values()),
            "by_level": dict(counts),
            "error_ratio": round(
                (counts.get("ERROR", 0) + counts.get("FATAL", 0))
                / max(sum(counts.values()), 1),
                3,
            ),
        }

    logger.info("Computed log statistics for %d services", len(result))
    return json.dumps(result, indent=2)
