"""Data models for security analysis results.

Defines structured types for authentication logs, network logs, API access logs,
endpoint events, cloud audit entries, IOC matches, and MITRE ATT&CK mappings.
"""

from dataclasses import dataclass, field
from typing import Literal

# Authentication action types
AuthAction = Literal[
    "login_success",
    "login_failure",
    "mfa_challenge",
    "role_change",
    "sudo",
    "logout",
]

# Network firewall actions
NetworkAction = Literal["allow", "deny", "drop"]

# Endpoint event types
EndpointEventType = Literal[
    "process_start",
    "file_write",
    "registry_change",
    "network_connection",
    "dll_load",
]

# Cloud audit result types
CloudAuditResult = Literal["success", "failure"]

# IOC indicator types
IOCType = Literal["ip", "domain", "hash", "url", "email"]


@dataclass(frozen=True)
class AuthLogEntry:
    """A single authentication log entry.

    Attributes:
        timestamp: ISO 8601 timestamp.
        user: Username attempting the action.
        source_ip: IP address of the request origin.
        action: Type of authentication action.
        geo_location: Geographic location string (e.g. 'New York, US').
        user_agent: Browser or client user agent string.
        session_id: Session identifier.
        success: Whether the action was successful.
    """

    timestamp: str
    user: str
    source_ip: str
    action: AuthAction
    geo_location: str
    user_agent: str
    session_id: str
    success: bool = True


@dataclass(frozen=True)
class NetworkLogEntry:
    """A single network/firewall log entry.

    Attributes:
        timestamp: ISO 8601 timestamp.
        source_ip: Source IP address.
        dest_ip: Destination IP address.
        dest_port: Destination port number.
        protocol: Network protocol (TCP, UDP, ICMP, etc.).
        bytes_sent: Bytes sent in the connection.
        bytes_received: Bytes received in the connection.
        action: Firewall action taken.
        rule_name: Name of the firewall rule matched.
    """

    timestamp: str
    source_ip: str
    dest_ip: str
    dest_port: int
    protocol: str
    bytes_sent: int
    bytes_received: int
    action: NetworkAction
    rule_name: str = ""


@dataclass(frozen=True)
class APIAccessEntry:
    """A single API access log entry.

    Attributes:
        timestamp: ISO 8601 timestamp.
        user: User making the API call.
        api_key_id: API key identifier used.
        endpoint: API endpoint path.
        method: HTTP method (GET, POST, etc.).
        status_code: HTTP response status code.
        response_time_ms: Response time in milliseconds.
        source_ip: IP address of the caller.
        user_agent: Client user agent string.
    """

    timestamp: str
    user: str
    api_key_id: str
    endpoint: str
    method: str
    status_code: int
    response_time_ms: int
    source_ip: str
    user_agent: str = ""


@dataclass(frozen=True)
class EndpointEvent:
    """A single endpoint/process event from EDR.

    Attributes:
        timestamp: ISO 8601 timestamp.
        hostname: Host where the event occurred.
        process_name: Name of the process.
        process_hash: SHA256 hash of the process binary.
        parent_process: Parent process name.
        command_line: Full command line of the process.
        event_type: Type of endpoint event.
    """

    timestamp: str
    hostname: str
    process_name: str
    process_hash: str
    parent_process: str
    command_line: str
    event_type: EndpointEventType


@dataclass(frozen=True)
class CloudAuditEntry:
    """A single cloud audit trail entry.

    Attributes:
        timestamp: ISO 8601 timestamp.
        principal: IAM principal performing the action.
        action: Cloud API action performed.
        resource: Target resource ARN/identifier.
        resource_type: Type of cloud resource.
        region: Cloud region.
        result: Whether the action succeeded or failed.
        source_ip: IP address of the caller.
    """

    timestamp: str
    principal: str
    action: str
    resource: str
    resource_type: str
    region: str
    result: CloudAuditResult
    source_ip: str


@dataclass(frozen=True)
class IOCMatch:
    """A match against the Indicator of Compromise database.

    Attributes:
        indicator: The matched indicator value.
        indicator_type: Type of indicator.
        threat_name: Name of the associated threat.
        confidence: Confidence score (0.0 to 1.0).
        source: Intelligence source that reported this IOC.
        first_seen: ISO 8601 timestamp of first sighting.
        last_seen: ISO 8601 timestamp of most recent sighting.
    """

    indicator: str
    indicator_type: IOCType
    threat_name: str
    confidence: float
    source: str
    first_seen: str
    last_seen: str


@dataclass(frozen=True)
class MITREMapping:
    """A mapping to the MITRE ATT&CK framework.

    Attributes:
        tactic_id: MITRE tactic ID (e.g. TA0001).
        tactic_name: MITRE tactic name (e.g. Initial Access).
        technique_id: MITRE technique ID (e.g. T1110).
        technique_name: MITRE technique name (e.g. Brute Force).
        description: Description of how the observed behavior maps.
    """

    tactic_id: str
    tactic_name: str
    technique_id: str
    technique_name: str
    description: str
