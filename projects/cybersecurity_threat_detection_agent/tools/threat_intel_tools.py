"""Tools for threat intelligence enrichment.

These tools are used by the Threat Intel Agent to enrich findings with
IOC lookups, MITRE ATT&CK mappings, and reputation scoring.
"""

import json
import logging

from agents import RunContextWrapper, function_tool
from cybersecurity_threat_detection_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)

# Simulated IOC database
IOC_DATABASE: dict[str, dict] = {
    # Malicious IPs
    "185.220.101.34": {
        "type": "ip",
        "threat": "Tor Exit Node / Brute Force Botnet",
        "confidence": 0.95,
        "source": "AbuseIPDB",
        "first_seen": "2024-01-15",
        "last_seen": "2026-02-01",
    },
    "91.219.237.12": {
        "type": "ip",
        "threat": "Credential Stuffing Botnet",
        "confidence": 0.90,
        "source": "OTX",
        "first_seen": "2024-06-20",
        "last_seen": "2026-01-28",
    },
    "45.155.205.99": {
        "type": "ip",
        "threat": "APT Infrastructure - Data Exfiltration",
        "confidence": 0.88,
        "source": "VirusTotal",
        "first_seen": "2025-03-10",
        "last_seen": "2026-02-05",
    },
    "193.56.28.103": {
        "type": "ip",
        "threat": "Scanning Infrastructure",
        "confidence": 0.85,
        "source": "Shodan",
        "first_seen": "2024-09-01",
        "last_seen": "2026-01-30",
    },
    "89.248.167.131": {
        "type": "ip",
        "threat": "Brute Force Source",
        "confidence": 0.92,
        "source": "AbuseIPDB",
        "first_seen": "2024-04-12",
        "last_seen": "2026-02-03",
    },
    "198.51.100.42": {
        "type": "ip",
        "threat": "Cobalt Strike C2 Server",
        "confidence": 0.98,
        "source": "CrowdStrike",
        "first_seen": "2025-11-01",
        "last_seen": "2026-02-08",
    },
    "203.0.113.77": {
        "type": "ip",
        "threat": "C2 Infrastructure",
        "confidence": 0.85,
        "source": "Mandiant",
        "first_seen": "2025-08-15",
        "last_seen": "2026-01-20",
    },
    # Malware hashes
    "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2": {
        "type": "hash",
        "threat": "Cobalt Strike Beacon",
        "confidence": 0.99,
        "source": "VirusTotal",
        "first_seen": "2025-10-01",
        "last_seen": "2026-02-07",
    },
    "f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e1": {
        "type": "hash",
        "threat": "Mimikatz",
        "confidence": 0.99,
        "source": "VirusTotal",
        "first_seen": "2023-01-01",
        "last_seen": "2026-02-08",
    },
    "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3": {
        "type": "hash",
        "threat": "PowerShell Empire",
        "confidence": 0.97,
        "source": "Hybrid Analysis",
        "first_seen": "2024-05-01",
        "last_seen": "2026-01-15",
    },
}

