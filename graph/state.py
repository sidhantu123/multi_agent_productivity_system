"""State definition for the Gmail conversation graph"""

from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages


class GmailState(TypedDict):
    """State for the Gmail conversation graph using LangGraph built-in memory"""
    messages: Annotated[List[dict], add_messages]
    user_query: str
    agent_response: str
    continue_conversation: bool
    # Gmail-specific fields
    emails: Optional[List[dict]]  # List of fetched emails
    selected_email_id: Optional[str]  # Currently selected email ID
    email_action: Optional[str]  # Action to perform (list, read, search, etc.)

