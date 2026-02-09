"""Tools for proposing containment actions.

These tools are used by the Containment Agent to propose
specific containment actions based on threat analysis findings.
"""

import json
import logging

from agents import RunContextWrapper, function_tool

from cybersecurity_threat_detection_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)

# High-value accounts that require extra approval
PROTECTED_ACCOUNTS = {"admin", "root", "svc-deploy", "svc-monitor"}

# Critical infrastructure IPs
CRITICAL_IPS = {"10.0.1.50", "10.0.10.5", "10.0.10.6"}


@function_tool
def propose_ip_block(
    ctx: RunContextWrapper[ScenarioData],
    ip_address: str,
    reason: str,
    duration_hours: int = 24,
) -> str:
    """Propose blocking an IP address at the firewall.

    Creates a containment proposal to block inbound and outbound traffic
    from/to a specific IP address. Includes risk assessment and approval requirements.

    Args:
        ctx: Run context containing the scenario data.
        ip_address: The IP address to block.
        reason: Justification for blocking this IP.
        duration_hours: How long to maintain the block (default 24 hours).

    Returns:
        str: JSON string with the containment action proposal.
    """
    logger.info("Proposing IP block: %s", ip_address)

    is_internal = ip_address.startswith("10.") or ip_address.startswith("192.168.")
    is_critical = ip_address in CRITICAL_IPS
    risk_level = "critical" if is_critical else "high" if is_internal else "low"
    requires_approval = is_internal or is_critical

    result = {
        "action_type": "block_ip",
        "target": ip_address,
        "reason": reason,
        "risk_level": risk_level,
        "requires_approval": requires_approval,
        "duration_hours": duration_hours,
        "command": f"firewall-cmd --add-rich-rule='rule family=ipv4 source address={ip_address} reject' --timeout={duration_hours}h",
        "status": "proposed",
        "warnings": [],
    }

    if is_internal:
        result["warnings"].append(f"WARNING: {ip_address} is an internal IP - blocking may disrupt services")
    if is_critical:
        result["warnings"].append(f"CRITICAL: {ip_address} is a critical infrastructure IP - requires SOC lead approval")

    return json.dumps(result, indent=2)


@function_tool
def propose_account_disable(
    ctx: RunContextWrapper[ScenarioData],
    username: str,
    reason: str,
) -> str:
    """Propose disabling a user account.

    Creates a containment proposal to disable a compromised or suspicious
    user account. Protected accounts require additional approval.

    Args:
        ctx: Run context containing the scenario data.
        username: The username to disable.
        reason: Justification for disabling the account.

    Returns:
        str: JSON string with the containment action proposal.
    """
    logger.info("Proposing account disable: %s", username)

    is_protected = username in PROTECTED_ACCOUNTS
    risk_level = "critical" if is_protected else "medium"
    requires_approval = is_protected

    result = {
        "action_type": "disable_account",
        "target": username,
        "reason": reason,
        "risk_level": risk_level,
        "requires_approval": requires_approval,
        "command": f"az ad user update --id {username} --account-enabled false",
        "status": "proposed",
        "warnings": [],
    }

    if is_protected:
        result["warnings"].append(f"CRITICAL: {username} is a protected/service account - disabling may impact production")

    return json.dumps(result, indent=2)


@function_tool
def propose_api_key_revoke(
    ctx: RunContextWrapper[ScenarioData],
    api_key_id: str,
    reason: str,
) -> str:
    """Propose revoking an API key.

    Creates a containment proposal to revoke a compromised API key
    and issue a replacement.

    Args:
        ctx: Run context containing the scenario data.
        api_key_id: The API key identifier to revoke.
        reason: Justification for revoking the key.

    Returns:
        str: JSON string with the containment action proposal.
    """
    logger.info("Proposing API key revocation: %s", api_key_id)

    is_production = "prod" in api_key_id
    risk_level = "high" if is_production else "medium"

    result = {
        "action_type": "revoke_api_key",
        "target": api_key_id,
        "reason": reason,
        "risk_level": risk_level,
        "requires_approval": is_production,
        "command": f"api-admin revoke-key --key-id {api_key_id} --generate-replacement",
        "status": "proposed",
        "warnings": [],
    }

    if is_production:
        result["warnings"].append(f"WARNING: {api_key_id} is a production key - services using this key will be disrupted until replacement is configured")

    return json.dumps(result, indent=2)


@function_tool
def propose_host_isolation(
    ctx: RunContextWrapper[ScenarioData],
    hostname: str,
    reason: str,
) -> str:
    """Propose isolating a host from the network.

    Creates a containment proposal to network-isolate a compromised host,
    allowing only management access for forensic investigation.

    Args:
        ctx: Run context containing the scenario data.
        hostname: The hostname to isolate.
        reason: Justification for isolating the host.

    Returns:
        str: JSON string with the containment action proposal.
    """
    logger.info("Proposing host isolation: %s", hostname)

    is_server = hostname.startswith("srv-")
    risk_level = "high" if is_server else "medium"
    requires_approval = is_server

    result = {
        "action_type": "isolate_host",
        "target": hostname,
        "reason": reason,
        "risk_level": risk_level,
        "requires_approval": requires_approval,
        "command": f"edr-agent isolate --host {hostname} --allow-management-only",
        "status": "proposed",
        "warnings": [],
    }

    if is_server:
        result["warnings"].append(f"WARNING: {hostname} is a server - isolation will impact services running on this host")

    return json.dumps(result, indent=2)
