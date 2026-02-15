"""Order and shipment simulator.

Generates realistic order data with items, shipment tracking,
and return histories for various customer support scenarios.
"""

import logging
from datetime import datetime, timedelta, timezone

from customer_support_agent.models.orders import Order, OrderItem, Return, Shipment

logger = logging.getLogger(__name__)


def _iso(dt: datetime) -> str:
    """Convert datetime to ISO 8601 string.

    Args:
        dt: Datetime to convert.

    Returns:
        str: ISO 8601 formatted string.
    """
    return dt.isoformat()


def generate_delayed_order_data(
    base_time: datetime,
) -> tuple[list[Order], list[Return]]:
    """Generate order data for the delayed_order scenario.

    Creates an order that's been stuck in 'shipped' status with no tracking
    updates for 5 days, plus a few normal completed orders for context.

    Args:
        base_time: Reference timestamp for generating dates.

    Returns:
        tuple[list[Order], list[Return]]: Orders and returns for the scenario.
    """
    five_days_ago = base_time - timedelta(days=5)
    ten_days_ago = base_time - timedelta(days=10)
    thirty_days_ago = base_time - timedelta(days=30)

    orders = [
        Order(
            order_id="ORD-2024-1001",
            customer_id="CUST-002",
            items=[
                OrderItem("PROD-A1", "Wireless Noise-Cancelling Headphones", 1, 249.99),
                OrderItem("PROD-A2", "Premium Headphone Case", 1, 39.99),
            ],
            total_amount=289.98,
            status="shipped",
            created_at=_iso(ten_days_ago),
            updated_at=_iso(five_days_ago),
            shipment=Shipment(
                tracking_number="TRK-9876543210",
                carrier="FedEx",
                status="in_transit",
                estimated_delivery=_iso(base_time - timedelta(days=2)),
                current_location="Distribution Center, Memphis, TN",
                last_update=_iso(five_days_ago),
            ),
            notes="Customer contacted about delay. Package stuck at distribution center.",
        ),
        Order(
            order_id="ORD-2024-0950",
            customer_id="CUST-002",
            items=[
                OrderItem("PROD-B1", "USB-C Hub 7-in-1", 1, 59.99),
            ],
            total_amount=59.99,
            status="delivered",
            created_at=_iso(thirty_days_ago),
            updated_at=_iso(thirty_days_ago + timedelta(days=4)),
            shipment=Shipment(
                tracking_number="TRK-1234567890",
                carrier="UPS",
                status="delivered",
                estimated_delivery=_iso(thirty_days_ago + timedelta(days=3)),
                current_location="Delivered to front door",
                last_update=_iso(thirty_days_ago + timedelta(days=4)),
            ),
        ),
    ]

    logger.info("Generated %d orders for delayed_order scenario", len(orders))
    return orders, []


def generate_refund_request_data(
    base_time: datetime,
) -> tuple[list[Order], list[Return]]:
    """Generate order data for the refund_request scenario.

    Creates an order with a defective product that was delivered,
    and the customer wants a refund.

    Args:
        base_time: Reference timestamp for generating dates.

    Returns:
        tuple[list[Order], list[Return]]: Orders and returns for the scenario.
    """
    seven_days_ago = base_time - timedelta(days=7)
    three_days_ago = base_time - timedelta(days=3)

    orders = [
        Order(
            order_id="ORD-2024-1042",
            customer_id="CUST-003",
            items=[
                OrderItem("PROD-C1", "Smart Watch Pro X", 1, 399.99),
                OrderItem("PROD-C2", "Watch Band - Leather", 2, 29.99),
            ],
            total_amount=459.97,
            status="delivered",
            created_at=_iso(seven_days_ago),
            updated_at=_iso(three_days_ago),
            shipment=Shipment(
                tracking_number="TRK-5555666677",
                carrier="USPS",
                status="delivered",
                estimated_delivery=_iso(seven_days_ago + timedelta(days=3)),
                current_location="Delivered to mailbox",
                last_update=_iso(three_days_ago),
            ),
            notes="Customer reports screen defect on Smart Watch Pro X.",
        ),
    ]

    returns = [
        Return(
            return_id="RET-2024-0088",
            order_id="ORD-2024-1042",
            reason="Defective product - screen has dead pixels and touch not responsive",
            status="requested",
            refund_amount=399.99,
            created_at=_iso(base_time),
        ),
    ]

    logger.info(
        "Generated %d orders, %d returns for refund_request scenario",
        len(orders),
        len(returns),
    )
    return orders, returns


