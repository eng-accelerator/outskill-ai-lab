"""Tools for billing information, refunds, subscriptions, and payments.

These tools are used by the Billing Support Agent to investigate
and resolve billing-related customer issues.
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone

from agents import RunContextWrapper, function_tool
from customer_support_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


@function_tool
def get_billing_info(ctx: RunContextWrapper[ScenarioData], customer_id: str) -> str:
    """Get comprehensive billing information for a customer.

    Retrieves the customer's subscription details, recent invoices,
    and payment history. Use this to understand the customer's
    billing situation and identify issues.

    Args:
        ctx: Run context containing the scenario data.
        customer_id: The customer ID to look up billing for.

    Returns:
        str: JSON string with subscription, invoices, and payment data.
    """
    scenario = ctx.context
    logger.info("Fetching billing info for customer: %s", customer_id)

    subs = [asdict(s) for s in scenario.subscriptions if s.customer_id == customer_id]
    invoices = [asdict(i) for i in scenario.invoices if i.customer_id == customer_id]
    payments = [asdict(p) for p in scenario.payments if p.customer_id == customer_id]
    refunds = [asdict(r) for r in scenario.refunds]

    result = {
        "customer_id": customer_id,
        "subscriptions": subs,
        "invoices": invoices,
        "payments": payments,
        "refunds": refunds,
        "summary": {
            "active_subscriptions": len(
                [s for s in subs if s.get("status") == "active"]
            ),
            "total_invoiced": sum(i.get("amount", 0) for i in invoices),
            "total_paid": sum(
                p.get("amount", 0) for p in payments if p.get("status") == "completed"
            ),
            "pending_refunds": len(
                [r for r in refunds if r.get("status") in ("pending", "processing")]
            ),
        },
    }

    logger.info(
        "Billing info: %d subs, %d invoices, %d payments",
        len(subs),
        len(invoices),
        len(payments),
    )
    return json.dumps(result, indent=2)


@function_tool
def process_refund(
    ctx: RunContextWrapper[ScenarioData],
    payment_id: str,
    amount: float,
    reason: str,
) -> str:
    """Process a refund for a specific payment.

    Issues a refund for the specified payment. The refund amount can be
    partial or full. Refunds over $500 require manager approval.

    Args:
        ctx: Run context containing the scenario data.
        payment_id: The payment ID to refund (e.g., 'PAY-2024-0501').
        amount: The refund amount in dollars.
        reason: Reason for the refund.

    Returns:
        str: JSON string with refund confirmation or error.
    """
    scenario = ctx.context
    logger.info(
        "Processing refund: payment=%s, amount=%.2f, reason=%s",
        payment_id,
        amount,
        reason,
    )

    # Find the payment
    target_payment = None
    for payment in scenario.payments:
        if payment.payment_id == payment_id:
            target_payment = payment
            break

    if target_payment is None:
        return json.dumps({"error": f"Payment {payment_id} not found"})

    if target_payment.status == "refunded":
        return json.dumps(
            {
                "error": f"Payment {payment_id} has already been refunded",
            }
        )

    if amount > target_payment.amount:
        return json.dumps(
            {
                "error": f"Refund amount ${amount:.2f} exceeds payment amount ${target_payment.amount:.2f}",
            }
        )

    requires_approval = amount > 500.0

    refund_id = (
        f"REF-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}-{payment_id[-4:]}"
    )
    result = {
        "refund_id": refund_id,
        "payment_id": payment_id,
        "amount": amount,
        "reason": reason,
        "status": "pending_approval" if requires_approval else "approved",
        "requires_approval": requires_approval,
        "estimated_processing": "3-5 business days",
        "message": (
            f"Refund of ${amount:.2f} has been {'submitted for manager approval' if requires_approval else 'approved'}. "
            f"The refund will appear on the customer's statement within 5-10 business days."
        ),
    }

    logger.info(
        "Refund %s created: amount=%.2f, requires_approval=%s",
        refund_id,
        amount,
        requires_approval,
    )
    return json.dumps(result, indent=2)


@function_tool
def update_subscription(
    ctx: RunContextWrapper[ScenarioData],
    customer_id: str,
    new_plan: str,
) -> str:
    """Change a customer's subscription plan.

    Updates the customer's subscription to the specified plan.
    Upgrades take effect immediately; downgrades at next billing cycle.

    Args:
        ctx: Run context containing the scenario data.
        customer_id: The customer ID whose subscription to change.
        new_plan: The target plan ('free', 'starter', 'professional', 'enterprise').

    Returns:
        str: JSON string with subscription change confirmation or error.
    """
    scenario = ctx.context
    logger.info("Updating subscription for %s to plan: %s", customer_id, new_plan)

    valid_plans = {
        "free": 0.00,
        "starter": 9.99,
        "professional": 29.99,
        "enterprise": 99.99,
    }

    if new_plan not in valid_plans:
        return json.dumps(
            {
                "error": f"Invalid plan: {new_plan}. Valid plans: {', '.join(valid_plans.keys())}",
            }
        )

    # Find current subscription
    current_sub = None
    for sub in scenario.subscriptions:
        if sub.customer_id == customer_id:
            current_sub = sub
            break

    if current_sub is None:
        return json.dumps(
            {"error": f"No active subscription found for customer {customer_id}"}
        )

    if current_sub.plan == new_plan:
        return json.dumps(
            {
                "message": f"Customer is already on the {new_plan} plan. No change needed.",
            }
        )

    current_price = valid_plans.get(current_sub.plan, 0)
    new_price = valid_plans[new_plan]
    is_upgrade = new_price > current_price

    result = {
        "customer_id": customer_id,
        "previous_plan": current_sub.plan,
        "new_plan": new_plan,
        "previous_amount": current_price,
        "new_amount": new_price,
        "change_type": "upgrade" if is_upgrade else "downgrade",
        "effective": "immediately" if is_upgrade else "next billing cycle",
        "next_billing_date": current_sub.next_billing_date,
        "message": (
            f"Subscription changed from {current_sub.plan} (${current_price:.2f}/mo) "
            f"to {new_plan} (${new_price:.2f}/mo). "
            f"{'Change effective immediately with prorated billing.' if is_upgrade else 'Change takes effect at next billing cycle. Current plan features remain active until then.'}"
        ),
    }

    logger.info(
        "Subscription updated: %s -> %s for customer %s",
        current_sub.plan,
        new_plan,
        customer_id,
    )
    return json.dumps(result, indent=2)


@function_tool
def check_payment_status(ctx: RunContextWrapper[ScenarioData], payment_id: str) -> str:
    """Check the status of a specific payment transaction.

    Retrieves detailed information about a payment including its current
    status, amount, method, and associated invoice.

    Args:
        ctx: Run context containing the scenario data.
        payment_id: The payment ID to check (e.g., 'PAY-2024-0500').

    Returns:
        str: JSON string with payment details, or error if not found.
    """
    scenario = ctx.context
    logger.info("Checking payment status: %s", payment_id)

    for payment in scenario.payments:
        if payment.payment_id == payment_id:
            payment_data = asdict(payment)

            # Find associated invoice
            for invoice in scenario.invoices:
                if invoice.invoice_id == payment.invoice_id:
                    payment_data["invoice_details"] = asdict(invoice)
                    break

            logger.info("Found payment %s with status: %s", payment_id, payment.status)
            return json.dumps(payment_data, indent=2)

    logger.warning("Payment not found: %s", payment_id)
    return json.dumps({"error": f"Payment {payment_id} not found"})
