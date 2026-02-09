"""Billing, subscription, and payment data models.

Defines billing-related types for subscriptions, invoices, payments,
and refunds used in the support agent system.
"""

from dataclasses import dataclass, field
from typing import Literal

# Subscription plan tiers
SubscriptionPlan = Literal["free", "starter", "professional", "enterprise"]

# Subscription statuses
SubscriptionStatus = Literal["active", "paused", "cancelled", "past_due", "trialing"]

# Payment statuses
PaymentStatus = Literal["pending", "completed", "failed", "refunded", "disputed"]

# Payment methods
PaymentMethod = Literal["credit_card", "debit_card", "paypal", "bank_transfer", "crypto"]

# Refund statuses
RefundStatus = Literal["pending", "approved", "processing", "completed", "rejected"]


@dataclass(frozen=True)
class Subscription:
    """A customer subscription to a service plan.

    Attributes:
        sub_id: Unique subscription identifier.
        customer_id: Customer who owns the subscription.
        plan: Current subscription plan.
        monthly_amount: Monthly charge in dollars.
        billing_cycle_day: Day of month for billing (1-28).
        status: Current subscription status.
        started_at: Subscription start date (ISO 8601).
        next_billing_date: Next billing date (ISO 8601).
    """

    sub_id: str
    customer_id: str
    plan: SubscriptionPlan
    monthly_amount: float
    billing_cycle_day: int
    status: SubscriptionStatus
    started_at: str
    next_billing_date: str


@dataclass(frozen=True)
class Invoice:
    """An invoice issued to a customer.

    Attributes:
        invoice_id: Unique invoice identifier.
        customer_id: Customer the invoice is for.
        amount: Total invoice amount in dollars.
        status: Payment status of the invoice.
        issued_at: Invoice issue date (ISO 8601).
        due_date: Payment due date (ISO 8601).
        items: Line item descriptions.
    """

    invoice_id: str
    customer_id: str
    amount: float
    status: PaymentStatus
    issued_at: str
    due_date: str
    items: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Payment:
    """A payment transaction for a customer.

    Attributes:
        payment_id: Unique payment identifier.
        customer_id: Customer who made the payment.
        amount: Payment amount in dollars.
        method: Payment method used.
        status: Current payment status.
        timestamp: Payment timestamp (ISO 8601).
        invoice_id: Associated invoice (if any).
    """

    payment_id: str
    customer_id: str
    amount: float
    method: PaymentMethod
    status: PaymentStatus
    timestamp: str
    invoice_id: str = ""


@dataclass(frozen=True)
class Refund:
    """A refund issued for a payment.

    Attributes:
        refund_id: Unique refund identifier.
        payment_id: The payment being refunded.
        amount: Refund amount in dollars.
        reason: Reason for the refund.
        status: Current refund status.
        processed_at: Refund processing timestamp (ISO 8601).
    """

    refund_id: str
    payment_id: str
    amount: float
    reason: str
    status: RefundStatus
    processed_at: str
