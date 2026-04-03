"""Incident response pipeline API routes.

Exposes endpoints to list scenarios, start incident runs, stream SSE events,
and fetch completed results.
"""

import asyncio
import logging

from agents import RunConfig, Runner
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from aiops_incident_response_agent.api.schemas.incident import (
    IncidentRequest,
    IncidentResultResponse,
    IncidentRunResponse,
    ScenarioInfo,
)
from aiops_incident_response_agent.api.streaming import (
    StreamingIncidentHooks,
    _sse_line,
    create_run,
    event_generator,
    get_run,
)
from aiops_incident_response_agent.main import build_agent_pipeline, create_openrouter_model
from aiops_incident_response_agent.simulators.scenario_engine import (
    ScenarioData,
    generate_scenario,
    list_scenarios,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/incident", tags=["incident"])


def _build_incident_input(scenario_data: ScenarioData) -> str:
    """Compose the initial user message passed to the triage agent.

    Args:
        scenario_data: Correlated scenario payload from generate_scenario.

    Returns:
        str: Formatted incident alert text for Runner.run input.
    """
    alert_summary = "\n".join(
        f"- [{a.severity.upper()}] {a.service}: {a.message}"
        for a in scenario_data.alerts
    )
    return (
        "INCIDENT ALERT\n"
        "Scenario: %s\n\n"
        "Active Alerts:\n%s\n\n"
        "Please triage this incident, analyze the root cause, "
        "propose remediation, and generate a complete incident report."
    ) % (scenario_data.description, alert_summary)


async def _run_pipeline(run_id: str) -> None:
    """Execute the incident pipeline as a background task.

    Calls generate_scenario, build_agent_pipeline, and Runner.run, then
    enqueues report, phase_change completed, and done SSE events.

    Args:
        run_id: The run identifier.
    """
    state = get_run(run_id)
    assert state is not None

    state.status = "running"
    hooks = StreamingIncidentHooks(state)
    model = create_openrouter_model()
    scenario_data = generate_scenario(state.scenario_type)
    triage_agent = build_agent_pipeline(model, hooks)

    incident_input = _build_incident_input(scenario_data)

    run_config = RunConfig(
        workflow_name="aiops_incident_response",
        tracing_disabled=True,
    )

    result = await Runner.run(
        starting_agent=triage_agent,
        input=incident_input,
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

    logger.info("Incident pipeline completed: run_id=%s", run_id)


@router.get("/scenarios", response_model=list[ScenarioInfo])
async def list_incident_scenarios() -> list[ScenarioInfo]:
    """List available incident scenarios.

    Returns:
        list[ScenarioInfo]: Scenario type and description for each option.
    """
    return [
        ScenarioInfo(scenario_type=st, description=desc)
        for st, desc in list_scenarios()
    ]


@router.post("", response_model=IncidentRunResponse)
async def start_incident_run(request: IncidentRequest) -> IncidentRunResponse:
    """Start a new incident response run for the given scenario type.

    Args:
        request: Body with scenario_type.

    Returns:
        IncidentRunResponse: run_id and initial pending status.
    """
    state = create_run(request.scenario_type)
    asyncio.create_task(_run_pipeline(state.run_id))
    return IncidentRunResponse(run_id=state.run_id, status="pending")


@router.get("/{run_id}/stream")
async def stream_incident(run_id: str) -> EventSourceResponse:
    """Stream SSE events for an incident run until done or error.

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


@router.get("/{run_id}", response_model=IncidentResultResponse)
async def get_incident_result(run_id: str) -> IncidentResultResponse:
    """Fetch the current result snapshot for an incident run.

    Args:
        run_id: The run identifier.

    Returns:
        IncidentResultResponse: Status, scenario, and report text.

    Raises:
        HTTPException: 404 if the run does not exist.
    """
    state = get_run(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Run not found")

    return IncidentResultResponse(
        run_id=state.run_id,
        status=state.status,
        scenario_type=state.scenario_type,
        report=state.report,
    )
