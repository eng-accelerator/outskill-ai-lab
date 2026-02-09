"""Simulates realistic endpoint/EDR event data for threat scenarios.

Generates structured endpoint events with patterns for normal process execution,
suspicious process trees, malware indicators, and lateral movement.
"""

import random
from datetime import datetime, timedelta

from cybersecurity_threat_detection_agent.models.analysis import EndpointEvent

# Normal process names and their typical parents
NORMAL_PROCESSES = [
    ("chrome.exe", "explorer.exe", "C:\\Program Files\\Google\\Chrome\\chrome.exe"),
    ("outlook.exe", "explorer.exe", "C:\\Program Files\\Microsoft Office\\outlook.exe"),
    (
        "code.exe",
        "explorer.exe",
        "C:\\Users\\user\\AppData\\Local\\Programs\\VS Code\\code.exe",
    ),
    ("svchost.exe", "services.exe", "C:\\Windows\\System32\\svchost.exe -k netsvcs"),
    ("nginx", "systemd", "/usr/sbin/nginx -g daemon off;"),
    ("python3", "bash", "/usr/bin/python3 /app/server.py"),
    ("java", "systemd", "/usr/bin/java -jar /app/service.jar"),
]

# Known malware hashes (simulated)
MALWARE_HASHES = {
    "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2": "Cobalt Strike Beacon",
    "f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e1": "Mimikatz",
    "b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3": "PowerShell Empire",
}

# Normal process hashes
CLEAN_HASHES = [
    "aa11bb22cc33dd44ee55ff66aa77bb88cc99dd00ee11ff22aa33bb44cc55dd66",
    "bb22cc33dd44ee55ff66aa77bb88cc99dd00ee11ff22aa33bb44cc55dd66ee77",
    "cc33dd44ee55ff66aa77bb88cc99dd00ee11ff22aa33bb44cc55dd66ee77ff88",
]

HOSTNAMES = [
    "ws-jsmith-01",
    "ws-agarcia-01",
    "ws-mchen-01",
    "srv-db-01",
    "srv-dc-01",
    "srv-file-01",
    "srv-web-01",
]


def _generate_baseline_endpoint_events(
    base_time: datetime, count: int
) -> list[EndpointEvent]:
    """Generate normal baseline endpoint events.

    Args:
        base_time: Starting timestamp for event generation.
        count: Number of events to generate.

    Returns:
        list[EndpointEvent]: Normal endpoint events.
    """
    entries = []
    for _ in range(count):
        ts = base_time + timedelta(seconds=random.randint(0, 3600))
        proc_name, parent, cmd = random.choice(NORMAL_PROCESSES)
        entries.append(
            EndpointEvent(
                timestamp=ts.isoformat(),
                hostname=random.choice(HOSTNAMES),
                process_name=proc_name,
                process_hash=random.choice(CLEAN_HASHES),
                parent_process=parent,
                command_line=cmd,
                event_type="process_start",
            )
        )
    return entries


def generate_brute_force_endpoint_events(
    base_time: datetime,
) -> list[EndpointEvent]:
    """Generate endpoint events for a brute force scenario (minimal endpoint activity).

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[EndpointEvent]: Endpoint events.
    """
    return _generate_baseline_endpoint_events(base_time, 10)


def generate_insider_threat_endpoint_events(
    base_time: datetime,
) -> list[EndpointEvent]:
    """Generate endpoint events for an insider threat scenario.

    Shows unusual file access and data staging activity.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[EndpointEvent]: Endpoint events showing insider activity.
    """
    entries = _generate_baseline_endpoint_events(base_time, 10)
    insider_host = "ws-mchen-01"  # Using mchen's workstation for kpatel

    # Accessing sensitive files
    sensitive_files = [
        "C:\\Confidential\\customer_database.csv",
        "C:\\Confidential\\financial_report_2025.xlsx",
        "C:\\Confidential\\employee_salaries.csv",
        "C:\\Confidential\\api_keys_backup.txt",
    ]
    for i, filepath in enumerate(sensitive_files):
        ts = base_time + timedelta(minutes=35 + i * 3)
        entries.append(
            EndpointEvent(
                timestamp=ts.isoformat(),
                hostname=insider_host,
                process_name="explorer.exe",
                process_hash=CLEAN_HASHES[0],
                parent_process="explorer.exe",
                command_line=f"explorer.exe /select,{filepath}",
                event_type="file_write",
            )
        )

    # Compressing data for exfiltration
    entries.append(
        EndpointEvent(
            timestamp=(base_time + timedelta(minutes=50)).isoformat(),
            hostname=insider_host,
            process_name="7z.exe",
            process_hash=CLEAN_HASHES[1],
            parent_process="cmd.exe",
            command_line="7z.exe a -p C:\\Temp\\backup.7z C:\\Confidential\\*",
            event_type="process_start",
        )
    )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_api_key_compromise_endpoint_events(
    base_time: datetime,
) -> list[EndpointEvent]:
    """Generate endpoint events for an API key compromise scenario (minimal).

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[EndpointEvent]: Endpoint events.
    """
    return _generate_baseline_endpoint_events(base_time, 10)


