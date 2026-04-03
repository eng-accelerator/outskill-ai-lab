"""Customer support pipeline API routes.

Exposes endpoints to list scenarios, start support runs, stream SSE events,
and fetch completed results.
"""

import asyncio
import logging

from agents import RunConfig, Runner
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from customer_support_agent.api.schemas.support import (
    ScenarioInfo,
    SupportRequest,
    SupportResultResponse,
    SupportRunResponse,
)
from customer_support_agent.api.streaming import (
    StreamingSupportHooks,
    _sse_line,
    create_run,
    event_generator,
    get_run,
)
from customer_support_agent.main import build_agent_pipeline, create_openrouter_model
from customer_support_agent.simulators.scenario_engine import (
    ScenarioData,
    generate_scenario,
    list_scenarios as list_engine_scenarios,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/support", tags=["support"])


def _build_support_input(scenario_data: ScenarioData) -> str:
    """Compose the initial user message passed to the intake agent.

    Args:
        scenario_data: Correlated scenario payload from generate_scenario.

    Returns:
        str: Formatted support request text for Runner.run input.
    """
    ticket_info = ""
    if scenario_data.ticket:
        ticket_info = (
            "\nSupport Ticket: %s\n"
            "Category: %s\n"
            "Priority: %s\n"
            "Subject: %s\n"
        ) % (
            scenario_data.ticket.ticket_id,
            scenario_data.ticket.category,
            scenario_data.ticket.priority,
            scenario_data.ticket.subject,
        )

    return (
        "CUSTOMER SUPPORT REQUEST\n"
        "Customer ID: %s\n"
        "Customer: %s (%s tier)\n"
        "%s\n"
        "Customer Message:\n%s\n\n"
        "Please help this customer by investigating their issue, taking appropriate actions, "
        "and providing a complete resolution."
    ) % (
        scenario_data.customer.customer_id,
        scenario_data.customer.name,
        scenario_data.customer.tier,
        ticket_info,
        scenario_data.customer_query,
    )


async def _run_pipeline(run_id: str) -> None:
    """Execute the support pipeline as a background task.

    Calls generate_scenario, build_agent_pipeline, and Runner.run, then
    enqueues report, phase_change completed, and done SSE events.

    Args:
        run_id: The run identifier.
    """
    state = get_run(run_id)
    assert state is not None

    state.status = "running"
    hooks = StreamingSupportHooks(state)
    model = create_openrouter_model()
    scenario_data = generate_scenario(state.scenario_type)
    intake_agent = build_agent_pipeline(model, hooks)

    support_input = _build_support_input(scenario_data)

    run_config = RunConfig(
        workflow_name="customer_support",
        tracing_disabled=True,
    )

    result = await Runner.run(
        starting_agent=intake_agent,
        input=support_input,
        context=scenario_data,
        max_turns=40,
        run_config=run_config,
    )

    state.report = result.final_output
    state.status = "completed"
    state.current_phase = "completed"

    await state.queue.put(_sse_line("phase_change", {"phase": "completed"}))
    await state.queue.put(_sse_line("report", {"content": state.report}))
    await state.queue.put(_sse_line("done", {"run_id": run_id}))

    logger.info("Support pipeline completed: run_id=%s", run_id)


@router.get("/scenarios", response_model=list[ScenarioInfo])
async def list_support_scenarios() -> list[ScenarioInfo]:
    """List available customer support scenarios.

    Returns:
        list[ScenarioInfo]: Scenario type and description for each option.
    """
    return [
        ScenarioInfo(scenario_type=st, description=desc)
        for st, desc in list_engine_scenarios()
    ]


@router.post("", response_model=SupportRunResponse)
async def start_support_run(request: SupportRequest) -> SupportRunResponse:
    """Start a new customer support run for the given scenario type.

    Args:
        request: Body with scenario_type.

    Returns:
        SupportRunResponse: run_id and initial pending status.
    """
    state = create_run(request.scenario_type)
    asyncio.create_task(_run_pipeline(state.run_id))
    return SupportRunResponse(run_id=state.run_id, status="pending")


@router.get("/{run_id}/stream")
async def stream_support(run_id: str) -> EventSourceResponse:
    """Stream SSE events for a support run until done or error.

    Args:
        run_id: The run identifier.

    Returns:
        EventSourceResponse: SSE stream of pipeline events.

    Raises:
        HTTPException: 404 if the run does not exist.
    """
    state = get_run(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return EventSourceResponse(event_generator(state))


@router.get("/{run_id}", response_model=SupportResultResponse)
async def get_support_result(run_id: str) -> SupportResultResponse:
    """Fetch the current result snapshot for a support run.

    Args:
        run_id: The run identifier.

    Returns:
        SupportResultResponse: Status, scenario, and report text.

    Raises:
        HTTPException: 404 if the run does not exist.
    """
    state = get_run(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Run not found")

    return SupportResultResponse(
        run_id=state.run_id,
        status=state.status,
        scenario_type=state.scenario_type,
        report=state.report,
    )
