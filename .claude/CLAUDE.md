# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a playground repository for experimenting with LangGraph, a framework for building stateful, multi-agent applications with LLMs.

## Development Setup

This repository is currently empty and ready for LangGraph experiments. When setting up projects here:

### Python Environment
- Use Python virtual environments for dependency isolation
- Common setup: `python -m venv venv` then `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
- Install LangGraph: `pip install langgraph langchain-core langchain-anthropic`

### Running Examples
- Execute Python scripts directly: `python <script_name>.py`
- For Jupyter notebooks: `jupyter notebook` or `jupyter lab`

## LangGraph Architecture Concepts

When working with LangGraph code in this repository:

### State Graphs
- LangGraph uses StateGraph to define agent workflows
- Nodes represent individual processing steps or agent actions
- Edges define the flow between nodes (conditional or direct)
- State is passed between nodes and can be annotated with reducers

### Key Patterns
- **Supervisor Pattern**: A supervisor node routes to specialized sub-agents
- **Sequential Pattern**: Linear chain of processing steps
- **Human-in-the-Loop**: Breakpoints for human approval/input
- **Memory/Checkpointing**: Persist state between runs using checkpointers

### Common Graph Components
- `StateGraph`: Main graph constructor
- `add_node()`: Add processing nodes
- `add_edge()`: Add unconditional transitions
- `add_conditional_edges()`: Add routing logic
- `compile()`: Finalize graph (with optional checkpointer)
- `invoke()` or `stream()`: Execute the graph

### Testing LangGraph Applications
- Test individual node functions independently
- Use mock LLM responses for deterministic tests
- Test graph structure and edge routing logic separately
- Integration tests should verify full graph execution paths

## Logs Directory

The `logs/` directory contains MCP (Model Context Protocol) server logs and should not be committed to version control.
