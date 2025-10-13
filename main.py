"""Main entry point for the Weather Agent application"""

import asyncio
from dotenv import load_dotenv

from utils.logging import setup_logging
from graph.builder import create_weather_graph
from graph.runner import run_weather_graph


async def main():
    """Main entry point for the weather agent application"""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    
    # Create the graph
    graph = create_weather_graph()
    
    # Run the graph
    await run_weather_graph(graph)


if __name__ == "__main__":
    asyncio.run(main())

