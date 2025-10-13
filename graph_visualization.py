"""Graph Visualization - Generate Mermaid diagram of the Gmail Agent graph"""

import asyncio
from graph.builder import create_gmail_graph


def visualize_graph():
    """Generate and display the graph visualization in Mermaid format"""
    print("\n" + "="*80)
    print("Gmail Agent Graph Visualization (Mermaid)")
    print("="*80)
    
    # Create the graph
    graph = create_gmail_graph()
    
    try:
        # Generate Mermaid diagram
        mermaid_code = graph.get_graph().draw_mermaid()
        print("\n" + mermaid_code)
        print("\n" + "="*80)
        print("Copy the above code to https://mermaid.live to visualize the graph")
        print("="*80 + "\n")
    except Exception as e:
        print(f"Error generating Mermaid visualization: {e}")
        print("="*80 + "\n")


if __name__ == "__main__":
    visualize_graph()

