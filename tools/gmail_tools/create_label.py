"""Gmail tool: create_label"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def create_label(ctx: RunContext[GmailDeps], label_name: str) -> str:
    """
    Create a new Gmail label.
    
    Use this to create custom labels/categories for organizing emails.
    
    Args:
        label_name: The name for the new label (e.g., "Work", "Personal", "Urgent")
    
    Returns:
        Confirmation message with the created label details
    """
    result = ctx.deps.gmail_service.create_label(label_name)
    
    if result:
        return f"Label '{label_name}' created successfully! (ID: {result['id']})"
    else:
        return f"Failed to create label '{label_name}'. It may already exist or there was an error."
