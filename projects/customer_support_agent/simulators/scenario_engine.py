"""Scenario engine that orchestrates realistic customer support scenarios.

Coordinates all simulators to produce correlated customer, order, billing,
and knowledge base data for a given support scenario type.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from customer_support_agent.models.billing import Invoice, Payment, Refund, Subscription
from customer_support_agent.models.customer import CustomerProfile
from customer_support_agent.models.orders import Order, Return
from customer_support_agent.models.support import KBArticle, SupportTicket
from customer_support_agent.simulators.billing_simulator import (
    generate_billing_dispute_billing,
    generate_complex_escalation_billing,
    generate_delayed_order_billing,
    generate_refund_request_billing,
    generate_technical_issue_billing,
)
from customer_support_agent.simulators.customer_simulator import (
    generate_customer_profiles,
    get_customer_by_id,
)
from customer_support_agent.simulators.knowledge_base_simulator import generate_knowledge_base
from customer_support_agent.simulators.order_simulator import (
    generate_billing_dispute_data,
    generate_complex_escalation_data,
    generate_delayed_order_data,
    generate_refund_request_data,
    generate_technical_issue_data,
)

logger = logging.getLogger(__name__)

# Supported scenario types
ScenarioType = Literal[
    "delayed_order",
    "refund_request",
    "billing_dispute",
    "technical_issue",
    "complex_escalation",
]

SCENARIO_DESCRIPTIONS: dict[ScenarioType, str] = {
    "delayed_order": (
        "Customer inquiring about an order that's been stuck in 'shipped' "
        "with no tracking updates for 5 days. Wants to know where their package is."
    ),
    "refund_request": (
        "Customer received a defective Smart Watch Pro X with dead pixels and "
        "unresponsive touch screen. Wants a full refund for the product."
    ),
    "billing_dispute": (
        "Enterprise customer was double-charged for their monthly subscription. "
        "Also wants to downgrade from Enterprise to Professional plan."
    ),
    "technical_issue": (
        "Customer can't log into their account after a password reset. "
        "Also experiencing API authentication failures with their developer tools."
    ),
    "complex_escalation": (
        "Angry platinum customer with multiple issues: received wrong item in recent order, "
        "overcharged on subscription ($149.99 instead of $99.99), and product features "
        "not working. Demands immediate resolution and compensation."
    ),
}

SCENARIO_CUSTOMER_QUERIES: dict[ScenarioType, str] = {
    "delayed_order": (
        "Hi, I ordered wireless headphones and a case 10 days ago (order ORD-2024-1001) "
        "and tracking says it's been sitting at a FedEx distribution center in Memphis for "
        "5 days now with no updates. The estimated delivery was 2 days ago! I need these "
        "for a trip next week. Can you help me figure out what's going on?"
    ),
    "refund_request": (
        "I'm really disappointed. I just received my Smart Watch Pro X (order ORD-2024-1042) "
        "and the screen has dead pixels and the touch screen barely works. I paid $400 for this "
        "and it's clearly defective. I want a full refund immediately. This is unacceptable "
        "quality for a premium product."
    ),
    "billing_dispute": (
        "I just checked my credit card statement and I was charged TWICE for my Enterprise "
        "subscription this month - two charges of $99.99 on the same day! This is the second "
        "billing issue I've had. I want the duplicate charge refunded AND I want to downgrade "
        "to Professional plan. I'm losing trust in your billing system."
    ),
    "technical_issue": (
        "I can't log into my account at all. I tried resetting my password but the reset email "
        "never arrived. I've checked spam. I'm a developer and I also can't authenticate with "
        "the API - getting 401 errors on all my requests. My API key was working fine yesterday. "
        "This is blocking my work. Please help urgently."
    ),
    "complex_escalation": (
        "I am EXTREMELY frustrated. I've been a loyal platinum customer for 6 years spending "
        "over $42,000 and this is how I'm treated? First, you sent me the WRONG keyboard - "
        "I ordered the Premium Ergonomic and got the basic Standard one. Second, I was charged "
        "$149.99 for my Enterprise plan when it should be $99.99 - that's $50 overcharge! "
        "And third, the 4K monitor I bought last month has started flickering. I want ALL of "
        "these fixed NOW, a full refund for the keyboard, the billing corrected, and I expect "
        "compensation for this terrible experience. If this isn't resolved today, I'm cancelling "
        "everything."
    ),
}

# Map scenarios to their primary customer
SCENARIO_CUSTOMERS: dict[ScenarioType, str] = {
    "delayed_order": "CUST-002",
    "refund_request": "CUST-003",
    "billing_dispute": "CUST-005",
    "technical_issue": "CUST-006",
    "complex_escalation": "CUST-007",
}


@dataclass
class ScenarioData:
    """Complete customer support data for a simulated scenario.

    Attributes:
        scenario_type: The type of support scenario.
        description: Human-readable description of the scenario.
        customer_query: The customer's initial message/complaint.
        base_time: Starting timestamp for the scenario.
        customer: The primary customer profile for this scenario.
        all_customers: All customer profiles in the system.
        orders: Orders associated with the customer.
        returns: Return requests for the customer.
        subscriptions: Customer subscriptions.
        invoices: Customer invoices.
        payments: Customer payment history.
        refunds: Any existing refunds.
        knowledge_base: Available knowledge base articles.
        ticket: The support ticket for this interaction.
    """

    scenario_type: ScenarioType
    description: str
    customer_query: str
    base_time: datetime
    customer: CustomerProfile
    all_customers: list[CustomerProfile] = field(default_factory=list)
    orders: list[Order] = field(default_factory=list)
    returns: list[Return] = field(default_factory=list)
    subscriptions: list[Subscription] = field(default_factory=list)
    invoices: list[Invoice] = field(default_factory=list)
    payments: list[Payment] = field(default_factory=list)
    refunds: list[Refund] = field(default_factory=list)
    knowledge_base: list[KBArticle] = field(default_factory=list)
    ticket: SupportTicket | None = None


def _generate_ticket(scenario_type: ScenarioType, customer_id: str, base_time: datetime) -> SupportTicket:
    """Generate a support ticket for the given scenario.

    Args:
        scenario_type: The type of support scenario.
        customer_id: The customer filing the ticket.
        base_time: Timestamp for ticket creation.

    Returns:
        SupportTicket: A support ticket for the scenario.
    """
    match scenario_type:
        case "delayed_order":
            return SupportTicket(
                ticket_id="TKT-2024-5001",
                customer_id=customer_id,
                category="order_issue",
                priority="high",
                subject="Order stuck in transit - no tracking updates for 5 days",
                description="Order ORD-2024-1001 shipped 10 days ago, tracking hasn't updated in 5 days.",
                status="open",
                created_at=base_time.isoformat(),
            )
        case "refund_request":
            return SupportTicket(
                ticket_id="TKT-2024-5002",
                customer_id=customer_id,
                category="order_issue",
                priority="high",
                subject="Defective Smart Watch Pro X - requesting full refund",
                description="Screen has dead pixels, touch unresponsive. Order ORD-2024-1042.",
                status="open",
                created_at=base_time.isoformat(),
            )
        case "billing_dispute":
            return SupportTicket(
                ticket_id="TKT-2024-5003",
                customer_id=customer_id,
                category="billing_issue",
                priority="high",
                subject="Double-charged for Enterprise subscription + plan downgrade request",
                description="Two charges of $99.99 on same day. Wants refund and downgrade to Professional.",
                status="open",
                created_at=base_time.isoformat(),
            )
        case "technical_issue":
            return SupportTicket(
                ticket_id="TKT-2024-5004",
                customer_id=customer_id,
                category="technical_issue",
                priority="urgent",
                subject="Cannot login + API authentication failures",
                description="Password reset email not arriving. API returning 401 on all requests.",
                status="open",
                created_at=base_time.isoformat(),
            )
        case "complex_escalation":
            return SupportTicket(
                ticket_id="TKT-2024-5005",
                customer_id=customer_id,
                category="complaint",
                priority="urgent",
                subject="Multiple issues: wrong item, billing overcharge, product defect",
                description="Platinum customer with 3 simultaneous issues. Threatening to cancel.",
                status="open",
                created_at=base_time.isoformat(),
            )


def generate_scenario(scenario_type: ScenarioType) -> ScenarioData:
    """Generate a complete customer support scenario with correlated data.

    Coordinates all simulators to produce customer profiles, orders, billing data,
    and knowledge base articles for the specified scenario type.

    Args:
        scenario_type: The type of support scenario to simulate.

    Returns:
        ScenarioData: Complete support data for the scenario.

    Raises:
        AssertionError: If scenario_type is not a supported scenario.
    """
    assert scenario_type in SCENARIO_DESCRIPTIONS, f"Unknown scenario: {scenario_type}"

    base_time = datetime.now(timezone.utc)
    logger.info("Generating scenario: %s", scenario_type)

    # Generate shared data
    all_customers = generate_customer_profiles()
    knowledge_base = generate_knowledge_base()

    customer_id = SCENARIO_CUSTOMERS[scenario_type]
    customer = get_customer_by_id(all_customers, customer_id)
    assert customer is not None, f"Customer {customer_id} not found"

    # Generate scenario-specific data
    order_generators = {
        "delayed_order": generate_delayed_order_data,
        "refund_request": generate_refund_request_data,
        "billing_dispute": generate_billing_dispute_data,
        "technical_issue": generate_technical_issue_data,
        "complex_escalation": generate_complex_escalation_data,
    }

    billing_generators = {
        "delayed_order": generate_delayed_order_billing,
        "refund_request": generate_refund_request_billing,
        "billing_dispute": generate_billing_dispute_billing,
        "technical_issue": generate_technical_issue_billing,
        "complex_escalation": generate_complex_escalation_billing,
    }

    orders, returns = order_generators[scenario_type](base_time)
    subs, invoices, payments, refunds = billing_generators[scenario_type](base_time)
    ticket = _generate_ticket(scenario_type, customer_id, base_time)

    logger.info(
        "Scenario generated: orders=%d, returns=%d, subs=%d, invoices=%d, payments=%d, kb=%d",
        len(orders), len(returns), len(subs), len(invoices), len(payments), len(knowledge_base),
    )

    return ScenarioData(
        scenario_type=scenario_type,
        description=SCENARIO_DESCRIPTIONS[scenario_type],
        customer_query=SCENARIO_CUSTOMER_QUERIES[scenario_type],
        base_time=base_time,
        customer=customer,
        all_customers=all_customers,
        orders=orders,
        returns=returns,
        subscriptions=subs,
        invoices=invoices,
        payments=payments,
        refunds=refunds,
        knowledge_base=knowledge_base,
        ticket=ticket,
    )


def list_scenarios() -> list[tuple[ScenarioType, str]]:
    """List all available customer support scenarios.

    Returns:
        list[tuple[ScenarioType, str]]: List of (scenario_type, description) tuples.
    """
    return [(k, v) for k, v in SCENARIO_DESCRIPTIONS.items()]
