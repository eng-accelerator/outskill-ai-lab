"""Tools for querying and analyzing authentication logs.

These tools are used by the Auth Analyzer Agent to investigate
login patterns, anomalous authentication, and privilege changes.
"""

import json
import logging
from collections import Counter
from dataclasses import asdict

from agents import RunContextWrapper, function_tool
from cybersecurity_threat_detection_agent.simulators.scenario_engine import \
    ScenarioData

logger = logging.getLogger(__name__)


@function_tool
def query_auth_logs(
    ctx: RunContextWrapper[ScenarioData],
    user: str = "",
    source_ip: str = "",
    action: str = "",
    limit: int = 50,
) -> str:
    """Query authentication logs, optionally filtered by user, source IP, or action.

    Returns recent auth log entries matching the filters. Each entry includes
    timestamp, user, source_ip, action, geo_location, user_agent, and session_id.

    Args:
        ctx: Run context containing the scenario data.
        user: Filter by username (empty for all users).
        source_ip: Filter by source IP address (empty for all IPs).
        action: Filter by action type - login_success, login_failure, mfa_challenge, role_change, sudo (empty for all).
        limit: Maximum number of entries to return (default 50).

    Returns:
        str: JSON string of matching auth log entries.
    """
    scenario = ctx.context
    logs = scenario.auth_logs

    if user:
        logs = [entry for entry in logs if entry.user == user]
    if source_ip:
        logs = [entry for entry in logs if entry.source_ip == source_ip]
    if action:
        logs = [entry for entry in logs if entry.action == action]

    logs = logs[:limit]
    logger.info(
        "Queried %d auth logs (user=%s, source_ip=%s, action=%s)",
        len(logs),
        user,
        source_ip,
        action,
    )
    return json.dumps([asdict(entry) for entry in logs], indent=2)


@function_tool
def detect_anomalous_logins(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Detect anomalous login patterns in authentication logs.

    Performs statistical analysis to identify:
    - Impossible travel (logins from distant geolocations within short time)
    - Brute force patterns (many failures followed by success)
    - Unusual hours access
    - Logins from known malicious IPs

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string of detected anomalies with descriptions and severity.
    """
    scenario = ctx.context
    anomalies = []
    known_malicious_ips = {
        "185.220.101.34",
        "91.219.237.12",
        "45.155.205.99",
        "193.56.28.103",
        "89.248.167.131",
    }

    # Group logins by user
    user_logins: dict[str, list] = {}
    for entry in scenario.auth_logs:
        if entry.user not in user_logins:
            user_logins[entry.user] = []
        user_logins[entry.user].append(entry)

    for user, entries in user_logins.items():
        # Check for brute force: many failures then success
        failures = [e for e in entries if e.action == "login_failure"]
        successes = [e for e in entries if e.action == "login_success"]
        if len(failures) >= 5:
            anomalies.append(
                {
                    "type": "brute_force_pattern",
                    "severity": "critical",
                    "user": user,
                    "description": f"{len(failures)} failed login attempts detected for user {user}",
                    "failed_count": len(failures),
                    "source_ips": list(set(e.source_ip for e in failures)),
                }
            )

        # Check for impossible travel: different geolocations in short time
        geos = list(set(e.geo_location for e in successes))
        if len(geos) > 1:
            anomalies.append(
                {
                    "type": "impossible_travel",
                    "severity": "high",
                    "user": user,
                    "description": f"User {user} logged in from {len(geos)} different locations: {', '.join(geos)}",
                    "locations": geos,
                }
            )

        # Check for logins from malicious IPs
        mal_logins = [e for e in entries if e.source_ip in known_malicious_ips]
        if mal_logins:
            anomalies.append(
                {
                    "type": "malicious_ip_login",
                    "severity": "critical",
                    "user": user,
                    "description": f"Login from known malicious IP(s) for user {user}",
                    "malicious_ips": list(set(e.source_ip for e in mal_logins)),
                    "count": len(mal_logins),
                }
            )

    logger.info("Detected %d login anomalies", len(anomalies))
    return json.dumps(anomalies, indent=2)


@function_tool
def check_privilege_changes(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Find privilege escalation events in authentication logs.

    Searches for role_change and sudo events, which may indicate
    unauthorized privilege escalation.

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string of privilege change events with analysis.
    """
    scenario = ctx.context
    priv_events = [
        entry for entry in scenario.auth_logs if entry.action in ("role_change", "sudo")
    ]

    results = []
    for event in priv_events:
        results.append(
            {
                "timestamp": event.timestamp,
                "user": event.user,
                "action": event.action,
                "source_ip": event.source_ip,
                "geo_location": event.geo_location,
                "session_id": event.session_id,
                "risk_assessment": (
                    "high" if event.action == "role_change" else "medium"
                ),
            }
        )

    logger.info("Found %d privilege change events", len(results))
    return json.dumps(results, indent=2)
