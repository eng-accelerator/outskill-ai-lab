"""SSE streaming infrastructure for the Deep Research Agent API.

Provides custom AgentHooks that push lifecycle events to an asyncio.Queue,
an SSE event generator, and in-memory run state management.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field

from agents import AgentHooks

from deep_research_agent.api.schemas.research import (
    PhaseType,
    RunStatus,
    SourcePayload,
)

logger = logging.getLogger(__name__)

AGENT_PHASE_MAP: dict[str, PhaseType] = {
    "Research Planner": "planning",
    "Web Researcher": "searching",
    "Academic Researcher": "searching",
    "News Researcher": "searching",
    "Content Extractor": "reading",
    "Synthesizer": "synthesizing",
    "Report Writer": "writing",
}


@dataclass
class RunState:
    """In-memory state for a single research run.

    Attributes:
        run_id: Unique run identifier.
        query: The original research query.
        status: Current run status.
        queue: Async queue for SSE events.
        report: Final report content once completed.
        sources: Accumulated sources discovered during the run.
        current_phase: The current pipeline phase.
    """

    run_id: str
    query: str
    status: RunStatus = "pending"
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    report: str = ""
    sources: list[SourcePayload] = field(default_factory=list)
    current_phase: PhaseType = "planning"


_runs: dict[str, RunState] = {}


def create_run(query: str) -> RunState:
    """Create a new run state and register it.

    Args:
        query: The research query.

    Returns:
        RunState: The newly created run state.
    """
    run_id = uuid.uuid4().hex[:12]
    state = RunState(run_id=run_id, query=query)
    _runs[run_id] = state
    logger.info("Created run: run_id=%s, query=%s", run_id, query[:80])
    return state


def get_run(run_id: str) -> RunState | None:
    """Look up a run by ID.

    Args:
        run_id: The run identifier.

    Returns:
        RunState | None: The run state, or None if not found.
    """
    return _runs.get(run_id)


def _sse_line(event: str, data: dict) -> str:
    """Format a single SSE message.

    Args:
        event: The event type name.
        data: The JSON-serializable payload.

    Returns:
        str: SSE-formatted string.
    """
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


class StreamingResearchHooks(AgentHooks):
    """AgentHooks that push lifecycle events to an SSE queue.

    Replaces the CLI-based DeepResearchHooks. Each hook method
    serializes an event and puts it on the run's asyncio.Queue
    for the SSE endpoint to consume.

    Args:
        state: The RunState to push events to.
    """

    def __init__(self, state: RunState) -> None:
        self._state = state

    async def on_start(self, context, agent) -> None:
        """Push agent_start event and update phase.

        Args:
            context: The run context.
            agent: The agent that is starting.
        """
        phase = AGENT_PHASE_MAP.get(agent.name, self._state.current_phase)
        if phase != self._state.current_phase:
            self._state.current_phase = phase
            await self._state.queue.put(
                _sse_line("phase_change", {"phase": phase})
            )

        await self._state.queue.put(
            _sse_line("agent_start", {"agent_name": agent.name})
        )
        logger.info("[%s] agent started: %s", self._state.run_id, agent.name)

    async def on_end(self, context, agent, output) -> None:
        """Push agent_end event.

        Args:
            context: The run context.
            agent: The agent that completed.
            output: The agent's output.
        """
        await self._state.queue.put(
            _sse_line("agent_end", {"agent_name": agent.name})
        )

    async def on_tool_start(self, context, agent, tool) -> None:
        """Push tool_start event.

        Args:
            context: The run context.
            agent: The agent invoking the tool.
            tool: The tool being invoked.
        """
        await self._state.queue.put(
            _sse_line(
                "tool_start",
                {"agent_name": agent.name, "detail": tool.name},
            )
        )

    async def on_tool_end(self, context, agent, tool, result) -> None:
        """Push tool_end event and extract source data from tool results.

        Args:
            context: The run context.
            agent: The agent that invoked the tool.
            tool: The tool that completed.
            result: The tool's result.
        """
        await self._state.queue.put(
            _sse_line(
                "tool_end",
                {"agent_name": agent.name, "detail": tool.name},
            )
        )

    async def on_handoff(self, context, agent, source) -> None:
        """Push handoff event.

        Args:
            context: The run context.
            agent: The target agent receiving the handoff.
            source: The source agent performing the handoff.
        """
        await self._state.queue.put(
            _sse_line(
                "handoff",
                {
                    "agent_name": agent.name,
                    "detail": f"{source.name} -> {agent.name}",
                },
            )
        )
        logger.info(
            "[%s] handoff: %s -> %s",
            self._state.run_id,
            source.name,
            agent.name,
        )


async def event_generator(state: RunState):
    """Async generator that yields SSE-formatted strings from a run's queue.

    Blocks on queue.get() until an event is available. Terminates when
    it receives a 'done' or 'error' event.

    Args:
        state: The RunState whose queue to consume.

    Yields:
        str: SSE-formatted event strings.
    """
    while True:
        msg: str = await state.queue.get()
        yield msg
        if '"done"' in msg or '"error"' in msg:
            break
