"""Data models for the Browser Automation Agent.

Provides structured types for tasks, page state, and results
used throughout the agent pipeline.
"""

from browser_automation_agent.models.page import ActionRecord, PageObservation
from browser_automation_agent.models.result import (AutomationReport,
                                                     ExtractionResult)
from browser_automation_agent.models.task import (BrowserContext, TaskPlan,
                                                   TaskStep)

__all__ = [
    "ActionRecord",
    "AutomationReport",
    "BrowserContext",
    "ExtractionResult",
    "PageObservation",
    "TaskPlan",
    "TaskStep",
]
