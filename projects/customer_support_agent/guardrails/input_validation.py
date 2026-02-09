"""Input guardrail for validating customer support queries.

Ensures the support query contains valid, actionable customer information
before the agent pipeline processes it.
"""

import logging

from agents import Agent, GuardrailFunctionOutput, InputGuardrail, RunContextWrapper

from customer_support_agent.simulators.scenario_engine import ScenarioData

logger = logging.getLogger(__name__)


async def validate_support_input(
    ctx: RunContextWrapper[ScenarioData],
    agent: Agent,
    input_data: str | list,
) -> GuardrailFunctionOutput:
    """Validate that the support query has actionable customer context.

    Checks that the scenario data has been loaded and contains
    a valid customer profile and at least a customer query.

    Args:
        ctx: Run context containing the scenario data.
        agent: The agent being guarded.
        input_data: The input string or message list.

    Returns:
        GuardrailFunctionOutput: Validation result with tripwire status.
    """
    scenario = ctx.context

    # Check for customer profile
    if scenario.customer is None:
        logger.warning("Input validation failed: no customer profile")
        return GuardrailFunctionOutput(
            output_info="No customer profile available. Cannot proceed with support.",
            tripwire_triggered=True,
        )

    # Check for customer query
    if not scenario.customer_query or len(scenario.customer_query.strip()) < 10:
        logger.warning("Input validation failed: customer query too short or empty")
        return GuardrailFunctionOutput(
            output_info="Customer query is empty or too short. Need a substantive query to proceed.",
            tripwire_triggered=True,
        )

    # Check for at least some contextual data
    has_orders = len(scenario.orders) > 0
    has_billing = len(scenario.subscriptions) > 0 or len(scenario.invoices) > 0
    has_kb = len(scenario.knowledge_base) > 0

    if not has_orders and not has_billing and not has_kb:
        logger.warning("Input validation failed: no contextual data available")
        return GuardrailFunctionOutput(
            output_info="No order, billing, or knowledge base data available. Cannot provide meaningful support.",
            tripwire_triggered=True,
        )

    logger.info(
        "Input validation passed: customer=%s, query_len=%d, orders=%d, billing=%d, kb=%d",
        scenario.customer.customer_id,
        len(scenario.customer_query),
        len(scenario.orders),
        len(scenario.subscriptions) + len(scenario.invoices),
        len(scenario.knowledge_base),
    )
    return GuardrailFunctionOutput(
        output_info="Customer support query validated successfully.",
        tripwire_triggered=False,
    )


support_input_guardrail = InputGuardrail(
    guardrail_function=validate_support_input,
    name="support_input_validation",
)
