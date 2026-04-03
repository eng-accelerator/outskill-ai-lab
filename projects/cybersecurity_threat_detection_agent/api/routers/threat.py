"""Threat detection pipeline API routes.

Exposes endpoints to list scenarios, start runs, stream SSE events,
and fetch completed SOC reports.
"""

import asyncio
import logging

from agents import RunConfig, Runner
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from cybersecurity_threat_detection_agent.api.schemas.threat import (
    ScenarioInfo,
    ThreatRequest,
    ThreatResultResponse,
    ThreatRunResponse,
)
from cybersecurity_threat_detection_agent.api.streaming import (
    StreamingThreatHooks,
    _sse_line,
    create_run,
    event_generator,
    get_run,
)
from cybersecurity_threat_detection_agent.main import build_agent_pipeline, create_openrouter_model
from cybersecurity_threat_detection_agent.simulators.scenario_engine import (
    ScenarioData,
    generate_scenario,
    list_scenarios as list_engine_scenarios,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/threat", tags=["threat"])


def _build_threat_input(scenario_data: ScenarioData) -> str:
    """Compose the initial user message passed to the alert intake agent.

    Args:
        scenario_data: Correlated scenario payload from generate_scenario.

    Returns:
        str: Formatted threat briefing text for Runner.run input.
    """
    alert_summary = "\n".join(
        "- [%s] [%s] %s: %s"
        % (a.severity.upper(), a.source, a.category, a.message)
        for a in scenario_data.alerts
    )
    return (
        "SECURITY THREAT DETECTED\n"
        "Scenario: %s\n\n"
        "Active Security Alerts:\n%s\n\n"
        "Please analyze this threat, enrich with threat intelligence, "
        "propose containment actions, and generate a complete SOC incident report."
    ) % (scenario_data.description, alert_summary)


async def _run_pipeline(run_id: str) -> None:
    """Execute the threat pipeline as a background task.

    Calls generate_scenario, build_agent_pipeline, and Runner.run, then
    enqueues report, phase_change completed, and done SSE events.

    Args:
        run_id: The run identifier.
    """
    state = get_run(run_id)
    assert state is not None

    state.status = "running"
    hooks = StreamingThreatHooks(state)
    model = create_openrouter_model()
    scenario_data = generate_scenario(state.scenario_type)
    intake_agent = build_agent_pipeline(model, hooks)

    threat_input = _build_threat_input(scenario_data)

    run_config = RunConfig(
        workflow_name="cybersecurity_threat_detection",
        tracing_disabled=True,
    )

    result = await Runner.run(
        starting_agent=intake_agent,
        input=threat_input,
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

    logger.info("Threat pipeline completed: run_id=%s", run_id)


@router.get("/scenarios", response_model=list[ScenarioInfo])
async def list_threat_scenarios() -> list[ScenarioInfo]:
    """List available cybersecurity threat scenarios.

    Returns:
        list[ScenarioInfo]: Scenario type and description for each option.
    """
    return [
        ScenarioInfo(scenario_type=st, description=desc)
        for st, desc in list_engine_scenarios()
    ]


@router.post("", response_model=ThreatRunResponse)
async def start_threat_run(request: ThreatRequest) -> ThreatRunResponse:
    """Start a new threat detection run for the given scenario type.

    Args:
        request: Body with scenario_type.

    Returns:
        ThreatRunResponse: run_id and initial pending status.
    """
    state = create_run(request.scenario_type)
    asyncio.create_task(_run_pipeline(state.run_id))
    return ThreatRunResponse(run_id=state.run_id, status="pending")


@router.get("/{run_id}/stream")
async def stream_threat(run_id: str) -> EventSourceResponse:
    """Stream SSE events for a threat run until done or error.

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


@router.get("/{run_id}", response_model=ThreatResultResponse)
async def get_threat_result(run_id: str) -> ThreatResultResponse:
    """Fetch the current result snapshot for a threat run.

    Args:
        run_id: The run identifier.

    Returns:
        ThreatResultResponse: Status, scenario, and report text.

    Raises:
        HTTPException: 404 if the run does not exist.
    """
    state = get_run(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Run not found")

    return ThreatResultResponse(
        run_id=state.run_id,
        status=state.status,
        scenario_type=state.scenario_type,
        report=state.report,
    )