def generate_malware_endpoint_events(base_time: datetime) -> list[EndpointEvent]:
    """Generate endpoint events for a malware lateral movement scenario.

    Shows phishing payload execution, malware process trees, credential dumping,
    and lateral movement via PsExec/WMI.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[EndpointEvent]: Endpoint events showing malware activity.
    """
    entries = _generate_baseline_endpoint_events(base_time, 10)
    compromised_host = "ws-jsmith-01"
    cobalt_hash = list(MALWARE_HASHES.keys())[0]
    mimikatz_hash = list(MALWARE_HASHES.keys())[1]

    # Phase 1: Phishing payload - Word macro spawning PowerShell
    phish_time = base_time + timedelta(minutes=8)
    entries.append(
        EndpointEvent(
            timestamp=phish_time.isoformat(),
            hostname=compromised_host,
            process_name="WINWORD.EXE",
            process_hash=CLEAN_HASHES[0],
            parent_process="explorer.exe",
            command_line="WINWORD.EXE /n C:\\Users\\jsmith\\Downloads\\invoice_Q4.docm",
            event_type="process_start",
        )
    )

    # PowerShell download cradle
    entries.append(
        EndpointEvent(
            timestamp=(phish_time + timedelta(seconds=5)).isoformat(),
            hostname=compromised_host,
            process_name="powershell.exe",
            process_hash=CLEAN_HASHES[2],
            parent_process="WINWORD.EXE",
            command_line=(
                "powershell.exe -nop -w hidden -enc "
                "SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIABOAGUAdAAuAFcAZQBiAEMAbABpAGUAbgB0ACkA"
            ),
            event_type="process_start",
        )
    )

    # Phase 2: Cobalt Strike beacon
    entries.append(
        EndpointEvent(
            timestamp=(phish_time + timedelta(seconds=15)).isoformat(),
            hostname=compromised_host,
            process_name="rundll32.exe",
            process_hash=cobalt_hash,
            parent_process="powershell.exe",
            command_line="rundll32.exe C:\\Users\\jsmith\\AppData\\Local\\Temp\\beacon.dll,Start",
            event_type="process_start",
        )
    )

    # Phase 3: Credential dumping with Mimikatz
    cred_dump_time = phish_time + timedelta(minutes=10)
    entries.append(
        EndpointEvent(
            timestamp=cred_dump_time.isoformat(),
            hostname=compromised_host,
            process_name="mimikatz.exe",
            process_hash=mimikatz_hash,
            parent_process="rundll32.exe",
            command_line="mimikatz.exe privilege::debug sekurlsa::logonpasswords exit",
            event_type="process_start",
        )
    )

    # Phase 4: Lateral movement via PsExec
    lateral_targets = [
        ("srv-db-01", base_time + timedelta(minutes=25)),
        ("srv-dc-01", base_time + timedelta(minutes=30)),
        ("srv-file-01", base_time + timedelta(minutes=35)),
    ]
    for target_host, ts in lateral_targets:
        entries.append(
            EndpointEvent(
                timestamp=ts.isoformat(),
                hostname=target_host,
                process_name="PSEXESVC.exe",
                process_hash=CLEAN_HASHES[0],
                parent_process="services.exe",
                command_line="C:\\Windows\\PSEXESVC.exe",
                event_type="process_start",
            )
        )
        entries.append(
            EndpointEvent(
                timestamp=(ts + timedelta(seconds=2)).isoformat(),
                hostname=target_host,
                process_name="cmd.exe",
                process_hash=CLEAN_HASHES[1],
                parent_process="PSEXESVC.exe",
                command_line="cmd.exe /c whoami && ipconfig /all && net user /domain",
                event_type="process_start",
            )
        )

    # Network connection from beacon to C2
    entries.append(
        EndpointEvent(
            timestamp=(phish_time + timedelta(seconds=20)).isoformat(),
            hostname=compromised_host,
            process_name="rundll32.exe",
            process_hash=cobalt_hash,
            parent_process="powershell.exe",
            command_line="rundll32.exe -> 198.51.100.42:8443",
            event_type="network_connection",
        )
    )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_cloud_misconfig_endpoint_events(
    base_time: datetime,
) -> list[EndpointEvent]:
    """Generate endpoint events for a cloud misconfiguration scenario (minimal).

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[EndpointEvent]: Endpoint events.
    """
    return _generate_baseline_endpoint_events(base_time, 10)
