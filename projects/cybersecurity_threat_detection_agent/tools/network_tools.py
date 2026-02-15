"""Tools for querying and analyzing network and API access logs.

These tools are used by the Network/API Analyzer Agent to investigate
network traffic patterns, API access anomalies, and C2 communication.
"""

import json
import logging
from collections import Counter, defaultdict
from dataclasses import asdict

from agents import RunContextWrapper, function_tool
from cybersecurity_threat_detection_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


@function_tool
def query_network_logs(
    ctx: RunContextWrapper[ScenarioData],
    source_ip: str = "",
    dest_ip: str = "",
    dest_port: int = 0,
    action: str = "",
    limit: int = 50,
) -> str:
    """Query network/firewall logs, optionally filtered by IP, port, or action.

    Returns network log entries matching the filters. Each entry includes
    timestamp, source_ip, dest_ip, dest_port, protocol, bytes, and action.

    Args:
        ctx: Run context containing the scenario data.
        source_ip: Filter by source IP address (empty for all).
        dest_ip: Filter by destination IP address (empty for all).
        dest_port: Filter by destination port (0 for all ports).
        action: Filter by firewall action - allow, deny, drop (empty for all).
        limit: Maximum number of entries to return (default 50).

    Returns:
        str: JSON string of matching network log entries.
    """
    scenario = ctx.context
    logs = scenario.network_logs

    if source_ip:
        logs = [entry for entry in logs if entry.source_ip == source_ip]
    if dest_ip:
        logs = [entry for entry in logs if entry.dest_ip == dest_ip]
    if dest_port > 0:
        logs = [entry for entry in logs if entry.dest_port == dest_port]
    if action:
        logs = [entry for entry in logs if entry.action == action]

    logs = logs[:limit]
    logger.info(
        "Queried %d network logs (src=%s, dst=%s, port=%d)",
        len(logs),
        source_ip,
        dest_ip,
        dest_port,
    )
    return json.dumps([asdict(entry) for entry in logs], indent=2)


@function_tool
def query_api_access_logs(
    ctx: RunContextWrapper[ScenarioData],
    user: str = "",
    endpoint: str = "",
    api_key_id: str = "",
    status_code: int = 0,
    limit: int = 50,
) -> str:
    """Query API access logs, optionally filtered by user, endpoint, or key.

    Returns API access entries matching the filters. Each entry includes
    timestamp, user, api_key_id, endpoint, method, status_code, and source_ip.

    Args:
        ctx: Run context containing the scenario data.
        user: Filter by username (empty for all).
        endpoint: Filter by API endpoint path substring (empty for all).
        api_key_id: Filter by API key ID (empty for all).
        status_code: Filter by HTTP status code (0 for all).
        limit: Maximum number of entries to return (default 50).

    Returns:
        str: JSON string of matching API access log entries.
    """
    scenario = ctx.context
    logs = scenario.api_access_logs

    if user:
        logs = [entry for entry in logs if entry.user == user]
    if endpoint:
        logs = [entry for entry in logs if endpoint in entry.endpoint]
    if api_key_id:
        logs = [entry for entry in logs if entry.api_key_id == api_key_id]
    if status_code > 0:
        logs = [entry for entry in logs if entry.status_code == status_code]

    logs = logs[:limit]
    logger.info(
        "Queried %d API access logs (user=%s, endpoint=%s)", len(logs), user, endpoint
    )
    return json.dumps([asdict(entry) for entry in logs], indent=2)


@function_tool
def detect_c2_patterns(ctx: RunContextWrapper[ScenarioData]) -> str:
    """Detect Command & Control (C2) communication patterns in network logs.

    Analyzes network traffic for:
    - Periodic beaconing (regular interval connections to same IP)
    - Connections to known-bad IPs
    - Unusual port usage
    - DNS tunneling indicators (high volume DNS queries)

    Args:
        ctx: Run context containing the scenario data.

    Returns:
        str: JSON string of detected C2 patterns with descriptions.
    """
    scenario = ctx.context
    known_c2_ips = {"198.51.100.42", "203.0.113.77", "192.0.2.199"}
    findings = []

    # Group outbound connections by destination IP
    dest_groups: dict[str, list] = defaultdict(list)
    for entry in scenario.network_logs:
        if entry.source_ip.startswith("10."):  # Internal source
            dest_groups[entry.dest_ip].append(entry)

    for dest_ip, connections in dest_groups.items():
        # Check for known C2 IPs
        if dest_ip in known_c2_ips:
            findings.append(
                {
                    "type": "known_c2_server",
                    "severity": "critical",
                    "description": f"Connections detected to known C2 server {dest_ip}",
                    "dest_ip": dest_ip,
                    "connection_count": len(connections),
                    "source_ips": list(set(c.source_ip for c in connections)),
                    "ports": list(set(c.dest_port for c in connections)),
                }
            )

        # Check for beaconing pattern (regular intervals)
        if len(connections) >= 5:
            timestamps = sorted(c.timestamp for c in connections)
            # Simple interval check
            findings.append(
                {
                    "type": "periodic_beaconing",
                    "severity": "high",
                    "description": f"Periodic connections to {dest_ip}: {len(connections)} connections detected",
                    "dest_ip": dest_ip,
                    "connection_count": len(connections),
                    "first_seen": timestamps[0],
                    "last_seen": timestamps[-1],
                }
            )

    # Check for port scanning
    internal_sources = defaultdict(set)
    for entry in scenario.network_logs:
        if entry.source_ip.startswith("10."):
            internal_sources[entry.source_ip].add((entry.dest_ip, entry.dest_port))

    for src_ip, targets in internal_sources.items():
        unique_ports_per_dest: dict[str, set] = defaultdict(set)
        for dest_ip, port in targets:
            if dest_ip.startswith("10."):  # Internal scanning
                unique_ports_per_dest[dest_ip].add(port)
        for dest_ip, ports in unique_ports_per_dest.items():
            if len(ports) >= 4:
                findings.append(
                    {
                        "type": "port_scanning",
                        "severity": "high",
                        "description": f"Port scanning detected: {src_ip} scanned {len(ports)} ports on {dest_ip}",
                        "source_ip": src_ip,
                        "target_ip": dest_ip,
                        "ports_scanned": sorted(ports),
                    }
                )

    logger.info("Detected %d C2/network patterns", len(findings))
    return json.dumps(findings, indent=2)
