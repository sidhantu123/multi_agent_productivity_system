"""Main entry point for the Gmail Agent application"""

import asyncio
from dotenv import load_dotenv

from utils.logging import setup_logging
from graph.builder import create_gmail_graph
from graph.runner import run_gmail_graph


async def main():
    """Main entry point for the Gmail agent application"""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    setup_logging()
    
    # Create the graph
    graph = create_gmail_graph()
    
    # Run the graph
    await run_gmail_graph(graph)


if __name__ == "__main__":
    asyncio.run(main())

