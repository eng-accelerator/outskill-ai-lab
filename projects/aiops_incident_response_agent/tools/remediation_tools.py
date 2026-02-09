"""Tools for proposing remediation actions.

These tools are used by the Remediation Agent to look up runbooks
and propose specific remediation actions based on the root cause analysis.
"""

import json
import logging

from agents import RunContextWrapper, function_tool
from aiops_incident_response_agent.simulators.scenario_engine import \
    ScenarioData

logger = logging.getLogger(__name__)

# Simulated runbook knowledge base
RUNBOOKS: dict[str, dict] = {
    "memory_leak": {
        "title": "Memory Leak Remediation Runbook",
        "steps": [
            "1. Identify the leaking service and pod(s)",
            "2. Capture heap dump for analysis: kubectl exec <pod> -- jmap -dump:format=b,file=/tmp/heap.hprof <pid>",
            "3. Restart affected pods: kubectl rollout restart deployment/<service>",
            "4. Monitor memory usage post-restart",
            "5. If leak recurs, consider rolling back to previous version",
            "6. File bug ticket with heap dump attached for dev team analysis",
        ],
        "estimated_time_minutes": 15,
    },
    "deployment_regression": {
        "title": "Deployment Regression Runbook",
        "steps": [
            "1. Confirm the regression correlates with the deployment timestamp",
            "2. Check deployment diff for breaking changes",
            "3. Initiate rollback: kubectl rollout undo deployment/<service>",
            "4. Verify error rates return to baseline after rollback",
            "5. Notify the deploying team of the regression",
            "6. Block re-deployment until root cause is fixed",
        ],
        "estimated_time_minutes": 10,
    },
    "database_exhaustion": {
        "title": "Database Connection Pool Exhaustion Runbook",
        "steps": [
            "1. Check active connections: SELECT count(*) FROM pg_stat_activity",
            "2. Identify long-running queries: SELECT * FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC",
            "3. Kill long-running queries if safe: SELECT pg_terminate_backend(<pid>)",
            "4. Increase connection pool size temporarily in database-proxy config",
            "5. Restart database-proxy to apply new pool settings",
            "6. Investigate and fix the query or connection leak causing exhaustion",
        ],
        "estimated_time_minutes": 20,
    },
    "network_partition": {
        "title": "Network Partition Remediation Runbook",
        "steps": [
            "1. Verify network connectivity: kubectl exec <pod> -- curl -s <target-service>:8080/health",
            "2. Check network policies: kubectl get networkpolicies -n <namespace>",
            "3. Check node status: kubectl get nodes -o wide",
            "4. If node issue, cordon and drain: kubectl cordon <node> && kubectl drain <node>",
            "5. If network policy issue, update policies to restore connectivity",
            "6. Verify service mesh / ingress controller status",
        ],
        "estimated_time_minutes": 25,
    },
    "cpu_spike": {
        "title": "CPU Spike Remediation Runbook",
        "steps": [
            "1. Identify the pod(s) with high CPU: kubectl top pods -n <namespace>",
            "2. Check for runaway processes: kubectl exec <pod> -- top -b -n 1",
            "3. If caused by traffic spike, scale horizontally: kubectl scale deployment/<service> --replicas=<n>",
            "4. If caused by code bug, restart the pod: kubectl delete pod <pod>",
            "5. Consider enabling HPA if not already configured",
            "6. Monitor CPU after remediation",
        ],
        "estimated_time_minutes": 10,
    },
}


@function_tool
def lookup_runbook(category: str) -> str:
    """Look up the remediation runbook for a given incident category.

    Available categories: memory_leak, deployment_regression,
    database_exhaustion, network_partition, cpu_spike.

    Args:
        category: The incident category to look up.

    Returns:
        str: JSON string of the runbook with title, steps, and estimated time.
    """
    logger.info("Looking up runbook for category: %s", category)
    runbook = RUNBOOKS.get(category)
    if not runbook:
        return json.dumps(
            {
                "error": f"No runbook found for category: {category}",
                "available_categories": list(RUNBOOKS.keys()),
            }
        )
    return json.dumps(runbook, indent=2)


@function_tool
def propose_scaling_action(
    service: str,
    current_replicas: int = 2,
    target_replicas: int = 4,
    reason: str = "",
) -> str:
    """Propose a horizontal scaling action for a service.

    Generates a scaling proposal with the command and expected impact.

    Args:
        service: Target service to scale.
        current_replicas: Current number of replicas.
        target_replicas: Proposed number of replicas.
        reason: Reason for the scaling action.

    Returns:
        str: JSON string of the scaling proposal.
    """
    logger.info(
        "Proposing scale %s: %d -> %d replicas",
        service,
        current_replicas,
        target_replicas,
    )
    return json.dumps(
        {
            "action": (
                "scale_up" if target_replicas > current_replicas else "scale_down"
            ),
            "service": service,
            "current_replicas": current_replicas,
            "target_replicas": target_replicas,
            "command": f"kubectl scale deployment/{service} --replicas={target_replicas}",
            "reason": reason,
            "risk_level": "low" if target_replicas <= 6 else "medium",
            "requires_approval": target_replicas > 6,
        },
        indent=2,
    )


@function_tool
def propose_rollback(
    service: str,
    current_version: str = "",
    target_version: str = "",
    reason: str = "",
) -> str:
    """Propose a rollback to a previous version of a service.

    Generates a rollback proposal with the command and expected impact.

    Args:
        service: Target service to rollback.
        current_version: Current version string.
        target_version: Version to rollback to.
        reason: Reason for the rollback.

    Returns:
        str: JSON string of the rollback proposal.
    """
    logger.info(
        "Proposing rollback %s: %s -> %s", service, current_version, target_version
    )
    return json.dumps(
        {
            "action": "rollback",
            "service": service,
            "current_version": current_version,
            "target_version": target_version,
            "command": f"kubectl rollout undo deployment/{service}",
            "reason": reason,
            "risk_level": "medium",
            "requires_approval": True,
        },
        indent=2,
    )


@function_tool
def propose_config_change(
    service: str,
    config_key: str = "",
    current_value: str = "",
    proposed_value: str = "",
    reason: str = "",
) -> str:
    """Propose a configuration change for a service.

    Generates a config change proposal with the expected impact.

    Args:
        service: Target service.
        config_key: Configuration key to change.
        current_value: Current configuration value.
        proposed_value: Proposed new value.
        reason: Reason for the change.

    Returns:
        str: JSON string of the config change proposal.
    """
    logger.info(
        "Proposing config change on %s: %s = %s -> %s",
        service,
        config_key,
        current_value,
        proposed_value,
    )
    return json.dumps(
        {
            "action": "config_change",
            "service": service,
            "config_key": config_key,
            "current_value": current_value,
            "proposed_value": proposed_value,
            "command": f"kubectl set env deployment/{service} {config_key}={proposed_value}",
            "reason": reason,
            "risk_level": "medium",
            "requires_approval": True,
        },
        indent=2,
    )
