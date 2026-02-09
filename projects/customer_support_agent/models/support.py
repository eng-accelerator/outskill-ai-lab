"""Support ticket, knowledge base, and resolution data models.

Defines support-related types for tickets, escalations, knowledge base articles,
resolution summaries, and CSAT scoring used in the support agent system.
"""

from dataclasses import dataclass, field
from typing import Literal

# Support ticket priority levels
TicketPriority = Literal["low", "medium", "high", "urgent"]

# Support ticket categories
TicketCategory = Literal[
    "order_issue",
    "billing_issue",
    "technical_issue",
    "general_inquiry",
    "complaint",
    "feedback",
]

# Ticket statuses
TicketStatus = Literal[
    "open",
    "in_progress",
    "waiting_customer",
    "escalated",
    "resolved",
    "closed",
]

# Resolution types
ResolutionType = Literal[
    "resolved_by_agent",
    "resolved_with_action",
    "escalated_to_human",
    "pending_follow_up",
    "no_action_needed",
]

# Knowledge base article categories
KBCategory = Literal[
    "orders",
    "billing",
    "technical",
    "account",
    "general",
    "troubleshooting",
]


@dataclass(frozen=True)
class KBArticle:
    """A knowledge base article for customer self-service or agent reference.

    Attributes:
        article_id: Unique article identifier.
        title: Article title.
        content: Full article content.
        category: Article category.
        tags: Searchable tags.
        helpful_count: Number of times marked as helpful.
    """

    article_id: str
    title: str
    content: str
    category: KBCategory
    tags: list[str] = field(default_factory=list)
    helpful_count: int = 0


@dataclass(frozen=True)
class SupportTicket:
    """A customer support ticket.

    Attributes:
        ticket_id: Unique ticket identifier.
        customer_id: Customer who opened the ticket.
        category: Issue category.
        priority: Ticket priority level.
        subject: Brief subject line.
        description: Detailed issue description.
        status: Current ticket status.
        created_at: Ticket creation timestamp (ISO 8601).
    """

    ticket_id: str
    customer_id: str
    category: TicketCategory
    priority: TicketPriority
    subject: str
    description: str
    status: TicketStatus
    created_at: str


@dataclass(frozen=True)
class EscalationTicket:
    """An escalation ticket for cases requiring human intervention.

    Attributes:
        ticket_id: Reference to the original support ticket.
        reason: Reason for escalation.
        priority: Escalation priority.
        assigned_team: Team assigned to handle the escalation.
        notes: Additional context for the human agent.
    """

    ticket_id: str
    reason: str
    priority: TicketPriority
    assigned_team: str
    notes: str = ""


@dataclass(frozen=True)
class Resolution:
    """Resolution summary for a support interaction.

    Attributes:
        ticket_id: Reference to the support ticket.
        resolution_type: How the issue was resolved.
        summary: Human-readable resolution summary.
        actions_taken: List of actions taken during resolution.
        follow_up_required: Whether follow-up is needed.
    """

    ticket_id: str
    resolution_type: ResolutionType
    summary: str
    actions_taken: list[str] = field(default_factory=list)
    follow_up_required: bool = False


@dataclass(frozen=True)
class CSATScore:
    """Customer satisfaction score prediction.

    Attributes:
        score: Predicted CSAT score (1-5 scale).
        predicted_satisfaction: Descriptive satisfaction level.
        factors: Contributing factors that influenced the prediction.
    """

    score: int
    predicted_satisfaction: str
    factors: list[str] = field(default_factory=list)
