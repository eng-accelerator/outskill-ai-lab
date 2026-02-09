"""Simulates realistic API access log data for threat scenarios.

Generates structured API access log entries with patterns for normal usage,
excessive API calls, unauthorized endpoint access, and API key abuse.
"""

import random
from datetime import datetime, timedelta

from cybersecurity_threat_detection_agent.models.analysis import APIAccessEntry

# Normal API endpoints
NORMAL_ENDPOINTS = [
    "/api/v1/users/me",
    "/api/v1/projects",
    "/api/v1/projects/{id}/tasks",
    "/api/v1/notifications",
    "/api/v1/search",
    "/api/v1/files/upload",
    "/api/v1/reports/summary",
]

# Sensitive/admin API endpoints
ADMIN_ENDPOINTS = [
    "/api/v1/admin/users",
    "/api/v1/admin/config",
    "/api/v1/admin/audit-logs",
    "/api/v1/admin/secrets",
    "/api/v1/admin/iam/roles",
    "/api/v1/internal/database/export",
    "/api/v1/internal/keys/rotate",
]

# Data export endpoints
DATA_ENDPOINTS = [
    "/api/v1/data/export/users",
    "/api/v1/data/export/transactions",
    "/api/v1/data/export/customers",
    "/api/v1/data/bulk-download",
]

# API key IDs
API_KEYS = {
    "key-prod-001": {"user": "svc-deploy", "scope": "deploy"},
    "key-prod-002": {"user": "svc-monitor", "scope": "read"},
    "key-dev-003": {"user": "jsmith", "scope": "dev"},
    "key-admin-004": {"user": "admin", "scope": "admin"},
    "key-user-005": {"user": "kpatel", "scope": "user"},
}


def _generate_baseline_api_logs(
    base_time: datetime, count: int
) -> list[APIAccessEntry]:
    """Generate normal baseline API access log entries.

    Args:
        base_time: Starting timestamp for log generation.
        count: Number of entries to generate.

    Returns:
        list[APIAccessEntry]: Normal API access log entries.
    """
    entries = []
    for _ in range(count):
        ts = base_time + timedelta(seconds=random.randint(0, 3600))
        key_id = random.choice(["key-dev-003", "key-user-005", "key-prod-002"])
        key_info = API_KEYS[key_id]
        entries.append(
            APIAccessEntry(
                timestamp=ts.isoformat(),
                user=key_info["user"],
                api_key_id=key_id,
                endpoint=random.choice(NORMAL_ENDPOINTS),
                method=random.choice(["GET", "GET", "GET", "POST"]),
                status_code=random.choices([200, 201, 304], weights=[70, 20, 10])[0],
                response_time_ms=random.randint(20, 300),
                source_ip=f"10.0.2.{random.randint(10, 50)}",
                user_agent="Mozilla/5.0 (compatible; app-client/1.0)",
            )
        )
    return entries


def generate_brute_force_api_logs(base_time: datetime) -> list[APIAccessEntry]:
    """Generate API logs for a brute force scenario (minimal API activity).

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[APIAccessEntry]: API access log entries.
    """
    return _generate_baseline_api_logs(base_time, 10)


def generate_insider_threat_api_logs(base_time: datetime) -> list[APIAccessEntry]:
    """Generate API logs consistent with an insider threat.

    Shows an employee accessing admin endpoints and bulk-exporting data
    beyond their normal role.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[APIAccessEntry]: API access log entries showing insider abuse.
    """
    entries = _generate_baseline_api_logs(base_time, 15)
    insider_ip = "10.0.2.45"

    # Access to admin endpoints (beyond kpatel's normal scope)
    for i in range(6):
        ts = base_time + timedelta(minutes=20 + i * 3)
        entries.append(
            APIAccessEntry(
                timestamp=ts.isoformat(),
                user="kpatel",
                api_key_id="key-user-005",
                endpoint=random.choice(ADMIN_ENDPOINTS),
                method="GET",
                status_code=random.choices([200, 403], weights=[40, 60])[0],
                response_time_ms=random.randint(50, 200),
                source_ip=insider_ip,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
            )
        )

    # Bulk data export
    for i in range(4):
        ts = base_time + timedelta(minutes=40 + i * 5)
        entries.append(
            APIAccessEntry(
                timestamp=ts.isoformat(),
                user="kpatel",
                api_key_id="key-user-005",
                endpoint=random.choice(DATA_ENDPOINTS),
                method="GET",
                status_code=200,
                response_time_ms=random.randint(2000, 8000),  # Slow due to large data
                source_ip=insider_ip,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_api_key_compromise_api_logs(
    base_time: datetime,
) -> list[APIAccessEntry]:
    """Generate API logs for an API key compromise scenario.

    Shows a leaked API key being used from a foreign IP for mass data extraction.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[APIAccessEntry]: API access log entries showing key compromise.
    """
    entries = _generate_baseline_api_logs(base_time, 15)
    foreign_ip = "45.155.205.99"
    compromised_key = "key-prod-001"

    # Mass API calls from foreign IP using compromised key
    abuse_start = base_time + timedelta(minutes=10)
    for i in range(25):
        ts = abuse_start + timedelta(seconds=i * 15)
        entries.append(
            APIAccessEntry(
                timestamp=ts.isoformat(),
                user="svc-deploy",
                api_key_id=compromised_key,
                endpoint=random.choice(DATA_ENDPOINTS + ADMIN_ENDPOINTS),
                method=random.choice(["GET", "GET", "POST"]),
                status_code=200,
                response_time_ms=random.randint(100, 3000),
                source_ip=foreign_ip,
                user_agent="curl/8.4.0",
            )
        )

    # Attempted key rotation by attacker
    entries.append(
        APIAccessEntry(
            timestamp=(abuse_start + timedelta(minutes=10)).isoformat(),
            user="svc-deploy",
            api_key_id=compromised_key,
            endpoint="/api/v1/internal/keys/rotate",
            method="POST",
            status_code=200,
            response_time_ms=150,
            source_ip=foreign_ip,
            user_agent="curl/8.4.0",
        )
    )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_malware_api_logs(base_time: datetime) -> list[APIAccessEntry]:
    """Generate API logs for a malware scenario (minimal API activity).

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[APIAccessEntry]: API access log entries.
    """
    return _generate_baseline_api_logs(base_time, 10)


def generate_cloud_misconfig_api_logs(base_time: datetime) -> list[APIAccessEntry]:
    """Generate API logs for a cloud misconfiguration scenario.

    Shows unauthorized external access to APIs that should be internal-only.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[APIAccessEntry]: API access log entries for cloud misconfiguration.
    """
    entries = _generate_baseline_api_logs(base_time, 15)

    # External access to internal APIs after misconfiguration
    external_ips = ["203.0.113.55", "198.51.100.88", "192.0.2.101"]
    access_start = base_time + timedelta(minutes=20)
    for i in range(10):
        ts = access_start + timedelta(minutes=i * 2)
        entries.append(
            APIAccessEntry(
                timestamp=ts.isoformat(),
                user="anonymous",
                api_key_id="none",
                endpoint=random.choice(DATA_ENDPOINTS),
                method="GET",
                status_code=200,
                response_time_ms=random.randint(500, 3000),
                source_ip=random.choice(external_ips),
                user_agent=random.choice([
                    "curl/8.4.0",
                    "python-requests/2.31.0",
                    "Scrapy/2.11",
                ]),
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)
