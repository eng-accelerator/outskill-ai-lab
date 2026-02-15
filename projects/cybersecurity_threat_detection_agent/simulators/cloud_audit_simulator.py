"""Simulates realistic cloud audit trail data for threat scenarios.

Generates structured cloud audit entries with patterns for normal IAM operations,
S3 bucket policy changes, security group modifications, and credential anomalies.
"""

import random
from datetime import datetime, timedelta

from cybersecurity_threat_detection_agent.models.analysis import CloudAuditEntry

# Normal cloud principals
CLOUD_PRINCIPALS = [
    "arn:aws:iam::123456789012:user/admin",
    "arn:aws:iam::123456789012:user/jsmith",
    "arn:aws:iam::123456789012:role/deploy-role",
    "arn:aws:iam::123456789012:role/monitor-role",
    "arn:aws:iam::123456789012:user/kpatel",
]

# Normal cloud actions
NORMAL_ACTIONS = [
    "s3:GetObject",
    "s3:PutObject",
    "ec2:DescribeInstances",
    "logs:PutLogEvents",
    "cloudwatch:PutMetricData",
    "dynamodb:GetItem",
    "dynamodb:PutItem",
    "lambda:InvokeFunction",
]

# Sensitive/dangerous cloud actions
SENSITIVE_ACTIONS = [
    "s3:PutBucketPolicy",
    "s3:PutBucketAcl",
    "ec2:AuthorizeSecurityGroupIngress",
    "iam:CreateAccessKey",
    "iam:AttachRolePolicy",
    "iam:PutRolePolicy",
    "secretsmanager:GetSecretValue",
    "kms:Decrypt",
    "sts:AssumeRole",
]

REGIONS = ["us-east-1", "us-west-2", "eu-west-1"]


def _generate_baseline_cloud_audit(
    base_time: datetime, count: int
) -> list[CloudAuditEntry]:
    """Generate normal baseline cloud audit entries.

    Args:
        base_time: Starting timestamp for audit generation.
        count: Number of entries to generate.

    Returns:
        list[CloudAuditEntry]: Normal cloud audit entries.
    """
    entries = []
    for _ in range(count):
        ts = base_time + timedelta(seconds=random.randint(0, 3600))
        principal = random.choice(CLOUD_PRINCIPALS)
        action = random.choice(NORMAL_ACTIONS)
        resource_type = action.split(":")[0]
        entries.append(
            CloudAuditEntry(
                timestamp=ts.isoformat(),
                principal=principal,
                action=action,
                resource=f"arn:aws:{resource_type}:us-east-1:123456789012:resource-{random.randint(100, 999)}",
                resource_type=resource_type,
                region=random.choice(REGIONS),
                result="success",
                source_ip=f"10.0.{random.randint(1, 10)}.{random.randint(1, 50)}",
            )
        )
    return entries


def generate_brute_force_cloud_audit(base_time: datetime) -> list[CloudAuditEntry]:
    """Generate cloud audit for a brute force scenario (minimal cloud activity).

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[CloudAuditEntry]: Cloud audit entries.
    """
    return _generate_baseline_cloud_audit(base_time, 10)


