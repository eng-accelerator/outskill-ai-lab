"""Data models for page state and browser actions.

Defines the structured types for page observations (what the browser
sees) and action records (what the browser did).
"""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class PageObservation:
    """An observation of available actions on the current page.

    Attributes:
        url: The page URL at the time of observation.
        instruction: The natural language instruction used for observation.
        actions_found: Number of actionable elements found.
        raw_response: JSON string of the raw observation response.
    """

    url: str
    instruction: str
    actions_found: int
    raw_response: str


@dataclass(frozen=True)
class ActionRecord:
    """A record of a browser action that was executed.

    Attributes:
        action_type: The type of action performed (click, type, navigate, etc.).
        instruction: The natural language instruction that triggered the action.
        success: Whether the action completed successfully.
        message: Result message or error description.
        timestamp: When the action was performed (UTC).
    """

    action_type: str
    instruction: str
    success: bool
    message: str
    timestamp: str = ""

    def __post_init__(self) -> None:
        """Set timestamp to current UTC time if not provided."""
        if not self.timestamp:
            # frozen dataclass — use object.__setattr__ for init-time default
            object.__setattr__(
                self, "timestamp", datetime.now(timezone.utc).isoformat()
            )
