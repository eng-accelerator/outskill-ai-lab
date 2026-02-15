"""Billing and subscription simulator.

Generates realistic billing data including subscriptions, invoices,
payments, and refunds for various customer support scenarios.
"""

import logging
from datetime import datetime, timedelta, timezone

from customer_support_agent.models.billing import Invoice, Payment, Refund, Subscription

logger = logging.getLogger(__name__)


def _iso(dt: datetime) -> str:
    """Convert datetime to ISO 8601 string.

    Args:
        dt: Datetime to convert.

    Returns:
        str: ISO 8601 formatted string.
    """
    return dt.isoformat()


def generate_delayed_order_billing(
    base_time: datetime,
) -> tuple[list[Subscription], list[Invoice], list[Payment], list[Refund]]:
    """Generate billing data for the delayed_order scenario.

    Minimal billing data since this scenario focuses on order tracking.

    Args:
        base_time: Reference timestamp for generating dates.

    Returns:
        tuple: Subscriptions, invoices, payments, and refunds.
    """
    subs = [
        Subscription(
            sub_id="SUB-002",
            customer_id="CUST-002",
            plan="professional",
            monthly_amount=29.99,
            billing_cycle_day=15,
            status="active",
            started_at=_iso(base_time - timedelta(days=365)),
            next_billing_date=_iso(base_time + timedelta(days=6)),
        ),
    ]

    invoices = [
        Invoice(
            invoice_id="INV-2024-0200",
            customer_id="CUST-002",
            amount=29.99,
            status="completed",
            issued_at=_iso(base_time - timedelta(days=15)),
            due_date=_iso(base_time - timedelta(days=1)),
            items=["Professional Plan - Monthly"],
        ),
    ]

    payments = [
        Payment(
            payment_id="PAY-2024-0200",
            customer_id="CUST-002",
            amount=29.99,
            method="credit_card",
            status="completed",
            timestamp=_iso(base_time - timedelta(days=15)),
            invoice_id="INV-2024-0200",
        ),
    ]

    logger.info("Generated billing data for delayed_order scenario")
    return subs, invoices, payments, []


def generate_refund_request_billing(
    base_time: datetime,
) -> tuple[list[Subscription], list[Invoice], list[Payment], list[Refund]]:
    """Generate billing data for the refund_request scenario.

    Includes the payment for the defective product order.

    Args:
        base_time: Reference timestamp for generating dates.

    Returns:
        tuple: Subscriptions, invoices, payments, and refunds.
    """
    seven_days_ago = base_time - timedelta(days=7)

    subs = [
        Subscription(
            sub_id="SUB-003",
            customer_id="CUST-003",
            plan="starter",
            monthly_amount=9.99,
            billing_cycle_day=1,
            status="active",
            started_at=_iso(base_time - timedelta(days=180)),
            next_billing_date=_iso(base_time + timedelta(days=22)),
        ),
    ]

    invoices = [
        Invoice(
            invoice_id="INV-2024-0310",
            customer_id="CUST-003",
            amount=459.97,
            status="completed",
            issued_at=_iso(seven_days_ago),
            due_date=_iso(seven_days_ago),
            items=["Smart Watch Pro X x1", "Watch Band - Leather x2"],
        ),
    ]

    payments = [
        Payment(
            payment_id="PAY-2024-0310",
            customer_id="CUST-003",
            amount=459.97,
            method="debit_card",
            status="completed",
            timestamp=_iso(seven_days_ago),
            invoice_id="INV-2024-0310",
        ),
    ]

    logger.info("Generated billing data for refund_request scenario")
    return subs, invoices, payments, []


def generate_billing_dispute_billing(
    base_time: datetime,
) -> tuple[list[Subscription], list[Invoice], list[Payment], list[Refund]]:
    """Generate billing data for the billing_dispute scenario.

    Creates a double-charge situation where the customer was billed twice
    for their enterprise subscription in the same billing cycle.

    Args:
        base_time: Reference timestamp for generating dates.

    Returns:
        tuple: Subscriptions, invoices, payments, and refunds.
    """
    three_days_ago = base_time - timedelta(days=3)

    subs = [
        Subscription(
            sub_id="SUB-005",
            customer_id="CUST-005",
            plan="enterprise",
            monthly_amount=99.99,
            billing_cycle_day=10,
            status="active",
            started_at=_iso(base_time - timedelta(days=730)),
            next_billing_date=_iso(base_time + timedelta(days=7)),
        ),
    ]

    invoices = [
        Invoice(
            invoice_id="INV-2024-0500",
            customer_id="CUST-005",
            amount=99.99,
            status="completed",
            issued_at=_iso(three_days_ago),
            due_date=_iso(three_days_ago),
            items=["Enterprise Plan - Monthly"],
        ),
        Invoice(
            invoice_id="INV-2024-0501",
            customer_id="CUST-005",
            amount=99.99,
            status="completed",
            issued_at=_iso(three_days_ago),
            due_date=_iso(three_days_ago),
            items=["Enterprise Plan - Monthly (DUPLICATE)"],
        ),
    ]

    payments = [
        Payment(
            payment_id="PAY-2024-0500",
            customer_id="CUST-005",
            amount=99.99,
            method="credit_card",
            status="completed",
            timestamp=_iso(three_days_ago),
            invoice_id="INV-2024-0500",
        ),
        Payment(
            payment_id="PAY-2024-0501",
            customer_id="CUST-005",
            amount=99.99,
            method="credit_card",
            status="completed",
            timestamp=_iso(three_days_ago),
            invoice_id="INV-2024-0501",
        ),
    ]

    logger.info("Generated billing data for billing_dispute scenario (double-charge)")
    return subs, invoices, payments, []


