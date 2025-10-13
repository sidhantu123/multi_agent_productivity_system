"""Weather Agent definition with Pydantic AI and OpenAI GPT-4o"""

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from tools.location_tools import WeatherDeps, get_user_location, get_lat_long, convert_address_to_lat_long
from tools.weather_tools import get_weather
from tools.conversation_tools import end_conversation


def create_weather_agent():
    """Create and configure the weather agent with tools"""
    # Create the agent with OpenAI GPT-4o
    model = OpenAIModel('gpt-4o')

    weather_agent = Agent(
        model=model,
        deps_type=WeatherDeps,
        system_prompt="""You are a helpful weather assistant. You can help users get weather information
        for their location or any address they provide. Use the available tools to get location data and weather information.

        When the user wants to exit, quit, stop, end the conversation, or turn off the application,
        call the end_conversation tool to properly end the session. 

        Always provide clear, friendly responses with the weather details."""
    )

    # Register location tools
    weather_agent.tool(get_user_location)
    weather_agent.tool(get_lat_long)
    weather_agent.tool(convert_address_to_lat_long)

    # Register weather tool
    weather_agent.tool(get_weather)

    # Register conversation control tool
    weather_agent.tool(end_conversation)
    
    return weather_agent


# Lazy initialization - only create when accessed
_weather_agent = None

def get_weather_agent():
    """Get or create the weather agent instance"""
    global _weather_agent
    if _weather_agent is None:
        _weather_agent = create_weather_agent()
    return _weather_agent


# For backward compatibility
weather_agent = None  # Will be initialized on first use

