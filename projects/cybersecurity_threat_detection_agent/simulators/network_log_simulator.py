"""Simulates realistic network/firewall log data for threat scenarios.

Generates structured network log entries with patterns for port scanning,
C2 beaconing, data exfiltration, and normal traffic.
"""

import random
from datetime import datetime, timedelta

from cybersecurity_threat_detection_agent.models.analysis import NetworkLogEntry

# Internal network ranges
INTERNAL_IPS = [
    "10.0.1.50", "10.0.2.15", "10.0.2.22", "10.0.3.10",
    "10.0.2.45", "10.0.10.5", "10.0.10.6",
]

# Known malicious external IPs
MALICIOUS_IPS = [
    "185.220.101.34",
    "91.219.237.12",
    "45.155.205.99",
    "193.56.28.103",
    "89.248.167.131",
]

# Known C2 server IPs
C2_IPS = [
    "198.51.100.42",
    "203.0.113.77",
    "192.0.2.199",
]

# Common legitimate external IPs
LEGITIMATE_EXTERNAL_IPS = [
    "13.107.42.14",   # Microsoft
    "142.250.80.46",  # Google
    "52.84.125.10",   # AWS CloudFront
    "104.18.32.7",    # Cloudflare
]

COMMON_PORTS = [80, 443, 8080, 8443, 53, 22, 3389, 3306, 5432]


def _generate_baseline_network_logs(
    base_time: datetime, count: int
) -> list[NetworkLogEntry]:
    """Generate normal baseline network traffic logs.

    Args:
        base_time: Starting timestamp for log generation.
        count: Number of entries to generate.

    Returns:
        list[NetworkLogEntry]: Normal network log entries.
    """
    entries = []
    for _ in range(count):
        ts = base_time + timedelta(seconds=random.randint(0, 3600))
        src = random.choice(INTERNAL_IPS)
        dst = random.choice(LEGITIMATE_EXTERNAL_IPS)
        port = random.choice([80, 443])
        entries.append(
            NetworkLogEntry(
                timestamp=ts.isoformat(),
                source_ip=src,
                dest_ip=dst,
                dest_port=port,
                protocol="TCP",
                bytes_sent=random.randint(200, 5000),
                bytes_received=random.randint(500, 50000),
                action="allow",
                rule_name="allow-outbound-web",
            )
        )
    return entries


