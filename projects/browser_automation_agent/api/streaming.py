"""SSE streaming infrastructure for the Browser Automation Agent API.

Provides custom AgentHooks that push lifecycle events to an asyncio.Queue,
an SSE event generator, and in-memory run state management.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field

from agents import AgentHooks

from browser_automation_agent.api.schemas.automation import PhaseType, RunStatus

logger = logging.getLogger(__name__)

AGENT_PHASE_MAP: dict[str, PhaseType] = {
    "Task Planner": "planning",
    "Navigator": "navigating",
    "Interactor": "interacting",
    "Extractor": "extracting",
    "Validator": "validating",
    "Reporter": "reporting",
}


@dataclass
class RunState:
    """In-memory state for a single automation run.

    Attributes:
        run_id: Unique run identifier.
        task: The automation task description.
        status: Current run status.
        queue: Async queue for SSE events.
        report: Final report content.
        urls_visited: URLs navigated during the run.
        steps_completed: Number of completed steps.
        total_steps: Total planned steps.
        current_phase: The current pipeline phase.
    """

    run_id: str
    task: str
    status: RunStatus = "pending"
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    report: str = ""
    urls_visited: list[str] = field(default_factory=list)
    steps_completed: int = 0
    total_steps: int = 0
    current_phase: PhaseType = "planning"


_runs: dict[str, RunState] = {}


def create_run(task: str) -> RunState:
    """Create a new run state and register it.

    Args:
        task: The automation task.

    Returns:
        RunState: The newly created run state.
    """
    run_id = uuid.uuid4().hex[:12]
    state = RunState(run_id=run_id, task=task)
    _runs[run_id] = state
    logger.info("Created run: run_id=%s, task=%s", run_id, task[:80])
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


class StreamingAutomationHooks(AgentHooks):
    """AgentHooks that push lifecycle events to an SSE queue.

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
        """Push tool_end event.

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


async def event_generator(state: RunState):
    """Async generator that yields SSE-formatted strings from a run's queue.

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
