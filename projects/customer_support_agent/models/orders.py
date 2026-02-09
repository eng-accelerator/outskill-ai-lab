"""Order, shipment, and return data models.

Defines order-related types for tracking purchases, shipments,
and return/refund workflows in the support agent system.
"""

from dataclasses import dataclass, field
from typing import Literal

# Order lifecycle statuses
OrderStatus = Literal[
    "pending",
    "confirmed",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
    "returned",
]

# Shipment tracking statuses
ShipmentStatus = Literal[
    "label_created",
    "picked_up",
    "in_transit",
    "out_for_delivery",
    "delivered",
    "exception",
    "returned_to_sender",
]

# Return request statuses
ReturnStatus = Literal[
    "requested",
    "approved",
    "item_received",
    "refund_processing",
    "completed",
    "rejected",
]


@dataclass(frozen=True)
class OrderItem:
    """A single item in an order.

    Attributes:
        product_id: Unique product identifier.
        product_name: Human-readable product name.
        quantity: Number of units ordered.
        unit_price: Price per unit in dollars.
    """

    product_id: str
    product_name: str
    quantity: int
    unit_price: float


@dataclass(frozen=True)
class Shipment:
    """Shipment tracking information for an order.

    Attributes:
        tracking_number: Carrier tracking number.
        carrier: Shipping carrier name.
        status: Current shipment status.
        estimated_delivery: Estimated delivery date (ISO 8601).
        current_location: Last known location of the package.
        last_update: Timestamp of the last tracking update (ISO 8601).
    """

    tracking_number: str
    carrier: str
    status: ShipmentStatus
    estimated_delivery: str
    current_location: str
    last_update: str


@dataclass(frozen=True)
class Order:
    """A customer order with items and shipment details.

    Attributes:
        order_id: Unique order identifier.
        customer_id: Customer who placed the order.
        items: List of items in the order.
        total_amount: Total order amount in dollars.
        status: Current order status.
        created_at: Order creation timestamp (ISO 8601).
        updated_at: Last update timestamp (ISO 8601).
        shipment: Shipment tracking info (None if not yet shipped).
        notes: Internal notes about the order.
    """

    order_id: str
    customer_id: str
    items: list[OrderItem]
    total_amount: float
    status: OrderStatus
    created_at: str
    updated_at: str
    shipment: Shipment | None = None
    notes: str = ""


@dataclass(frozen=True)
class Return:
    """A return request for an order.

    Attributes:
        return_id: Unique return identifier.
        order_id: The order being returned.
        reason: Customer-provided reason for the return.
        status: Current return status.
        refund_amount: Amount to be refunded in dollars.
        created_at: Return request timestamp (ISO 8601).
    """

    return_id: str
    order_id: str
    reason: str
    status: ReturnStatus
    refund_amount: float
    created_at: str
