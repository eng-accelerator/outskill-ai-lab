"""Core security event types for the threat detection pipeline.

Defines the foundational data types for security alerts, asset information,
and threat classification used throughout the agent system.
"""

from dataclasses import dataclass, field
from typing import Literal

# Threat categories the system can detect
ThreatCategory = Literal[
    "brute_force",
    "credential_stuffing",
    "impossible_travel",
    "privilege_escalation",
    "api_misuse",
    "data_exfiltration",
    "malware",
    "c2_communication",
    "cloud_misconfiguration",
    "insider_threat",
]

# Severity levels for threats
ThreatSeverity = Literal["critical", "high", "medium", "low", "info"]

# Asset types in the environment
AssetType = Literal["server", "workstation", "cloud_resource", "network_device"]

# Asset criticality levels
AssetCriticality = Literal["critical", "high", "medium", "low"]


@dataclass(frozen=True)
class SecurityAlert:
    """A security alert from the SIEM or detection system.

    Attributes:
        alert_id: Unique identifier for the alert.
        source: Source system that generated the alert (e.g. 'siem', 'edr', 'waf').
        severity: Alert severity level.
        category: Threat category classification.
        message: Human-readable alert description.
        timestamp: ISO 8601 timestamp of when the alert fired.
        indicators: Key-value indicators of compromise (IPs, hashes, users, etc.).
    """

    alert_id: str
    source: str
    severity: ThreatSeverity
    category: ThreatCategory
    message: str
    timestamp: str
    indicators: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AssetInfo:
    """Information about an asset in the environment.

    Attributes:
        asset_id: Unique asset identifier.
        hostname: Hostname of the asset.
        ip_address: IP address of the asset.
        asset_type: Type of asset.
        owner: Owner or responsible team.
        criticality: Business criticality level.
    """

    asset_id: str
    hostname: str
    ip_address: str
    asset_type: AssetType
    owner: str
    criticality: AssetCriticality
