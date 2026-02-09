"""Simulates realistic authentication log data for threat scenarios.

Generates structured auth log entries with patterns for brute force attacks,
impossible travel, credential stuffing, and privilege escalation.
"""

import random
from datetime import datetime, timedelta

from cybersecurity_threat_detection_agent.models.analysis import AuthLogEntry

# Known legitimate users and their typical locations
LEGITIMATE_USERS = {
    "admin": {"geo": "New York, US", "ip": "10.0.1.50"},
    "jsmith": {"geo": "San Francisco, US", "ip": "10.0.2.15"},
    "agarcia": {"geo": "Austin, US", "ip": "10.0.2.22"},
    "mchen": {"geo": "Seattle, US", "ip": "10.0.3.10"},
    "kpatel": {"geo": "Chicago, US", "ip": "10.0.2.45"},
    "svc-deploy": {"geo": "AWS us-east-1", "ip": "10.0.10.5"},
    "svc-monitor": {"geo": "AWS us-east-1", "ip": "10.0.10.6"},
}

# Known botnet / attacker IPs
ATTACKER_IPS = [
    "185.220.101.34",
    "91.219.237.12",
    "45.155.205.99",
    "193.56.28.103",
    "89.248.167.131",
    "178.128.23.9",
]

# Distant geolocations for impossible travel
DISTANT_GEOS = [
    "Moscow, RU",
    "Beijing, CN",
    "Lagos, NG",
    "Sao Paulo, BR",
    "Mumbai, IN",
    "Pyongyang, KP",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) Safari/605.1",
    "python-requests/2.31.0",
    "curl/8.4.0",
    "Mozilla/5.0 (Linux; Android 14) Mobile Safari/537.36",
]


def _generate_baseline_auth_logs(
    base_time: datetime, count: int
) -> list[AuthLogEntry]:
    """Generate normal baseline authentication log entries.

    Args:
        base_time: Starting timestamp for log generation.
        count: Number of entries to generate.

    Returns:
        list[AuthLogEntry]: Normal auth log entries.
    """
    entries = []
    for i in range(count):
        ts = base_time + timedelta(seconds=random.randint(0, 3600))
        user = random.choice(list(LEGITIMATE_USERS.keys()))
        info = LEGITIMATE_USERS[user]
        action = random.choices(
            ["login_success", "logout", "mfa_challenge"],
            weights=[60, 30, 10],
        )[0]
        entries.append(
            AuthLogEntry(
                timestamp=ts.isoformat(),
                user=user,
                source_ip=info["ip"],
                action=action,
                geo_location=info["geo"],
                user_agent=random.choice(USER_AGENTS[:2]),
                session_id=f"sess-{random.randint(10000, 99999)}",
                success=True,
            )
        )
    return entries


