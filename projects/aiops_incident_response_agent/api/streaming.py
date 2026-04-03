"""SSE streaming infrastructure for the AI Ops Incident Response Agent API.

Provides AgentHooks that push lifecycle events to an asyncio.Queue,
an SSE event generator, and in-memory run state management.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field

from agents import AgentHooks

from aiops_incident_response_agent.api.schemas.incident import PhaseType, RunStatus
from aiops_incident_response_agent.simulators.scenario_engine import ScenarioType

logger = logging.getLogger(__name__)

AGENT_PHASE_MAP: dict[str, PhaseType] = {
    "Triage Agent": "triage",
    "Log Analyzer": "log_analysis",
    "Log Analyzer Agent": "log_analysis",
    "Metrics Analyzer": "metrics_analysis",
    "Metrics Analyzer Agent": "metrics_analysis",
    "Root Cause Analyzer": "root_cause_analysis",
    "Root Cause Analyzer Agent": "root_cause_analysis",
    "Remediation Agent": "remediation",
    "Incident Reporter": "reporting",
    "Incident Reporter Agent": "reporting",
}


@dataclass
class RunState:
    """In-memory state for a single incident response run.

    Attributes:
        run_id: Unique run identifier.
        scenario_type: The simulated scenario type for this run.
        status: Current run status.
        queue: Async queue for SSE events.
        report: Final incident report text once completed.
        current_phase: The current pipeline phase for SSE clients.
    """

    run_id: str
    scenario_type: ScenarioType
    status: RunStatus = "pending"
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    report: str = ""
    current_phase: PhaseType = "triage"


_runs: dict[str, RunState] = {}


def create_run(scenario_type: ScenarioType) -> RunState:
    """Create a new run state and register it.

    Args:
        scenario_type: The incident scenario to simulate.

    Returns:
        RunState: The newly created run state.
    """
    run_id = uuid.uuid4().hex[:12]
    state = RunState(run_id=run_id, scenario_type=scenario_type)
    _runs[run_id] = state
    logger.info("Created run: run_id=%s, scenario_type=%s", run_id, scenario_type)
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


class StreamingIncidentHooks(AgentHooks):
    """AgentHooks that push lifecycle events to an SSE queue.

    Maps each agent's display name to a coarse pipeline phase for the UI.

    Args:
        state: The RunState to push events to.
    """

    def __init__(self, state: RunState) -> None:
        self._state = state

    async def on_start(self, context, agent) -> None:
        """Push agent_start and optionally phase_change when the phase shifts.

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
        """Push agent_end when an agent finishes.

        Args:
            context: The run context.
            agent: The agent that completed.
            output: The agent's output.
        """
        await self._state.queue.put(
            _sse_line("agent_end", {"agent_name": agent.name})
        )

    async def on_tool_start(self, context, agent, tool) -> None:
        """Push tool_start when a tool is invoked.

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
        """Push tool_end when a tool returns.

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
        """Push handoff when control moves between agents.

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
                    "detail": "%s -> %s" % (source.name, agent.name),
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
    """Yield SSE-formatted strings from a run's queue until done or error.

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
