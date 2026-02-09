"""Tools for generating incident reports and notifications.

These tools are used by the Incident Reporter Agent to format
final reports and communication drafts.
"""

import json
import logging
from datetime import datetime, timezone

from agents import function_tool

logger = logging.getLogger(__name__)


@function_tool
def format_incident_report(
    title: str,
    severity: str,
    summary: str,
    root_cause: str,
    affected_services: str,
    timeline: str,
    remediation_actions: str,
    status: str = "investigating",
) -> str:
    """Format a structured incident report.

    Generates a formatted incident report suitable for stakeholder
    communication and post-incident review.

    Args:
        title: Incident title.
        severity: Incident severity (P0-P3).
        summary: Brief incident summary.
        root_cause: Identified root cause.
        affected_services: Comma-separated list of affected services.
        timeline: Key events timeline (newline-separated).
        remediation_actions: Actions taken or proposed (newline-separated).
        status: Current incident status.

    Returns:
        str: Formatted incident report as a string.
    """
    logger.info("Formatting incident report: %s", title)
    now = datetime.now(timezone.utc).isoformat()

    report = f"""
================================================================================
                         INCIDENT REPORT
================================================================================

Title:              {title}
Severity:           {severity}
Status:             {status}
Report Generated:   {now}

--------------------------------------------------------------------------------
SUMMARY
--------------------------------------------------------------------------------
{summary}

--------------------------------------------------------------------------------
ROOT CAUSE
--------------------------------------------------------------------------------
{root_cause}

--------------------------------------------------------------------------------
AFFECTED SERVICES
--------------------------------------------------------------------------------
{affected_services}

--------------------------------------------------------------------------------
TIMELINE
--------------------------------------------------------------------------------
{timeline}

--------------------------------------------------------------------------------
REMEDIATION ACTIONS
--------------------------------------------------------------------------------
{remediation_actions}

================================================================================
"""
    return report


@function_tool
def generate_timeline(events: str) -> str:
    """Generate a formatted timeline from a list of events.

    Takes a JSON string of events (each with timestamp, type, message)
    and produces a human-readable chronological timeline.

    Args:
        events: JSON string of events, each with 'timestamp', 'type', and 'message' fields.

    Returns:
        str: Formatted timeline string.
    """
    logger.info("Generating incident timeline")
    parsed_events = json.loads(events)

    sorted_events = sorted(parsed_events, key=lambda e: e.get("timestamp", ""))

    lines = []
    for event in sorted_events:
        ts = event.get("timestamp", "unknown")
        event_type = event.get("type", "event")
        message = event.get("message", "")
        lines.append(f"[{ts}] [{event_type.upper()}] {message}")

    return "\n".join(lines)