def generate_brute_force_auth_logs(base_time: datetime) -> list[AuthLogEntry]:
    """Generate auth logs consistent with a brute force attack.

    Produces many failed login attempts from botnet IPs against admin accounts,
    eventually succeeding on one account, followed by lateral movement.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[AuthLogEntry]: Auth log entries showing brute force pattern.
    """
    entries = _generate_baseline_auth_logs(base_time, 20)
    target_user = "admin"
    attack_start = base_time + timedelta(minutes=5)

    # Phase 1: Rapid failed logins from multiple IPs
    for i in range(30):
        ts = attack_start + timedelta(seconds=i * 2)
        attacker_ip = random.choice(ATTACKER_IPS)
        entries.append(
            AuthLogEntry(
                timestamp=ts.isoformat(),
                user=target_user,
                source_ip=attacker_ip,
                action="login_failure",
                geo_location=random.choice(DISTANT_GEOS),
                user_agent="python-requests/2.31.0",
                session_id=f"sess-{random.randint(10000, 99999)}",
                success=False,
            )
        )

    # Phase 2: Successful login after brute force
    compromise_time = attack_start + timedelta(minutes=2)
    compromise_ip = ATTACKER_IPS[0]
    entries.append(
        AuthLogEntry(
            timestamp=compromise_time.isoformat(),
            user=target_user,
            source_ip=compromise_ip,
            action="login_success",
            geo_location="Moscow, RU",
            user_agent="python-requests/2.31.0",
            session_id="sess-compromised-01",
            success=True,
        )
    )

    # Phase 3: Lateral movement - accessing other accounts
    for i, user in enumerate(["jsmith", "mchen"]):
        ts = compromise_time + timedelta(minutes=5 + i * 3)
        entries.append(
            AuthLogEntry(
                timestamp=ts.isoformat(),
                user=user,
                source_ip=compromise_ip,
                action="login_success",
                geo_location="Moscow, RU",
                user_agent="python-requests/2.31.0",
                session_id=f"sess-lateral-{i:02d}",
                success=True,
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_insider_threat_auth_logs(base_time: datetime) -> list[AuthLogEntry]:
    """Generate auth logs consistent with an insider threat.

    Shows an employee escalating their own privileges and accessing
    resources beyond their normal role.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[AuthLogEntry]: Auth log entries showing insider threat pattern.
    """
    entries = _generate_baseline_auth_logs(base_time, 15)
    insider = "kpatel"
    insider_ip = LEGITIMATE_USERS[insider]["ip"]
    insider_geo = LEGITIMATE_USERS[insider]["geo"]

    # Normal login
    entries.append(
        AuthLogEntry(
            timestamp=(base_time + timedelta(minutes=5)).isoformat(),
            user=insider,
            source_ip=insider_ip,
            action="login_success",
            geo_location=insider_geo,
            user_agent=USER_AGENTS[0],
            session_id="sess-insider-01",
            success=True,
        )
    )

    # Self-privilege escalation via role change
    entries.append(
        AuthLogEntry(
            timestamp=(base_time + timedelta(minutes=15)).isoformat(),
            user=insider,
            source_ip=insider_ip,
            action="role_change",
            geo_location=insider_geo,
            user_agent=USER_AGENTS[0],
            session_id="sess-insider-01",
            success=True,
        )
    )

    # Sudo to root
    entries.append(
        AuthLogEntry(
            timestamp=(base_time + timedelta(minutes=20)).isoformat(),
            user=insider,
            source_ip=insider_ip,
            action="sudo",
            geo_location=insider_geo,
            user_agent=USER_AGENTS[0],
            session_id="sess-insider-01",
            success=True,
        )
    )

    # Access from unusual hours (late night)
    late_time = base_time + timedelta(hours=14)
    entries.append(
        AuthLogEntry(
            timestamp=late_time.isoformat(),
            user=insider,
            source_ip=insider_ip,
            action="login_success",
            geo_location=insider_geo,
            user_agent=USER_AGENTS[0],
            session_id="sess-insider-02",
            success=True,
        )
    )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_api_key_compromise_auth_logs(base_time: datetime) -> list[AuthLogEntry]:
    """Generate auth logs for an API key compromise scenario.

    Shows normal auth activity with a compromised API key used from foreign IPs.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[AuthLogEntry]: Auth log entries for API key compromise.
    """
    entries = _generate_baseline_auth_logs(base_time, 15)

    # API key used from foreign IP (shows up as service account login)
    foreign_ip = "45.155.205.99"
    for i in range(5):
        ts = base_time + timedelta(minutes=10 + i * 2)
        entries.append(
            AuthLogEntry(
                timestamp=ts.isoformat(),
                user="svc-deploy",
                source_ip=foreign_ip,
                action="login_success",
                geo_location="Lagos, NG",
                user_agent="curl/8.4.0",
                session_id=f"sess-apikey-{i:02d}",
                success=True,
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_malware_auth_logs(base_time: datetime) -> list[AuthLogEntry]:
    """Generate auth logs for a malware lateral movement scenario.

    Shows compromised workstation credentials being used for lateral movement.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[AuthLogEntry]: Auth log entries showing malware lateral movement.
    """
    entries = _generate_baseline_auth_logs(base_time, 15)
    compromised_host_ip = "10.0.2.15"  # jsmith's workstation

    # Initial compromise (phishing)
    entries.append(
        AuthLogEntry(
            timestamp=(base_time + timedelta(minutes=10)).isoformat(),
            user="jsmith",
            source_ip=compromised_host_ip,
            action="login_success",
            geo_location="San Francisco, US",
            user_agent=USER_AGENTS[0],
            session_id="sess-phish-01",
            success=True,
        )
    )

    # Lateral movement via PsExec-style remote logins
    lateral_targets = [
        ("10.0.3.10", "srv-db-01"),
        ("10.0.1.50", "srv-dc-01"),
        ("10.0.2.22", "srv-file-01"),
    ]
    for i, (target_ip, _hostname) in enumerate(lateral_targets):
        ts = base_time + timedelta(minutes=25 + i * 5)
        entries.append(
            AuthLogEntry(
                timestamp=ts.isoformat(),
                user="jsmith",
                source_ip=compromised_host_ip,
                action="login_success",
                geo_location="San Francisco, US",
                user_agent="",
                session_id=f"sess-lateral-{i:02d}",
                success=True,
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_cloud_misconfig_auth_logs(base_time: datetime) -> list[AuthLogEntry]:
    """Generate auth logs for a cloud misconfiguration scenario.

    Shows normal auth activity with some IAM-related actions.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[AuthLogEntry]: Auth log entries for cloud misconfiguration.
    """
    entries = _generate_baseline_auth_logs(base_time, 15)

    # IAM role assumption from unusual principal
    entries.append(
        AuthLogEntry(
            timestamp=(base_time + timedelta(minutes=10)).isoformat(),
            user="svc-deploy",
            source_ip="10.0.10.5",
            action="role_change",
            geo_location="AWS us-east-1",
            user_agent="aws-sdk-python/1.34.0",
            session_id="sess-iam-01",
            success=True,
        )
    )

    return sorted(entries, key=lambda e: e.timestamp)
