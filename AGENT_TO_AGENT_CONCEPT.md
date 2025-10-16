# Agent-to-Agent Pattern for Multi-Agent Productivity System

## Current Architecture (Orchestrator-Based)
```
User Query
    ↓
Orchestrator (LLM classifies intent)
    ↓
Routes to: Gmail Agent | Calendar Agent | Both (sequential)
```

**Problems:**
- Orchestrator does JSON string parsing (jank)
- Manual task decomposition into gmail_instruction/calendar_instruction
- Complex routing logic with execution_order
- Agents don't know about each other

---

## Agent-to-Agent Architecture (Handoff-Based)

```
User Query
    ↓
Default Agent (e.g., Gmail Agent)
    ↓
Agent decides if it needs help from another agent
    ↓
Calls handoff tool: transfer_to_calendar() or transfer_to_gmail()
    ↓
Other agent completes its task
    ↓
Can hand back control or end conversation
```

**Benefits:**
- No JSON parsing
- Agents naturally decide when to hand off
- Simpler routing (agents handle it themselves)
- More scalable (add new agents by just giving them handoff tools)

---

## Implementation Details

### 1. Create Handoff Tools

```python
# tools/handoff_tools/transfer_to_calendar.py
from pydantic_ai import Tool
from langgraph.types import Command

def transfer_to_calendar(context: str = "") -> Command:
    """Transfer control to the Calendar agent.

    Use this when:
    - User asks about calendar events, meetings, schedules
    - You need calendar data to complete a task
    - User wants to schedule, modify, or delete events

    Args:
        context: Optional context about what the Calendar agent should do
    """
    return Command(
        goto="calendar_agent",
        update={
            "messages": [{"role": "system", "content": f"Handoff from Gmail: {context}"}]
        }
    )


# tools/handoff_tools/transfer_to_gmail.py
def transfer_to_gmail(context: str = "") -> Command:
    """Transfer control to the Gmail agent.

    Use this when:
    - User asks about emails, inbox, messages
    - You need email data to complete a task
    - User wants to send, read, or manage emails

    Args:
        context: Optional context about what the Gmail agent should do
    """
    return Command(
        goto="gmail_agent",
        update={
            "messages": [{"role": "system", "content": f"Handoff from Calendar: {context}"}]
        }
    )
```

### 2. Register Handoff Tools with Agents

```python
# agents/gmail_agent.py
def create_gmail_agent():
    gmail_agent = Agent(...)

    # Register all existing tools
    gmail_agent.tool(list_emails)
    gmail_agent.tool(send_email)
    # ... etc ...

    # NEW: Register handoff tool
    gmail_agent.tool(transfer_to_calendar)

    return gmail_agent
```

```python
# agents/calendar_agent.py
def create_calendar_agent():
    calendar_agent = Agent(...)

    # Register all existing tools
    calendar_agent.tool(list_upcoming_events)
    calendar_agent.tool(schedule_meeting)
    # ... etc ...

    # NEW: Register handoff tool
    calendar_agent.tool(transfer_to_gmail)

    return calendar_agent
```

### 3. Update System Prompts

```python
# agents/gmail_agent.py - Add to system prompt:
"""
MULTI-AGENT COORDINATION:
If the user's request involves calendar operations (events, meetings, scheduling):
1. Use the transfer_to_calendar tool to hand off to the Calendar agent
2. Provide context about what the Calendar agent should do
3. Example: transfer_to_calendar("User wants to see events for next week")

If the user asks to do BOTH email and calendar tasks:
1. Complete the email part first
2. Then transfer to Calendar agent with context about the remaining task
"""
```

```python
# agents/calendar_agent.py - Add to system prompt:
"""
MULTI-AGENT COORDINATION:
If the user's request involves email operations (reading, sending, searching):
1. Use the transfer_to_gmail tool to hand off to the Gmail agent
2. Provide context about what the Gmail agent should do
3. Example: transfer_to_gmail("User wants to email summary of events")

If the user asks to do BOTH calendar and email tasks:
1. Complete the calendar part first
2. Then transfer to Gmail agent with context about the remaining task
"""
```

### 4. Simplify Graph Structure