# Simulated MITRE ATT&CK mapping database
MITRE_MAPPINGS: dict[str, list[dict]] = {
    "brute_force": [
        {
            "tactic_id": "TA0006",
            "tactic_name": "Credential Access",
            "technique_id": "T1110",
            "technique_name": "Brute Force",
            "description": "Adversary attempted to gain access by systematically guessing passwords",
        },
        {
            "tactic_id": "TA0001",
            "tactic_name": "Initial Access",
            "technique_id": "T1078",
            "technique_name": "Valid Accounts",
            "description": "Adversary used compromised credentials to gain initial access",
        },
    ],
    "credential_stuffing": [
        {
            "tactic_id": "TA0006",
            "tactic_name": "Credential Access",
            "technique_id": "T1110.004",
            "technique_name": "Credential Stuffing",
            "description": "Adversary used previously breached credentials",
        },
    ],
    "impossible_travel": [
        {
            "tactic_id": "TA0001",
            "tactic_name": "Initial Access",
            "technique_id": "T1078",
            "technique_name": "Valid Accounts",
            "description": "Account used from geographically impossible locations",
        },
    ],
    "privilege_escalation": [
        {
            "tactic_id": "TA0004",
            "tactic_name": "Privilege Escalation",
            "technique_id": "T1078.004",
            "technique_name": "Cloud Accounts",
            "description": "Adversary escalated privileges via cloud IAM manipulation",
        },
        {
            "tactic_id": "TA0003",
            "tactic_name": "Persistence",
            "technique_id": "T1098",
            "technique_name": "Account Manipulation",
            "description": "Adversary modified account permissions to maintain access",
        },
    ],
    "api_misuse": [
        {
            "tactic_id": "TA0009",
            "tactic_name": "Collection",
            "technique_id": "T1530",
            "technique_name": "Data from Cloud Storage",
            "description": "Adversary accessed cloud storage to collect sensitive data",
        },
        {
            "tactic_id": "TA0010",
            "tactic_name": "Exfiltration",
            "technique_id": "T1567",
            "technique_name": "Exfiltration Over Web Service",
            "description": "Data exfiltrated via API calls",
        },
    ],
    "data_exfiltration": [
        {
            "tactic_id": "TA0010",
            "tactic_name": "Exfiltration",
            "technique_id": "T1041",
            "technique_name": "Exfiltration Over C2 Channel",
            "description": "Data exfiltrated over command and control channel",
        },
        {
            "tactic_id": "TA0010",
            "tactic_name": "Exfiltration",
            "technique_id": "T1567",
            "technique_name": "Exfiltration Over Web Service",
            "description": "Data exfiltrated via web service",
        },
    ],
    "malware": [
        {
            "tactic_id": "TA0002",
            "tactic_name": "Execution",
            "technique_id": "T1204.002",
            "technique_name": "Malicious File",
            "description": "User executed malicious macro-enabled document",
        },
        {
            "tactic_id": "TA0002",
            "tactic_name": "Execution",
            "technique_id": "T1059.001",
            "technique_name": "PowerShell",
            "description": "PowerShell used for malicious code execution",
        },
        {
            "tactic_id": "TA0005",
            "tactic_name": "Defense Evasion",
            "technique_id": "T1218.011",
            "technique_name": "Rundll32",
            "description": "Rundll32 used to proxy execution of malicious code",
        },
    ],
    "c2_communication": [
        {
            "tactic_id": "TA0011",
            "tactic_name": "Command and Control",
            "technique_id": "T1071.001",
            "technique_name": "Web Protocols",
            "description": "C2 communication over HTTPS",
        },
        {
            "tactic_id": "TA0011",
            "tactic_name": "Command and Control",
            "technique_id": "T1573",
            "technique_name": "Encrypted Channel",
            "description": "Encrypted C2 communication channel",
        },
    ],
    "cloud_misconfiguration": [
        {
            "tactic_id": "TA0001",
            "tactic_name": "Initial Access",
            "technique_id": "T1190",
            "technique_name": "Exploit Public-Facing Application",
            "description": "Misconfigured cloud resource exposed to public",
        },
        {
            "tactic_id": "TA0009",
            "tactic_name": "Collection",
            "technique_id": "T1530",
            "technique_name": "Data from Cloud Storage",
            "description": "Public access to cloud storage enabled data collection",
        },
    ],
    "insider_threat": [
        {
            "tactic_id": "TA0004",
            "tactic_name": "Privilege Escalation",
            "technique_id": "T1078",
            "technique_name": "Valid Accounts",
            "description": "Insider used valid credentials to escalate privileges",
        },
        {
            "tactic_id": "TA0009",
            "tactic_name": "Collection",
            "technique_id": "T1213",
            "technique_name": "Data from Information Repositories",
            "description": "Insider collected data from internal repositories",
        },
        {
            "tactic_id": "TA0010",
            "tactic_name": "Exfiltration",
            "technique_id": "T1567",
            "technique_name": "Exfiltration Over Web Service",
            "description": "Data exfiltrated via cloud storage upload",
        },
    ],
}

