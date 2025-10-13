"""State definition for the weather conversation graph"""

from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages


class WeatherState(TypedDict):
    """State for the weather conversation graph using LangGraph built-in memory"""
    messages: Annotated[List[dict], add_messages]
    user_query: str
    agent_response: str
    continue_conversation: bool

