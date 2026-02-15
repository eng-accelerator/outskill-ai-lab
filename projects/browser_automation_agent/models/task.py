"""Data models for task planning and browser context.

Defines the structured types for automation task plans, individual
steps, and the shared browser context passed through the pipeline.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

ScenarioType = Literal["scraping", "form_automation"]

ActionType = Literal[
    "navigate",
    "observe",
    "click",
    "type",
    "submit",
    "extract",
    "wait",
    "scroll",
]


@dataclass(frozen=True)
class TaskStep:
    """A single step in the browser automation plan.

    Attributes:
        step_number: Ordinal position of this step (1-based).
        action: The type of browser action to perform.
        target_url: URL to navigate to (for navigate actions).
        instruction: Natural language description of what to do.
        completed: Whether this step has been executed.
    """

    step_number: int
    action: ActionType
    target_url: str = ""
    instruction: str = ""
    completed: bool = False


@dataclass
class TaskPlan:
    """A structured plan for a browser automation task.

    Attributes:
        task: The original user task description.
        scenario_type: Classification of the task type.
        steps: Ordered list of browser steps to execute.
        target_urls: URLs involved in the task.
    """

    task: str
    scenario_type: ScenarioType
    steps: list[TaskStep] = field(default_factory=list)
    target_urls: list[str] = field(default_factory=list)


@dataclass
class BrowserContext:
    """Shared context object passed through the agent pipeline via RunContextWrapper.

    Holds the Stagehand session, accumulated observations, action history,
    and extraction results as agents work through the pipeline.

    Attributes:
        task: The original user automation task.
        config: API keys and model settings.
        session: The Stagehand browser session (set after creation).
        current_url: The URL the browser is currently on.
        task_plan: The generated automation plan (set by planner).
        action_log: History of all browser actions performed.
        extraction_results: Structured data extracted from pages.
    """

    task: str
    config: dict[str, str | None]
    session: Any = None
    current_url: str = ""
    task_plan: TaskPlan | None = None
    action_log: list[Any] = field(default_factory=list)
    extraction_results: list[Any] = field(default_factory=list)