```python
# graph/builder.py
def create_graph():
    """Create simplified agent-to-agent graph"""
    builder = StateGraph(UnifiedState)

    # Add agent nodes (they handle routing themselves via handoff tools)
    builder.add_node("gmail_agent", gmail_agent_node)
    builder.add_node("calendar_agent", calendar_agent_node)
    builder.add_node("user_input", user_input_node)

    # Simple flow: user_input -> default agent (gmail)
    builder.add_edge(START, "user_input")
    builder.add_conditional_edges(
        "user_input",
        should_continue,
        {
            "continue": "gmail_agent",  # Default to Gmail agent
            "end": END
        }
    )

    # No orchestrator needed!
    # No complex routing logic!
    # Agents use Command to route themselves

    memory_saver = MemorySaver()
    store = InMemoryStore()

    return builder.compile(
        checkpointer=memory_saver,
        store=store,
        interrupt_before=INTERRUPT_BEFORE
    )
```

### 5. Simplified Agent Nodes

```python
# graph/nodes.py
async def gmail_agent_node(state: UnifiedState) -> Command:
    """Gmail agent - now handles its own routing via handoff tools"""
    user_query = state["user_query"]

    # Get agent and dependencies
    agent = get_gmail_agent()
    deps = GmailDeps(emails=state.get('emails', []), ...)

    # Run agent - it will call transfer_to_calendar if needed
    result = await agent.run(user_query, deps=deps)

    # Agent returns Command via handoff tool, or we default to user_input
    if isinstance(result.output, Command):
        return result.output  # Agent decided to hand off

    # Otherwise, return to user
    return Command(
        goto="user_input",
        update={
            "agent_response": result.output,
            "messages": [{"role": "assistant", "content": str(result.output)}]
        }
    )
```

---

## Comparison: Current vs Agent-to-Agent

### Current Architecture
```python
# User: "Find calendar events and email them to me"

1. Orchestrator analyzes → "both", execution_order="calendar_first"
2. Orchestrator decomposes:
   - calendar_instruction: "find calendar events"
   - gmail_instruction: "email summary of events"
3. Router sends to calendar_agent first
4. Calendar agent runs with calendar_instruction
5. Calendar agent returns Command to gmail_agent
6. Gmail agent runs with gmail_instruction
7. Gmail agent returns Command to user_input
```

**Lines of code:** ~150 (orchestrator_node + routing logic + state fields)

### Agent-to-Agent
```python
# User: "Find calendar events and email them to me"

1. Gmail agent receives query
2. Gmail agent thinks: "I need calendar data first"
3. Gmail agent calls transfer_to_calendar("get events for next week")
4. Calendar agent retrieves events
5. Calendar agent calls transfer_to_gmail("email these events to user")
6. Gmail agent composes and sends email
7. Gmail agent returns to user
```

**Lines of code:** ~50 (just handoff tools + simplified nodes)

---

## Migration Path

### Phase 1: Keep Orchestrator, Add Handoff Tools
- Add handoff tools to both agents
- Keep orchestrator for routing
- Agents can still hand off to each other for "both" scenarios

### Phase 2: Make Orchestrator Optional
- Default to Gmail agent
- User can ask to "talk to calendar agent" if needed
- Orchestrator only used if explicitly requested

### Phase 3: Remove Orchestrator (Full Agent-to-Agent)
- Delete orchestrator_agent.py
- Delete orchestrator_node from graph
- Simplify state (remove orchestrator fields)
- Agents fully autonomous

---

## When to Use Each Pattern

### Use Orchestrator-Based (Current) When:
- You have 5+ agents (need central coordination)
- Agent capabilities overlap significantly
- You want guaranteed single-agent handling
- You need audit trail of routing decisions

### Use Agent-to-Agent When:
- You have 2-4 agents with clear domains
- Agents have distinct, non-overlapping capabilities
- You want agents to collaborate naturally
- You want simpler, more maintainable code

---

## Decision: Should You Migrate?

### Benefits of Migration:
✅ Remove JSON parsing jank
✅ Simpler routing logic (40% less code)
✅ More scalable (add agents without touching orchestrator)
✅ Agents naturally collaborate
✅ Easier to understand and debug

### Costs of Migration:
❌ Need to rewrite system prompts
❌ Need to test handoff behavior
❌ Loss of centralized routing logic
❌ Agents might hand off unnecessarily

### My Recommendation:
**Start with Phase 1** - Add handoff tools while keeping orchestrator. This gives you:
- Best of both worlds
- Fallback if agent-to-agent doesn't work well
- Ability to gradually migrate
- No big rewrites

Then measure:
- How often orchestrator says "both" vs agents naturally handing off
- Whether agents make good handoff decisions
- If code is actually simpler

If Phase 1 works well, proceed to Phase 2-3.