def generate_billing_dispute_data(
    base_time: datetime,
) -> tuple[list[Order], list[Return]]:
    """Generate order data for the billing_dispute scenario.

    Creates minimal order data since this scenario focuses on billing.

    Args:
        base_time: Reference timestamp for generating dates.

    Returns:
        tuple[list[Order], list[Return]]: Orders and returns for the scenario.
    """
    sixty_days_ago = base_time - timedelta(days=60)

    orders = [
        Order(
            order_id="ORD-2024-0890",
            customer_id="CUST-005",
            items=[
                OrderItem("PROD-D1", "Enterprise License Add-on", 1, 199.99),
            ],
            total_amount=199.99,
            status="delivered",
            created_at=_iso(sixty_days_ago),
            updated_at=_iso(sixty_days_ago + timedelta(days=1)),
        ),
    ]

    logger.info("Generated %d orders for billing_dispute scenario", len(orders))
    return orders, []


def generate_technical_issue_data(
    base_time: datetime,
) -> tuple[list[Order], list[Return]]:
    """Generate order data for the technical_issue scenario.

    Creates order data showing recent product purchases relevant to the tech issue.

    Args:
        base_time: Reference timestamp for generating dates.

    Returns:
        tuple[list[Order], list[Return]]: Orders and returns for the scenario.
    """
    fourteen_days_ago = base_time - timedelta(days=14)

    orders = [
        Order(
            order_id="ORD-2024-0975",
            customer_id="CUST-006",
            items=[
                OrderItem("PROD-E1", "Developer Pro Suite License", 1, 149.99),
                OrderItem("PROD-E2", "API Access Premium Tier", 1, 49.99),
            ],
            total_amount=199.98,
            status="delivered",
            created_at=_iso(fourteen_days_ago),
            updated_at=_iso(fourteen_days_ago + timedelta(days=1)),
            notes="Digital delivery. License keys emailed.",
        ),
    ]

    logger.info("Generated %d orders for technical_issue scenario", len(orders))
    return orders, []


def generate_complex_escalation_data(
    base_time: datetime,
) -> tuple[list[Order], list[Return]]:
    """Generate order data for the complex_escalation scenario.

    Creates multiple orders with issues: wrong item shipped, plus recent purchases.

    Args:
        base_time: Reference timestamp for generating dates.

    Returns:
        tuple[list[Order], list[Return]]: Orders and returns for the scenario.
    """
    five_days_ago = base_time - timedelta(days=5)
    two_days_ago = base_time - timedelta(days=2)
    twenty_days_ago = base_time - timedelta(days=20)

    orders = [
        Order(
            order_id="ORD-2024-1100",
            customer_id="CUST-007",
            items=[
                OrderItem("PROD-F1", "Premium Ergonomic Keyboard", 1, 189.99),
                OrderItem("PROD-F2", "Wireless Mouse Pro", 1, 79.99),
                OrderItem("PROD-F3", "Desk Mat XL", 1, 34.99),
            ],
            total_amount=304.97,
            status="delivered",
            created_at=_iso(five_days_ago),
            updated_at=_iso(two_days_ago),
            shipment=Shipment(
                tracking_number="TRK-8888999900",
                carrier="FedEx",
                status="delivered",
                estimated_delivery=_iso(five_days_ago + timedelta(days=2)),
                current_location="Delivered to front door",
                last_update=_iso(two_days_ago),
            ),
            notes="WRONG ITEM: Customer received Standard Keyboard instead of Premium Ergonomic Keyboard.",
        ),
        Order(
            order_id="ORD-2024-1050",
            customer_id="CUST-007",
            items=[
                OrderItem("PROD-G1", "4K Monitor 32-inch", 1, 599.99),
            ],
            total_amount=599.99,
            status="delivered",
            created_at=_iso(twenty_days_ago),
            updated_at=_iso(twenty_days_ago + timedelta(days=3)),
            shipment=Shipment(
                tracking_number="TRK-7777888899",
                carrier="UPS",
                status="delivered",
                estimated_delivery=_iso(twenty_days_ago + timedelta(days=3)),
                current_location="Delivered to front door",
                last_update=_iso(twenty_days_ago + timedelta(days=3)),
            ),
        ),
    ]

    returns = [
        Return(
            return_id="RET-2024-0095",
            order_id="ORD-2024-1100",
            reason="Wrong item received - got Standard Keyboard instead of Premium Ergonomic",
            status="requested",
            refund_amount=189.99,
            created_at=_iso(base_time),
        ),
    ]

    logger.info(
        "Generated %d orders, %d returns for complex_escalation scenario",
        len(orders),
        len(returns),
    )
    return orders, returns
