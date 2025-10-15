"""State definition for the unified multi-agent conversation graph"""

from typing import TypedDict, Annotated, List, Optional, Literal
from langgraph.graph.message import add_messages


class UnifiedState(TypedDict):
    """Unified state for the multi-agent conversation graph using LangGraph built-in memory"""
    messages: Annotated[List[dict], add_messages]
    user_query: str
    agent_response: str
    continue_conversation: bool

    # Orchestrator fields
    agent_type: Optional[Literal["gmail", "calendar", "both", "terminate"]]  # Which agent to route to
    execution_order: Optional[Literal["gmail_first", "calendar_first"]]  # For "both" tasks
    gmail_instruction: Optional[str]  # Specialized instruction for Gmail agent
    calendar_instruction: Optional[str]  # Specialized instruction for Calendar agent

    # Gmail-specific fields
    emails: Optional[List[dict]]  # List of fetched emails
    selected_email_id: Optional[str]  # Currently selected email ID
    email_action: Optional[str]  # Action to perform (list, read, search, etc.)

    # Calendar-specific fields
    events: Optional[List[dict]]  # List of fetched calendar events
    selected_event_id: Optional[str]  # Currently selected event ID
    calendar_action: Optional[str]  # Action to perform (list, create, update, etc.)