def generate_technical_issue_billing(
    base_time: datetime,
) -> tuple[list[Subscription], list[Invoice], list[Payment], list[Refund]]:
    """Generate billing data for the technical_issue scenario.

    Active subscription with recent successful payment.

    Args:
        base_time: Reference timestamp for generating dates.

    Returns:
        tuple: Subscriptions, invoices, payments, and refunds.
    """
    subs = [
        Subscription(
            sub_id="SUB-006",
            customer_id="CUST-006",
            plan="professional",
            monthly_amount=29.99,
            billing_cycle_day=20,
            status="active",
            started_at=_iso(base_time - timedelta(days=540)),
            next_billing_date=_iso(base_time + timedelta(days=11)),
        ),
    ]

    invoices = [
        Invoice(
            invoice_id="INV-2024-0600",
            customer_id="CUST-006",
            amount=29.99,
            status="completed",
            issued_at=_iso(base_time - timedelta(days=10)),
            due_date=_iso(base_time - timedelta(days=10)),
            items=["Professional Plan - Monthly"],
        ),
    ]

    payments = [
        Payment(
            payment_id="PAY-2024-0600",
            customer_id="CUST-006",
            amount=29.99,
            method="paypal",
            status="completed",
            timestamp=_iso(base_time - timedelta(days=10)),
            invoice_id="INV-2024-0600",
        ),
    ]

    logger.info("Generated billing data for technical_issue scenario")
    return subs, invoices, payments, []


def generate_complex_escalation_billing(
    base_time: datetime,
) -> tuple[list[Subscription], list[Invoice], list[Payment], list[Refund]]:
    """Generate billing data for the complex_escalation scenario.

    Platinum customer with enterprise subscription that has a billing error:
    charged at wrong rate after a plan change.

    Args:
        base_time: Reference timestamp for generating dates.

    Returns:
        tuple: Subscriptions, invoices, payments, and refunds.
    """
    five_days_ago = base_time - timedelta(days=5)

    subs = [
        Subscription(
            sub_id="SUB-007",
            customer_id="CUST-007",
            plan="enterprise",
            monthly_amount=99.99,
            billing_cycle_day=5,
            status="active",
            started_at=_iso(base_time - timedelta(days=1825)),
            next_billing_date=_iso(base_time + timedelta(days=26)),
        ),
    ]

    invoices = [
        Invoice(
            invoice_id="INV-2024-0700",
            customer_id="CUST-007",
            amount=149.99,
            status="completed",
            issued_at=_iso(five_days_ago),
            due_date=_iso(five_days_ago),
            items=[
                "Enterprise Plan - Monthly (INCORRECT RATE: $149.99 instead of $99.99)"
            ],
        ),
        Invoice(
            invoice_id="INV-2024-0650",
            customer_id="CUST-007",
            amount=99.99,
            status="completed",
            issued_at=_iso(base_time - timedelta(days=35)),
            due_date=_iso(base_time - timedelta(days=35)),
            items=["Enterprise Plan - Monthly"],
        ),
    ]

    payments = [
        Payment(
            payment_id="PAY-2024-0700",
            customer_id="CUST-007",
            amount=149.99,
            method="credit_card",
            status="completed",
            timestamp=_iso(five_days_ago),
            invoice_id="INV-2024-0700",
        ),
        Payment(
            payment_id="PAY-2024-0650",
            customer_id="CUST-007",
            amount=99.99,
            method="credit_card",
            status="completed",
            timestamp=_iso(base_time - timedelta(days=35)),
            invoice_id="INV-2024-0650",
        ),
    ]

    logger.info("Generated billing data for complex_escalation scenario (wrong rate)")
    return subs, invoices, payments, []
