"""Scenario engine that orchestrates realistic cybersecurity threat scenarios.

Coordinates all simulators to produce correlated security event data
(auth logs, network logs, API access logs, endpoint events, cloud audit entries)
for a given threat scenario type.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from cybersecurity_threat_detection_agent.models.analysis import (
    APIAccessEntry,
    AuthLogEntry,
    CloudAuditEntry,
    EndpointEvent,
    NetworkLogEntry,
)
from cybersecurity_threat_detection_agent.models.events import AssetInfo, SecurityAlert
from cybersecurity_threat_detection_agent.simulators.api_access_simulator import (
    generate_api_key_compromise_api_logs,
    generate_brute_force_api_logs,
    generate_cloud_misconfig_api_logs,
    generate_insider_threat_api_logs,
    generate_malware_api_logs,
)
from cybersecurity_threat_detection_agent.simulators.auth_log_simulator import (
    generate_api_key_compromise_auth_logs,
    generate_brute_force_auth_logs,
    generate_cloud_misconfig_auth_logs,
    generate_insider_threat_auth_logs,
    generate_malware_auth_logs,
)
from cybersecurity_threat_detection_agent.simulators.cloud_audit_simulator import (
    generate_api_key_compromise_cloud_audit,
    generate_brute_force_cloud_audit,
    generate_cloud_misconfig_cloud_audit,
    generate_insider_threat_cloud_audit,
    generate_malware_cloud_audit,
)
from cybersecurity_threat_detection_agent.simulators.endpoint_simulator import (
    generate_api_key_compromise_endpoint_events,
    generate_brute_force_endpoint_events,
    generate_cloud_misconfig_endpoint_events,
    generate_insider_threat_endpoint_events,
    generate_malware_endpoint_events,
)
from cybersecurity_threat_detection_agent.simulators.network_log_simulator import (
    generate_api_key_compromise_network_logs,
    generate_brute_force_network_logs,
    generate_cloud_misconfig_network_logs,
    generate_insider_threat_network_logs,
    generate_malware_network_logs,
)

logger = logging.getLogger(__name__)

# Supported scenario types
ScenarioType = Literal[
    "brute_force_attack",
    "insider_threat",
    "api_key_compromise",
    "malware_lateral_movement",
    "cloud_misconfiguration",
]

SCENARIO_DESCRIPTIONS: dict[ScenarioType, str] = {
    "brute_force_attack": (
        "Brute force attack against admin accounts from botnet IPs. "
        "One account compromised, followed by lateral movement to internal systems."
    ),
    "insider_threat": (
        "Employee escalates own privileges via IAM, accesses sensitive APIs "
        "beyond their role, and exfiltrates customer data via API and cloud storage."
    ),
    "api_key_compromise": (
        "Leaked production API key used from foreign IP for mass data extraction. "
        "Attacker attempts key rotation to maintain persistence."
    ),
    "malware_lateral_movement": (
        "Phishing email delivers macro-enabled document, spawning Cobalt Strike beacon. "
        "Credential dumping with Mimikatz, lateral movement via PsExec, C2 beaconing."
    ),
    "cloud_misconfiguration": (
        "S3 bucket policy changed to public access, exposing customer data. "
        "Security group opened to 0.0.0.0/0, external actors access sensitive data."
    ),
}


def _generate_alerts(
    scenario_type: ScenarioType, base_time: datetime
) -> list[SecurityAlert]:
    """Generate security alerts for a given scenario type.

    Args:
        scenario_type: The type of threat scenario.
        base_time: Starting timestamp for alert generation.

    Returns:
        list[SecurityAlert]: Generated security alerts.
    """
    ts = base_time.isoformat()

    match scenario_type:
        case "brute_force_attack":
            return [
                SecurityAlert(
                    alert_id="ALERT-BF-001",
                    source="siem",
                    severity="critical",
                    category="brute_force",
                    message="Multiple failed login attempts detected for admin account from 6 distinct external IPs",
                    timestamp=ts,
                    indicators={
                        "target_user": "admin",
                        "source_ips": "185.220.101.34,91.219.237.12,45.155.205.99",
                        "failed_attempts": "30",
                    },
                ),
                SecurityAlert(
                    alert_id="ALERT-BF-002",
                    source="siem",
                    severity="high",
                    category="brute_force",
                    message="Successful login to admin account from known malicious IP after brute force pattern",
                    timestamp=ts,
                    indicators={
                        "user": "admin",
                        "source_ip": "185.220.101.34",
                        "geo": "Moscow, RU",
                    },
                ),
                SecurityAlert(
                    alert_id="ALERT-BF-003",
                    source="edr",
                    severity="medium",
                    category="credential_stuffing",
                    message="Lateral movement detected: admin session used to access jsmith and mchen accounts",
                    timestamp=ts,
                    indicators={
                        "source_ip": "185.220.101.34",
                        "target_users": "jsmith,mchen",
                    },
                ),
            ]
        case "insider_threat":
            return [
                SecurityAlert(
                    alert_id="ALERT-IT-001",
                    source="siem",
                    severity="high",
                    category="privilege_escalation",
                    message="User kpatel performed self-privilege escalation via IAM role attachment",
                    timestamp=ts,
                    indicators={
                        "user": "kpatel",
                        "action": "iam:AttachRolePolicy",
                        "target_role": "admin-role",
                    },
                ),
                SecurityAlert(
                    alert_id="ALERT-IT-002",
                    source="waf",
                    severity="high",
                    category="api_misuse",
                    message="User kpatel accessing admin API endpoints beyond assigned scope",
                    timestamp=ts,
                    indicators={
                        "user": "kpatel",
                        "endpoints": "/api/v1/admin/secrets,/api/v1/admin/users",
                    },
                ),
                SecurityAlert(
                    alert_id="ALERT-IT-003",
                    source="dlp",
                    severity="critical",
                    category="data_exfiltration",
                    message="Bulk data export detected: 6 large files downloaded from confidential S3 bucket",
                    timestamp=ts,
                    indicators={
                        "user": "kpatel",
                        "bucket": "confidential-data",
                        "files_count": "6",
                    },
                ),
            ]
        case "api_key_compromise":
            return [
                SecurityAlert(
                    alert_id="ALERT-AK-001",
                    source="waf",
                    severity="critical",
                    category="api_misuse",
                    message="Production API key key-prod-001 used from foreign IP 45.155.205.99 (Lagos, NG)",
                    timestamp=ts,
                    indicators={
                        "api_key": "key-prod-001",
                        "source_ip": "45.155.205.99",
                        "geo": "Lagos, NG",
                    },
                ),
                SecurityAlert(
                    alert_id="ALERT-AK-002",
                    source="siem",
                    severity="high",
                    category="data_exfiltration",
                    message="Mass API data extraction: 25 requests to data export endpoints in 6 minutes",
                    timestamp=ts,
                    indicators={
                        "api_key": "key-prod-001",
                        "request_count": "25",
                        "endpoints": "data/export/*",
                    },
                ),
                SecurityAlert(
                    alert_id="ALERT-AK-003",
                    source="siem",
                    severity="critical",
                    category="api_misuse",
                    message="API key rotation attempted from foreign IP - potential persistence mechanism",
                    timestamp=ts,
                    indicators={
                        "api_key": "key-prod-001",
                        "action": "keys/rotate",
                        "source_ip": "45.155.205.99",
                    },
                ),
            ]
        case "malware_lateral_movement":
            return [
                SecurityAlert(
                    alert_id="ALERT-ML-001",
                    source="edr",
                    severity="critical",
                    category="malware",
                    message="Known malware hash detected: Cobalt Strike Beacon on ws-jsmith-01",
                    timestamp=ts,
                    indicators={
                        "hostname": "ws-jsmith-01",
                        "hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
                        "malware": "Cobalt Strike Beacon",
                    },
                ),
                SecurityAlert(
                    alert_id="ALERT-ML-002",
                    source="edr",
                    severity="critical",
                    category="malware",
                    message="Credential dumping tool detected: Mimikatz executed on ws-jsmith-01",
                    timestamp=ts,
                    indicators={
                        "hostname": "ws-jsmith-01",
                        "tool": "mimikatz",
                        "parent": "rundll32.exe",
                    },
                ),
                SecurityAlert(
                    alert_id="ALERT-ML-003",
                    source="ndr",
                    severity="high",
                    category="c2_communication",
                    message="C2 beaconing detected: periodic connections from 10.0.2.15 to 198.51.100.42:8443",
                    timestamp=ts,
                    indicators={
                        "source_ip": "10.0.2.15",
                        "c2_ip": "198.51.100.42",
                        "port": "8443",
                        "interval": "5min",
                    },
                ),
                SecurityAlert(
                    alert_id="ALERT-ML-004",
                    source="edr",
                    severity="high",
                    category="malware",
                    message="PsExec lateral movement detected to srv-db-01, srv-dc-01, srv-file-01",
                    timestamp=ts,
                    indicators={
                        "source": "ws-jsmith-01",
                        "targets": "srv-db-01,srv-dc-01,srv-file-01",
                        "tool": "PsExec",
                    },
                ),
            ]
        case "cloud_misconfiguration":
            return [
                SecurityAlert(
                    alert_id="ALERT-CM-001",
                    source="cspm",
                    severity="critical",
                    category="cloud_misconfiguration",
                    message="S3 bucket prod-customer-data policy changed to allow public access",
                    timestamp=ts,
                    indicators={
                        "bucket": "prod-customer-data",
                        "principal": "jsmith",
                        "action": "PutBucketPolicy",
                    },
                ),
                SecurityAlert(
                    alert_id="ALERT-CM-002",
                    source="cspm",
                    severity="high",
                    category="cloud_misconfiguration",
                    message="Security group sg-prod-db opened to 0.0.0.0/0 on all ports",
                    timestamp=ts,
                    indicators={
                        "security_group": "sg-prod-db",
                        "principal": "jsmith",
                        "cidr": "0.0.0.0/0",
                    },
                ),
                SecurityAlert(
                    alert_id="ALERT-CM-003",
                    source="siem",
                    severity="critical",
                    category="data_exfiltration",
                    message="External IPs accessing prod-customer-data S3 bucket: 3 unique IPs, 12 objects downloaded",
                    timestamp=ts,
                    indicators={
                        "bucket": "prod-customer-data",
                        "external_ips": "203.0.113.55,198.51.100.88,192.0.2.101",
                    },
                ),
            ]


def _generate_assets(scenario_type: ScenarioType) -> list[AssetInfo]:
    """Generate asset inventory for a given scenario type.

    Args:
        scenario_type: The type of threat scenario.

    Returns:
        list[AssetInfo]: Asset information for the scenario.
    """
    base_assets = [
        AssetInfo(
            "asset-001",
            "srv-auth-01",
            "10.0.1.50",
            "server",
            "security-team",
            "critical",
        ),
        AssetInfo(
            "asset-002", "ws-jsmith-01", "10.0.2.15", "workstation", "jsmith", "medium"
        ),
        AssetInfo(
            "asset-003", "ws-agarcia-01", "10.0.2.22", "workstation", "agarcia", "low"
        ),
        AssetInfo(
            "asset-004", "srv-db-01", "10.0.3.10", "server", "db-team", "critical"
        ),
        AssetInfo(
            "asset-005", "ws-mchen-01", "10.0.2.45", "workstation", "mchen", "medium"
        ),
        AssetInfo(
            "asset-006", "srv-api-01", "10.0.10.5", "server", "platform-team", "high"
        ),
        AssetInfo(
            "asset-007", "srv-monitor-01", "10.0.10.6", "server", "sre-team", "medium"
        ),
        AssetInfo(
            "asset-008", "srv-dc-01", "10.0.1.50", "server", "infra-team", "critical"
        ),
        AssetInfo(
            "asset-009", "srv-file-01", "10.0.2.22", "server", "infra-team", "high"
        ),
        AssetInfo(
            "asset-010",
            "cloud-s3-prod",
            "n/a",
            "cloud_resource",
            "platform-team",
            "critical",
        ),
    ]
    return base_assets


@dataclass
class ScenarioData:
    """Complete security event data for a simulated threat scenario.

    Attributes:
        scenario_type: The type of threat scenario.
        description: Human-readable description of the scenario.
        base_time: Starting timestamp for the scenario.
        alerts: Security alerts generated for the scenario.
        assets: Asset inventory for the environment.
        auth_logs: Authentication log entries.
        network_logs: Network/firewall log entries.
        api_access_logs: API access log entries.
        endpoint_events: Endpoint/EDR event entries.
        cloud_audit_logs: Cloud audit trail entries.
    """

    scenario_type: ScenarioType
    description: str
    base_time: datetime
    alerts: list[SecurityAlert] = field(default_factory=list)
    assets: list[AssetInfo] = field(default_factory=list)
    auth_logs: list[AuthLogEntry] = field(default_factory=list)
    network_logs: list[NetworkLogEntry] = field(default_factory=list)
    api_access_logs: list[APIAccessEntry] = field(default_factory=list)
    endpoint_events: list[EndpointEvent] = field(default_factory=list)
    cloud_audit_logs: list[CloudAuditEntry] = field(default_factory=list)


def generate_scenario(scenario_type: ScenarioType) -> ScenarioData:
    """Generate a complete threat scenario with correlated security event data.

    Coordinates all simulators to produce auth logs, network logs, API access logs,
    endpoint events, and cloud audit entries for the specified scenario type.

    Args:
        scenario_type: The type of threat to simulate.

    Returns:
        ScenarioData: Complete security event data for the scenario.

    Raises:
        AssertionError: If scenario_type is not a supported scenario.
    """
    base_time = datetime.now(timezone.utc)
    logger.info("Generating scenario: %s", scenario_type)

    generators: dict[ScenarioType, tuple] = {
        "brute_force_attack": (
            generate_brute_force_auth_logs,
            generate_brute_force_network_logs,
            generate_brute_force_api_logs,
            generate_brute_force_endpoint_events,
            generate_brute_force_cloud_audit,
        ),
        "insider_threat": (
            generate_insider_threat_auth_logs,
            generate_insider_threat_network_logs,
            generate_insider_threat_api_logs,
            generate_insider_threat_endpoint_events,
            generate_insider_threat_cloud_audit,
        ),
        "api_key_compromise": (
            generate_api_key_compromise_auth_logs,
            generate_api_key_compromise_network_logs,
            generate_api_key_compromise_api_logs,
            generate_api_key_compromise_endpoint_events,
            generate_api_key_compromise_cloud_audit,
        ),
        "malware_lateral_movement": (
            generate_malware_auth_logs,
            generate_malware_network_logs,
            generate_malware_api_logs,
            generate_malware_endpoint_events,
            generate_malware_cloud_audit,
        ),
        "cloud_misconfiguration": (
            generate_cloud_misconfig_auth_logs,
            generate_cloud_misconfig_network_logs,
            generate_cloud_misconfig_api_logs,
            generate_cloud_misconfig_endpoint_events,
            generate_cloud_misconfig_cloud_audit,
        ),
    }

    assert scenario_type in generators, f"Unknown scenario: {scenario_type}"

    auth_gen, net_gen, api_gen, endpoint_gen, cloud_gen = generators[scenario_type]

    auth_logs = auth_gen(base_time)
    network_logs = net_gen(base_time)
    api_access_logs = api_gen(base_time)
    endpoint_events = endpoint_gen(base_time)
    cloud_audit_logs = cloud_gen(base_time)
    alerts = _generate_alerts(scenario_type, base_time)
    assets = _generate_assets(scenario_type)

    logger.info(
        "Scenario generated: auth=%d, network=%d, api=%d, endpoint=%d, cloud=%d, alerts=%d",
        len(auth_logs),
        len(network_logs),
        len(api_access_logs),
        len(endpoint_events),
        len(cloud_audit_logs),
        len(alerts),
    )

    return ScenarioData(
        scenario_type=scenario_type,
        description=SCENARIO_DESCRIPTIONS[scenario_type],
        base_time=base_time,
        alerts=alerts,
        assets=assets,
        auth_logs=auth_logs,
        network_logs=network_logs,
        api_access_logs=api_access_logs,
        endpoint_events=endpoint_events,
        cloud_audit_logs=cloud_audit_logs,
    )


def list_scenarios() -> list[tuple[ScenarioType, str]]:
    """List all available threat scenarios.

    Returns:
        list[tuple[ScenarioType, str]]: List of (scenario_type, description) tuples.
    """
    return [(k, v) for k, v in SCENARIO_DESCRIPTIONS.items()]
