"""Browser automation pipeline API routes.

Exposes endpoints to start automation runs, list scenarios,
stream real-time events via SSE, and fetch completed results.
"""

import asyncio
import logging

from agents import RunConfig, Runner
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from browser_automation_agent.api.schemas.automation import (
    AutomationRequest,
    AutomationResultResponse,
    AutomationRunResponse,
    ScenarioInfo,
)
from browser_automation_agent.api.streaming import (
    StreamingAutomationHooks,
    _sse_line,
    create_run,
    event_generator,
    get_run,
)
from browser_automation_agent.main import (
    SCENARIOS,
    build_agent_pipeline,
    create_openrouter_model,
    create_stagehand_session,
)
from browser_automation_agent.models.task import BrowserContext
from browser_automation_agent.utils.config import load_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/automation", tags=["automation"])


async def _run_pipeline(run_id: str) -> None:
    """Execute the automation pipeline as a background task.

    Args:
        run_id: The run identifier.
    """
    state = get_run(run_id)
    assert state is not None

    state.status = "running"
    hooks = StreamingAutomationHooks(state)

    config = load_config()
    model = create_openrouter_model(config)

    client, session = await create_stagehand_session(config)

    browser_context = BrowserContext(
        task=state.task,
        config=config,
        session=session,
    )

    planner_agent = build_agent_pipeline(model, hooks)

    automation_input = (
        f"BROWSER AUTOMATION TASK\n"
        f"Task: {state.task}\n\n"
        f"Please plan the browser automation, navigate to the target page(s), "
        f"interact with elements as needed, extract the requested data, "
        f"validate the results, and produce a structured report."
    )

    run_config = RunConfig(
        workflow_name="browser_automation",
        tracing_disabled=True,
    )

    try:
        result = await Runner.run(
            starting_agent=planner_agent,
            input=automation_input,
            context=browser_context,
            max_turns=30,
            run_config=run_config,
        )

        state.report = result.final_output
        state.status = "completed"
        state.urls_visited = [
            a.instruction for a in (browser_context.action_log or [])
            if hasattr(a, 'instruction')
        ]

        await state.queue.put(
            _sse_line("report", {"content": state.report})
        )
        await state.queue.put(_sse_line("done", {"run_id": run_id}))

    except Exception as exc:
        logger.exception("Automation pipeline failed: run_id=%s", run_id)
        state.status = "failed"
        await state.queue.put(
            _sse_line("error", {"message": str(exc)})
        )
    finally:
        await session.end()


@router.get("/scenarios", response_model=list[ScenarioInfo])
async def list_scenarios() -> list[ScenarioInfo]:
    """List available predefined automation scenarios.

    Returns:
        list[ScenarioInfo]: Available scenarios.
    """
    return [
        ScenarioInfo(key=k, name=v["name"], task=v["task"])
        for k, v in SCENARIOS.items()
    ]


@router.post("", response_model=AutomationRunResponse)
async def start_automation(request: AutomationRequest) -> AutomationRunResponse:
    """Start a new browser automation run.

    Args:
        request: The automation request.

    Returns:
        AutomationRunResponse: The run_id and initial status.
    """
    task = request.task
    if request.scenario and request.scenario in SCENARIOS:
        task = SCENARIOS[request.scenario]["task"]

    state = create_run(task)
    asyncio.create_task(_run_pipeline(state.run_id))
    return AutomationRunResponse(run_id=state.run_id, status="pending")


@router.get("/{run_id}/stream")
async def stream_automation(run_id: str) -> EventSourceResponse:
    """Stream real-time SSE events for an automation run.

    Args:
        run_id: The run identifier.

    Returns:
        EventSourceResponse: SSE stream.

    Raises:
        HTTPException: 404 if run_id is not found.
    """
    state = get_run(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return EventSourceResponse(event_generator(state))


@router.get("/{run_id}", response_model=AutomationResultResponse)
async def get_automation_result(run_id: str) -> AutomationResultResponse:
    """Fetch the result of a completed automation run.

    Args:
        run_id: The run identifier.

    Returns:
        AutomationResultResponse: The run result.

    Raises:
        HTTPException: 404 if run_id is not found.
    """
    state = get_run(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Run not found")

    return AutomationResultResponse(
        run_id=state.run_id,
        status=state.status,
        task=state.task,
        report=state.report,
        urls_visited=state.urls_visited,
        steps_completed=state.steps_completed,
        total_steps=state.total_steps,
    )
