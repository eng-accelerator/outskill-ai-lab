"""Tools for order lookup, shipment tracking, returns, and modifications.

These tools are used by the Order Support Agent to investigate
and resolve order-related customer issues.
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone

from agents import RunContextWrapper, function_tool
from customer_support_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


@function_tool
def lookup_order(ctx: RunContextWrapper[ScenarioData], order_id: str) -> str:
    """Look up full order details including items, status, and shipment info.

    Retrieves the complete order record from the order management system.
    Use this to check order status, items ordered, and delivery information.

    Args:
        ctx: Run context containing the scenario data.
        order_id: The order ID to look up (e.g., 'ORD-2024-1001').

    Returns:
        str: JSON string of the order details, or error message if not found.
    """
    scenario = ctx.context
    logger.info("Looking up order: %s", order_id)

    for order in scenario.orders:
        if order.order_id == order_id:
            order_data = asdict(order)
            logger.info("Found order %s with status: %s", order_id, order.status)
            return json.dumps(order_data, indent=2)

    logger.warning("Order not found: %s", order_id)
    return json.dumps({"error": f"Order {order_id} not found in the system"})


@function_tool
def track_shipment(ctx: RunContextWrapper[ScenarioData], tracking_number: str) -> str:
    """Track a shipment using the carrier tracking number.

    Queries the shipping carrier for real-time tracking information
    including current location, status, and estimated delivery.

    Args:
        ctx: Run context containing the scenario data.
        tracking_number: The carrier tracking number (e.g., 'TRK-9876543210').

    Returns:
        str: JSON string of shipment tracking details, or error if not found.
    """
    scenario = ctx.context
    logger.info("Tracking shipment: %s", tracking_number)

    for order in scenario.orders:
        if order.shipment and order.shipment.tracking_number == tracking_number:
            shipment_data = asdict(order.shipment)
            shipment_data["order_id"] = order.order_id

            # Add delay analysis
            if order.shipment.status == "in_transit":
                last_update = order.shipment.last_update
                now = datetime.now(timezone.utc).isoformat()
                shipment_data["delay_analysis"] = {
                    "last_update": last_update,
                    "current_time": now,
                    "note": "Package may be experiencing carrier delays. Contact carrier for investigation.",
                }

            logger.info(
                "Found shipment %s with status: %s",
                tracking_number,
                order.shipment.status,
            )
            return json.dumps(shipment_data, indent=2)

    logger.warning("Shipment not found: %s", tracking_number)
    return json.dumps({"error": f"Tracking number {tracking_number} not found"})


@function_tool
def process_return(
    ctx: RunContextWrapper[ScenarioData], order_id: str, reason: str
) -> str:
    """Initiate a return for an order and generate an RMA number.

    Creates a return request in the system. The customer will receive
    a prepaid return label and RMA number for shipping the item back.

    Args:
        ctx: Run context containing the scenario data.
        order_id: The order ID to return (e.g., 'ORD-2024-1042').
        reason: Customer-provided reason for the return.

    Returns:
        str: JSON string with return confirmation details, or error if order not found.
    """
    scenario = ctx.context
    logger.info("Processing return for order: %s, reason: %s", order_id, reason)

    # Find the order
    target_order = None
    for order in scenario.orders:
        if order.order_id == order_id:
            target_order = order
            break

    if target_order is None:
        return json.dumps({"error": f"Order {order_id} not found"})

    if target_order.status not in ("delivered", "shipped"):
        return json.dumps(
            {
                "error": f"Order {order_id} cannot be returned. Current status: {target_order.status}",
            }
        )

    # Check for existing return
    for ret in scenario.returns:
        if ret.order_id == order_id:
            return json.dumps(
                {
                    "return_id": ret.return_id,
                    "status": "already_requested",
                    "message": f"Return already initiated: {ret.return_id}",
                    "return_details": asdict(ret),
                }
            )

    # Create new return
    rma_number = f"RMA-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{order_id[-4:]}"
    result = {
        "return_id": f"RET-NEW-{order_id[-4:]}",
        "order_id": order_id,
        "rma_number": rma_number,
        "status": "approved",
        "refund_amount": target_order.total_amount,
        "return_label": f"https://returns.ourservice.com/label/{rma_number}",
        "instructions": (
            "1. Print the prepaid return label from the link above. "
            "2. Pack the item securely in its original packaging. "
            "3. Attach the label and drop off at any FedEx location. "
            "4. Refund will be processed within 5-7 business days after we receive the item."
        ),
        "reason": reason,
    }

    logger.info("Return approved for order %s, RMA: %s", order_id, rma_number)
    return json.dumps(result, indent=2)


@function_tool
def modify_order(
    ctx: RunContextWrapper[ScenarioData], order_id: str, action: str
) -> str:
    """Modify an existing order (cancel or update).

    Performs the requested modification on the order. Cancellation is only
    possible for orders that haven't shipped yet.

    Args:
        ctx: Run context containing the scenario data.
        order_id: The order ID to modify (e.g., 'ORD-2024-1001').
        action: The modification action ('cancel', 'expedite_shipping', 'update_address').

    Returns:
        str: JSON string with modification result.
    """
    scenario = ctx.context
    logger.info("Modifying order %s with action: %s", order_id, action)

    target_order = None
    for order in scenario.orders:
        if order.order_id == order_id:
            target_order = order
            break

    if target_order is None:
        return json.dumps({"error": f"Order {order_id} not found"})

    match action:
        case "cancel":
            if target_order.status in ("pending", "confirmed", "processing"):
                return json.dumps(
                    {
                        "order_id": order_id,
                        "action": "cancel",
                        "status": "cancelled",
                        "message": f"Order {order_id} has been cancelled. Refund of ${target_order.total_amount:.2f} will be processed within 3-5 business days.",
                    }
                )
            return json.dumps(
                {
                    "order_id": order_id,
                    "action": "cancel",
                    "status": "failed",
                    "message": f"Cannot cancel order {order_id}. Current status: {target_order.status}. Please initiate a return instead.",
                }
            )

        case "expedite_shipping":
            if target_order.status in ("shipped", "processing"):
                return json.dumps(
                    {
                        "order_id": order_id,
                        "action": "expedite_shipping",
                        "status": "requested",
                        "message": "Shipping expedite request submitted to carrier. Updated delivery estimate will be available within 24 hours.",
                    }
                )
            return json.dumps(
                {
                    "order_id": order_id,
                    "action": "expedite_shipping",
                    "status": "not_applicable",
                    "message": f"Cannot expedite. Order status: {target_order.status}.",
                }
            )

        case "update_address":
            if target_order.status in ("pending", "confirmed"):
                return json.dumps(
                    {
                        "order_id": order_id,
                        "action": "update_address",
                        "status": "ready",
                        "message": "Please provide the new shipping address to complete the update.",
                    }
                )
            return json.dumps(
                {
                    "order_id": order_id,
                    "action": "update_address",
                    "status": "failed",
                    "message": f"Cannot update address. Order already in status: {target_order.status}.",
                }
            )

        case _:
            return json.dumps(
                {
                    "error": f"Unknown action: {action}. Supported actions: cancel, expedite_shipping, update_address",
                }
            )
