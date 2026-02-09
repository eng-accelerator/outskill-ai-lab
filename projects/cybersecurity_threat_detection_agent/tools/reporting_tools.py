"""Tools for generating SOC incident reports and timelines.

These tools are used by the SOC Report Agent to produce the final
structured incident report with timeline and threat scoring.
"""

import json
import logging

from agents import RunContextWrapper, function_tool
from cybersecurity_threat_detection_agent.simulators.scenario_engine import \
    ScenarioData

logger = logging.getLogger(__name__)


@function_tool
def generate_threat_timeline(
    ctx: RunContextWrapper[ScenarioData],
    events_json: str,
) -> str:
    """Generate a formatted chronological threat timeline.

    Takes a JSON array of events and produces a formatted timeline string.
    Each event should have 'timestamp', 'type', and 'description' fields.

    Args:
        ctx: Run context containing the scenario data.
        events_json: JSON string of events, each with timestamp, type, and description.

    Returns:
        str: Formatted timeline string.
    """
    logger.info("Generating threat timeline")

    events = json.loads(events_json)
    events.sort(key=lambda e: e.get("timestamp", ""))

    timeline_lines = []
    for event in events:
        ts = event.get("timestamp", "unknown")
        event_type = event.get("type", "event")
        description = event.get("description", "")
        timeline_lines.append(f"[{ts}] [{event_type.upper()}] {description}")

    timeline = "\n".join(timeline_lines)
    logger.info("Generated timeline with %d events", len(events))
    return timeline


@function_tool
def format_soc_report(
    ctx: RunContextWrapper[ScenarioData],
    title: str,
    severity: str,
    threat_score: int,
    summary: str,
    mitre_techniques: str,
    affected_assets: str,
    timeline: str,
    containment_actions: str,
    evidence: str,
    status: str = "investigating",
) -> str:
    """Format a structured SOC incident report.

    Compiles all incident information into a standardized SOC report format.

    Args:
        ctx: Run context containing the scenario data.
        title: Descriptive incident title.
        severity: Threat severity (critical, high, medium, low).
        threat_score: Numeric threat score (0-100).
        summary: Executive summary (2-3 sentences).
        mitre_techniques: Comma-separated MITRE ATT&CK technique references.
        affected_assets: Comma-separated list of affected assets.
        timeline: Formatted timeline string.
        containment_actions: Numbered list of containment actions.
        evidence: Key evidence items, one per line.
        status: Incident status (investigating, containing, contained, remediated).

    Returns:
        str: Formatted SOC incident report.
    """
    logger.info("Formatting SOC report: %s", title)

    report = f"""
{'='*70}
SOC INCIDENT REPORT
{'='*70}

TITLE: {title}
SEVERITY: {severity.upper()}
THREAT SCORE: {threat_score}/100
STATUS: {status.upper()}
SCENARIO: {ctx.context.scenario_type}

{'─'*70}
EXECUTIVE SUMMARY
{'─'*70}
{summary}

{'─'*70}
MITRE ATT&CK MAPPING
{'─'*70}
{mitre_techniques}

{'─'*70}
AFFECTED ASSETS
{'─'*70}
{affected_assets}

{'─'*70}
TIMELINE OF EVENTS
{'─'*70}
{timeline}

{'─'*70}
CONTAINMENT ACTIONS
{'─'*70}
{containment_actions}

{'─'*70}
EVIDENCE
{'─'*70}
{evidence}

{'='*70}
END OF REPORT
{'='*70}
"""

    logger.info("SOC report formatted successfully")
    return report.strip()
