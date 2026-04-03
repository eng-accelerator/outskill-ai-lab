"""Research pipeline API routes.

Exposes endpoints to start research runs, stream real-time events
via SSE, and fetch completed results.
"""

import asyncio
import logging

from agents import RunConfig, Runner
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from deep_research_agent.api.schemas.research import (
    ResearchRequest,
    ResearchResultResponse,
    ResearchRunResponse,
    SourcePayload,
)
from deep_research_agent.api.streaming import (
    StreamingResearchHooks,
    _sse_line,
    create_run,
    event_generator,
    get_run,
)
from deep_research_agent.main import build_agent_pipeline, create_openrouter_model
from deep_research_agent.models.research import ResearchContext
from deep_research_agent.utils.config import load_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/research", tags=["research"])


async def _run_pipeline(run_id: str) -> None:
    """Execute the research pipeline as a background task.

    Builds the agent pipeline with streaming hooks, runs it,
    and pushes a final 'done' or 'error' event to the SSE queue.

    Args:
        run_id: The run identifier.
    """
    state = get_run(run_id)
    assert state is not None

    state.status = "running"
    hooks = StreamingResearchHooks(state)

    config = load_config()
    model = create_openrouter_model()
    planner_agent = build_agent_pipeline(model, hooks)

    research_context = ResearchContext(query=state.query, config=config)

    research_input = (
        f"DEEP RESEARCH REQUEST\n"
        f"Query: {state.query}\n\n"
        f"Please conduct comprehensive research on this topic. "
        f"Decompose the query into sub-questions, search multiple sources, "
        f"extract relevant content, cross-reference findings, and produce "
        f"a detailed research report with citations and confidence assessment."
    )

    run_config = RunConfig(
        workflow_name="deep_research",
        tracing_disabled=True,
    )

    try:
        result = await Runner.run(
            starting_agent=planner_agent,
            input=research_input,
            context=research_context,
            max_turns=50,
            run_config=run_config,
        )
        state.report = result.final_output
        state.status = "completed"

        sources = [
            SourcePayload(
                url=f.source_url,
                title=f.title,
                source_type=f.finding_type,
                snippet=f.content_snippet[:300],
                relevance_score=f.relevance_score,
            )
            for f in research_context.findings
        ]
        state.sources = sources

        await state.queue.put(
            _sse_line(
                "report",
                {"content": state.report, "sources": [s.model_dump() for s in sources]},
            )
        )
        await state.queue.put(_sse_line("done", {"run_id": run_id}))

    except Exception as exc:
        logger.exception("Research pipeline failed: run_id=%s", run_id)
        state.status = "failed"
        await state.queue.put(
            _sse_line("error", {"message": str(exc)})
        )


@router.post("", response_model=ResearchRunResponse)
async def start_research(request: ResearchRequest) -> ResearchRunResponse:
    """Start a new deep research run.

    Creates a run state, spawns the pipeline as a background task,
    and immediately returns the run_id so the client can connect
    to the SSE stream.

    Args:
        request: The research request containing the query.

    Returns:
        ResearchRunResponse: The run_id and initial status.
    """
    state = create_run(request.query)
    asyncio.create_task(_run_pipeline(state.run_id))
    return ResearchRunResponse(run_id=state.run_id, status="pending")


@router.get("/{run_id}/stream")
async def stream_research(run_id: str) -> EventSourceResponse:
    """Stream real-time SSE events for a research run.

    Connects to the run's event queue and yields events until
    the pipeline completes or errors.

    Args:
        run_id: The run identifier.

    Returns:
        EventSourceResponse: SSE stream of pipeline events.

    Raises:
        HTTPException: 404 if run_id is not found.
    """
    state = get_run(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Run not found")

    return EventSourceResponse(event_generator(state))


@router.get("/{run_id}", response_model=ResearchResultResponse)
async def get_research_result(run_id: str) -> ResearchResultResponse:
    """Fetch the result of a completed research run.

    Args:
        run_id: The run identifier.

    Returns:
        ResearchResultResponse: The run status, report, and sources.

    Raises:
        HTTPException: 404 if run_id is not found.
    """
    state = get_run(run_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Run not found")

    return ResearchResultResponse(
        run_id=state.run_id,
        status=state.status,
        query=state.query,
        report=state.report,
        sources=state.sources,
    )