def generate_brute_force_network_logs(base_time: datetime) -> list[NetworkLogEntry]:
    """Generate network logs consistent with a brute force attack.

    Shows inbound connection attempts from botnet IPs to auth services.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[NetworkLogEntry]: Network log entries showing brute force traffic.
    """
    entries = _generate_baseline_network_logs(base_time, 20)
    attack_start = base_time + timedelta(minutes=5)

    # Inbound brute force connections
    for i in range(25):
        ts = attack_start + timedelta(seconds=i * 2)
        attacker_ip = random.choice(MALICIOUS_IPS)
        entries.append(
            NetworkLogEntry(
                timestamp=ts.isoformat(),
                source_ip=attacker_ip,
                dest_ip="10.0.1.50",  # auth server
                dest_port=443,
                protocol="TCP",
                bytes_sent=random.randint(500, 2000),
                bytes_received=random.randint(200, 1000),
                action="allow",
                rule_name="allow-inbound-https",
            )
        )

    # Some blocked connections
    for i in range(10):
        ts = attack_start + timedelta(seconds=60 + i * 5)
        entries.append(
            NetworkLogEntry(
                timestamp=ts.isoformat(),
                source_ip=random.choice(MALICIOUS_IPS),
                dest_ip="10.0.1.50",
                dest_port=22,
                protocol="TCP",
                bytes_sent=0,
                bytes_received=0,
                action="deny",
                rule_name="block-ssh-external",
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_insider_threat_network_logs(base_time: datetime) -> list[NetworkLogEntry]:
    """Generate network logs consistent with an insider threat.

    Shows data exfiltration via large outbound transfers.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[NetworkLogEntry]: Network log entries showing insider data exfiltration.
    """
    entries = _generate_baseline_network_logs(base_time, 20)
    insider_ip = "10.0.2.45"  # kpatel

    # Large data transfers to external storage
    exfil_start = base_time + timedelta(minutes=30)
    for i in range(8):
        ts = exfil_start + timedelta(minutes=i * 2)
        entries.append(
            NetworkLogEntry(
                timestamp=ts.isoformat(),
                source_ip=insider_ip,
                dest_ip="104.18.32.7",  # Cloud storage
                dest_port=443,
                protocol="TCP",
                bytes_sent=random.randint(5_000_000, 50_000_000),  # Large uploads
                bytes_received=random.randint(500, 5000),
                action="allow",
                rule_name="allow-outbound-web",
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_api_key_compromise_network_logs(
    base_time: datetime,
) -> list[NetworkLogEntry]:
    """Generate network logs for an API key compromise scenario.

    Shows API traffic from foreign IPs and mass data extraction.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[NetworkLogEntry]: Network log entries for API key compromise.
    """
    entries = _generate_baseline_network_logs(base_time, 20)
    foreign_ip = "45.155.205.99"
    api_server = "10.0.10.5"

    # Foreign IP accessing API server
    for i in range(15):
        ts = base_time + timedelta(minutes=10 + i)
        entries.append(
            NetworkLogEntry(
                timestamp=ts.isoformat(),
                source_ip=foreign_ip,
                dest_ip=api_server,
                dest_port=443,
                protocol="TCP",
                bytes_sent=random.randint(500, 2000),
                bytes_received=random.randint(100_000, 1_000_000),  # Large responses
                action="allow",
                rule_name="allow-inbound-api",
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_malware_network_logs(base_time: datetime) -> list[NetworkLogEntry]:
    """Generate network logs for a malware lateral movement scenario.

    Shows C2 beaconing, port scanning, and lateral movement traffic.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[NetworkLogEntry]: Network log entries showing malware activity.
    """
    entries = _generate_baseline_network_logs(base_time, 20)
    compromised_ip = "10.0.2.15"  # jsmith's workstation

    # C2 beaconing - periodic connections to C2 server
    c2_ip = C2_IPS[0]
    beacon_start = base_time + timedelta(minutes=12)
    for i in range(12):
        ts = beacon_start + timedelta(minutes=i * 5)  # Every 5 minutes
        entries.append(
            NetworkLogEntry(
                timestamp=ts.isoformat(),
                source_ip=compromised_ip,
                dest_ip=c2_ip,
                dest_port=8443,
                protocol="TCP",
                bytes_sent=random.randint(100, 500),
                bytes_received=random.randint(200, 2000),
                action="allow",
                rule_name="allow-outbound-web",
            )
        )

    # Port scanning from compromised host
    scan_start = base_time + timedelta(minutes=20)
    scan_targets = ["10.0.3.10", "10.0.1.50", "10.0.2.22"]
    for target in scan_targets:
        for port in [22, 445, 3389, 5985, 135, 139]:
            ts = scan_start + timedelta(seconds=random.randint(0, 60))
            entries.append(
                NetworkLogEntry(
                    timestamp=ts.isoformat(),
                    source_ip=compromised_ip,
                    dest_ip=target,
                    dest_port=port,
                    protocol="TCP",
                    bytes_sent=random.randint(50, 200),
                    bytes_received=0,
                    action="allow" if port in [445, 5985] else "deny",
                    rule_name="internal-traffic",
                )
            )

    # Lateral movement via SMB (port 445)
    for i, target in enumerate(scan_targets):
        ts = base_time + timedelta(minutes=25 + i * 5)
        entries.append(
            NetworkLogEntry(
                timestamp=ts.isoformat(),
                source_ip=compromised_ip,
                dest_ip=target,
                dest_port=445,
                protocol="TCP",
                bytes_sent=random.randint(50_000, 500_000),
                bytes_received=random.randint(10_000, 100_000),
                action="allow",
                rule_name="internal-traffic",
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_cloud_misconfig_network_logs(
    base_time: datetime,
) -> list[NetworkLogEntry]:
    """Generate network logs for a cloud misconfiguration scenario.

    Shows external access to previously internal-only resources.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[NetworkLogEntry]: Network log entries for cloud misconfiguration.
    """
    entries = _generate_baseline_network_logs(base_time, 20)

    # External IPs accessing S3/storage that was made public
    external_access_start = base_time + timedelta(minutes=20)
    external_ips = ["203.0.113.55", "198.51.100.88", "192.0.2.101"]
    for i, ext_ip in enumerate(external_ips):
        for j in range(5):
            ts = external_access_start + timedelta(minutes=i * 3 + j)
            entries.append(
                NetworkLogEntry(
                    timestamp=ts.isoformat(),
                    source_ip=ext_ip,
                    dest_ip="10.0.10.5",
                    dest_port=443,
                    protocol="TCP",
                    bytes_sent=random.randint(200, 1000),
                    bytes_received=random.randint(100_000, 5_000_000),
                    action="allow",
                    rule_name="allow-inbound-api",
                )
            )

    return sorted(entries, key=lambda e: e.timestamp)