def generate_insider_threat_cloud_audit(base_time: datetime) -> list[CloudAuditEntry]:
    """Generate cloud audit for an insider threat scenario.

    Shows privilege escalation via IAM, accessing secrets, and data exfiltration.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[CloudAuditEntry]: Cloud audit entries showing insider threat.
    """
    entries = _generate_baseline_cloud_audit(base_time, 15)
    insider_principal = "arn:aws:iam::123456789012:user/kpatel"
    insider_ip = "10.0.2.45"

    # IAM privilege escalation
    entries.append(
        CloudAuditEntry(
            timestamp=(base_time + timedelta(minutes=15)).isoformat(),
            principal=insider_principal,
            action="iam:AttachRolePolicy",
            resource="arn:aws:iam::123456789012:role/admin-role",
            resource_type="iam",
            region="us-east-1",
            result="success",
            source_ip=insider_ip,
        )
    )

    # Creating new access key
    entries.append(
        CloudAuditEntry(
            timestamp=(base_time + timedelta(minutes=18)).isoformat(),
            principal=insider_principal,
            action="iam:CreateAccessKey",
            resource="arn:aws:iam::123456789012:user/kpatel",
            resource_type="iam",
            region="us-east-1",
            result="success",
            source_ip=insider_ip,
        )
    )

    # Accessing secrets
    for i in range(4):
        ts = base_time + timedelta(minutes=25 + i * 3)
        entries.append(
            CloudAuditEntry(
                timestamp=ts.isoformat(),
                principal=insider_principal,
                action="secretsmanager:GetSecretValue",
                resource=f"arn:aws:secretsmanager:us-east-1:123456789012:secret/prod-db-creds-{i}",
                resource_type="secretsmanager",
                region="us-east-1",
                result="success",
                source_ip=insider_ip,
            )
        )

    # Mass S3 data access
    for i in range(6):
        ts = base_time + timedelta(minutes=40 + i * 2)
        entries.append(
            CloudAuditEntry(
                timestamp=ts.isoformat(),
                principal=insider_principal,
                action="s3:GetObject",
                resource=f"arn:aws:s3:::confidential-data/exports/file-{i}.csv",
                resource_type="s3",
                region="us-east-1",
                result="success",
                source_ip=insider_ip,
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_api_key_compromise_cloud_audit(
    base_time: datetime,
) -> list[CloudAuditEntry]:
    """Generate cloud audit for an API key compromise scenario.

    Shows unusual API access patterns from foreign IPs.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[CloudAuditEntry]: Cloud audit entries for API key compromise.
    """
    entries = _generate_baseline_cloud_audit(base_time, 15)
    foreign_ip = "45.155.205.99"

    # Compromised service account accessing resources from foreign IP
    for i in range(8):
        ts = base_time + timedelta(minutes=12 + i * 2)
        entries.append(
            CloudAuditEntry(
                timestamp=ts.isoformat(),
                principal="arn:aws:iam::123456789012:role/deploy-role",
                action=random.choice(
                    ["s3:GetObject", "s3:ListBucket", "dynamodb:Scan"]
                ),
                resource=f"arn:aws:s3:::prod-data/table-{i}",
                resource_type="s3",
                region="us-east-1",
                result="success",
                source_ip=foreign_ip,
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)


def generate_malware_cloud_audit(base_time: datetime) -> list[CloudAuditEntry]:
    """Generate cloud audit for a malware scenario (minimal cloud activity).

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[CloudAuditEntry]: Cloud audit entries.
    """
    return _generate_baseline_cloud_audit(base_time, 10)


def generate_cloud_misconfig_cloud_audit(
    base_time: datetime,
) -> list[CloudAuditEntry]:
    """Generate cloud audit for a cloud misconfiguration scenario.

    Shows S3 bucket policy changes making data public, security group modifications,
    and IAM policy violations.

    Args:
        base_time: Starting timestamp for the scenario.

    Returns:
        list[CloudAuditEntry]: Cloud audit entries showing misconfiguration.
    """
    entries = _generate_baseline_cloud_audit(base_time, 15)
    misconfig_principal = "arn:aws:iam::123456789012:user/jsmith"

    # S3 bucket made public
    entries.append(
        CloudAuditEntry(
            timestamp=(base_time + timedelta(minutes=10)).isoformat(),
            principal=misconfig_principal,
            action="s3:PutBucketPolicy",
            resource="arn:aws:s3:::prod-customer-data",
            resource_type="s3",
            region="us-east-1",
            result="success",
            source_ip="10.0.2.15",
        )
    )

    entries.append(
        CloudAuditEntry(
            timestamp=(base_time + timedelta(minutes=10, seconds=5)).isoformat(),
            principal=misconfig_principal,
            action="s3:PutBucketAcl",
            resource="arn:aws:s3:::prod-customer-data",
            resource_type="s3",
            region="us-east-1",
            result="success",
            source_ip="10.0.2.15",
        )
    )

    # Security group opened to 0.0.0.0/0
    entries.append(
        CloudAuditEntry(
            timestamp=(base_time + timedelta(minutes=12)).isoformat(),
            principal=misconfig_principal,
            action="ec2:AuthorizeSecurityGroupIngress",
            resource="arn:aws:ec2:us-east-1:123456789012:security-group/sg-prod-db",
            resource_type="ec2",
            region="us-east-1",
            result="success",
            source_ip="10.0.2.15",
        )
    )

    # External access to now-public S3 bucket
    external_ips = ["203.0.113.55", "198.51.100.88", "192.0.2.101"]
    for i, ext_ip in enumerate(external_ips):
        for j in range(4):
            ts = base_time + timedelta(minutes=20 + i * 5 + j)
            entries.append(
                CloudAuditEntry(
                    timestamp=ts.isoformat(),
                    principal="anonymous",
                    action="s3:GetObject",
                    resource=f"arn:aws:s3:::prod-customer-data/customers/batch-{j}.csv",
                    resource_type="s3",
                    region="us-east-1",
                    result="success",
                    source_ip=ext_ip,
                )
            )

    # Failed IAM actions from external IPs
    for ext_ip in external_ips[:2]:
        entries.append(
            CloudAuditEntry(
                timestamp=(base_time + timedelta(minutes=35)).isoformat(),
                principal="anonymous",
                action="iam:CreateAccessKey",
                resource="arn:aws:iam::123456789012:user/admin",
                resource_type="iam",
                region="us-east-1",
                result="failure",
                source_ip=ext_ip,
            )
        )

    return sorted(entries, key=lambda e: e.timestamp)