# Simulated IP reputation database
REPUTATION_DATABASE: dict[str, dict] = {
    "185.220.101.34": {
        "score": 5,
        "category": "malicious",
        "reports": 1247,
        "country": "RU",
        "isp": "AS-CHOOPA",
    },
    "91.219.237.12": {
        "score": 12,
        "category": "malicious",
        "reports": 834,
        "country": "UA",
        "isp": "DELTAHOST",
    },
    "45.155.205.99": {
        "score": 8,
        "category": "malicious",
        "reports": 567,
        "country": "NG",
        "isp": "CLOUDINNOVATION",
    },
    "193.56.28.103": {
        "score": 15,
        "category": "suspicious",
        "reports": 342,
        "country": "NL",
        "isp": "HOSTING-SOLUTIONS",
    },
    "89.248.167.131": {
        "score": 3,
        "category": "malicious",
        "reports": 2156,
        "country": "NL",
        "isp": "IPVOLUME",
    },
    "198.51.100.42": {
        "score": 2,
        "category": "malicious",
        "reports": 89,
        "country": "US",
        "isp": "BULLETPROOF-HOST",
    },
    "203.0.113.77": {
        "score": 10,
        "category": "suspicious",
        "reports": 156,
        "country": "HK",
        "isp": "HKBN",
    },
    "203.0.113.55": {
        "score": 45,
        "category": "neutral",
        "reports": 12,
        "country": "JP",
        "isp": "NTT",
    },
    "198.51.100.88": {
        "score": 50,
        "category": "neutral",
        "reports": 5,
        "country": "DE",
        "isp": "HETZNER",
    },
    "192.0.2.101": {
        "score": 55,
        "category": "neutral",
        "reports": 3,
        "country": "US",
        "isp": "DIGITAL-OCEAN",
    },
}


@function_tool
def lookup_ioc(
    ctx: RunContextWrapper[ScenarioData],
    indicator: str,
) -> str:
    """Look up an Indicator of Compromise (IOC) in the threat intelligence database.

    Checks IPs, domains, and file hashes against a curated IOC database.
    Returns threat information including threat name, confidence, and source.

    Args:
        ctx: Run context containing the scenario data.
        indicator: The indicator to look up (IP address, domain, or file hash).

    Returns:
        str: JSON string with IOC match details, or "no match" result.
    """
    logger.info("Looking up IOC: %s", indicator[:40])

    if indicator in IOC_DATABASE:
        ioc = IOC_DATABASE[indicator]
        result = {
            "match": True,
            "indicator": indicator,
            "indicator_type": ioc["type"],
            "threat_name": ioc["threat"],
            "confidence": ioc["confidence"],
            "source": ioc["source"],
            "first_seen": ioc["first_seen"],
            "last_seen": ioc["last_seen"],
        }
    else:
        result = {
            "match": False,
            "indicator": indicator,
            "message": "No IOC match found in threat intelligence database",
        }

    return json.dumps(result, indent=2)


@function_tool
def map_mitre_attack(
    ctx: RunContextWrapper[ScenarioData],
    threat_category: str,
) -> str:
    """Map observed threat behaviors to MITRE ATT&CK tactics and techniques.

    Given a threat category, returns the relevant MITRE ATT&CK mappings
    including tactic IDs, technique IDs, names, and descriptions.

    Args:
        ctx: Run context containing the scenario data.
        threat_category: The threat category to map (e.g. brute_force, malware, c2_communication).

    Returns:
        str: JSON string of MITRE ATT&CK mappings for the category.
    """
    logger.info("Mapping MITRE ATT&CK for category: %s", threat_category)

    mappings = MITRE_MAPPINGS.get(threat_category, [])
    if not mappings:
        return json.dumps(
            {
                "category": threat_category,
                "mappings": [],
                "message": f"No MITRE ATT&CK mappings found for category: {threat_category}",
            },
            indent=2,
        )

    return json.dumps(
        {
            "category": threat_category,
            "mappings": mappings,
            "total_techniques": len(mappings),
        },
        indent=2,
    )


@function_tool
def get_threat_reputation(
    ctx: RunContextWrapper[ScenarioData],
    indicator: str,
) -> str:
    """Get the reputation score for an IP address, domain, or file hash.

    Returns a reputation score (0-100, lower is more malicious),
    category classification, abuse report count, and geographic info.

    Args:
        ctx: Run context containing the scenario data.
        indicator: The indicator to check reputation for.

    Returns:
        str: JSON string with reputation details.
    """
    logger.info("Checking reputation for: %s", indicator[:40])

    if indicator in REPUTATION_DATABASE:
        rep = REPUTATION_DATABASE[indicator]
        result = {
            "indicator": indicator,
            "reputation_score": rep["score"],
            "category": rep["category"],
            "abuse_reports": rep["reports"],
            "country": rep["country"],
            "isp": rep["isp"],
            "assessment": (
                "malicious"
                if rep["score"] < 20
                else "suspicious" if rep["score"] < 40 else "neutral"
            ),
        }
    else:
        result = {
            "indicator": indicator,
            "reputation_score": 70,
            "category": "unknown",
            "abuse_reports": 0,
            "assessment": "no data available",
        }

    return json.dumps(result, indent=2)
