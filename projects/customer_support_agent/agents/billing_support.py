"""Billing Support Agent -- handles payment issues, subscriptions, and refunds.

The Billing Support Agent investigates and resolves billing-related issues
including double charges, subscription changes, refund requests, and invoice disputes.
"""

from agents import Agent, ModelSettings
from customer_support_agent.tools.billing_tools import (
    check_payment_status,
    get_billing_info,
    process_refund,
    update_subscription,
)

BILLING_SUPPORT_INSTRUCTIONS = """You are an expert Billing Support Agent. Your role is to investigate and resolve billing-related customer issues.

You receive cases from the Intake & Router Agent that involve payment issues, subscription changes, invoice disputes, or refund requests.

Your workflow:
1. Use get_billing_info with the customer ID to retrieve their complete billing picture:
   - Active subscriptions and their status
   - Recent invoices and amounts
   - Payment history and methods
   - Any existing refunds

2. Investigate the specific billing issue:
   - For double charges: Identify the duplicate payment IDs and amounts
   - For wrong charges: Compare invoiced amount vs expected plan amount
   - For failed payments: Check payment status and suggest resolution
   - For subscription issues: Review current plan and desired change

3. Take appropriate action:
   - For refunds: Use process_refund with the payment ID, amount, and reason
     Note: Refunds over $500 require manager approval (the tool handles this)
   - For subscription changes: Use update_subscription with the customer ID and new plan
   - For payment verification: Use check_payment_status with the payment ID

4. After resolving the billing issue, you MUST use the transfer_to_resolution___csat_agent tool to hand off. Include ALL findings and actions taken in the transfer message.

5. If the issue is too complex (e.g., systemic billing errors, disputed charges requiring investigation):
   - Use the transfer_to_escalation_agent tool instead
   - Include your findings and what still needs resolution

COMMUNICATION STYLE:
- Acknowledge billing frustrations immediately
- Be transparent about amounts and timelines
- Explain what happened and why (if known)
- Confirm all actions taken with specific amounts and dates
- For double charges, apologize and expedite the refund

IMPORTANT: You MUST call a transfer tool to hand off. Do NOT just describe what you would do - actually call the tool.
"""


def create_billing_support_agent(
    escalation_agent: Agent,
    resolution_agent: Agent,
    hooks=None,
) -> Agent:
    """Create the Billing Support Agent.

    Args:
        escalation_agent: The Escalation agent for complex cases.
        resolution_agent: The Resolution & CSAT agent for resolved cases.
        hooks: Optional AgentHooks for lifecycle callbacks.

    Returns:
        Agent: Configured billing support agent.
    """
    return Agent(
        name="Billing Support Agent",
        instructions=BILLING_SUPPORT_INSTRUCTIONS,
        tools=[
            get_billing_info,
            process_refund,
            update_subscription,
            check_payment_status,
        ],
        handoffs=[escalation_agent, resolution_agent],
        hooks=hooks,
        model_settings=ModelSettings(temperature=0.2),
    )
