"""Gmail tool: delete_label"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def delete_label(ctx: RunContext[GmailDeps], label_name: str) -> str:
    """
    Delete a Gmail label (WARNING: This cannot be undone!).
    
    This will remove the label from all emails and delete it permanently.
    Note: System labels (INBOX, SENT, etc.) cannot be deleted.
    
    Args:
        label_name: The name of the label to delete
    
    Returns:
        Confirmation message
    """
    # First, get all labels to find the ID
    labels = ctx.deps.gmail_service.get_labels()
    
    # Find the label by name (case-insensitive)
    label_id = None
    actual_name = None
    for label in labels:
        if label['name'].lower() == label_name.lower():
            label_id = label['id']
            actual_name = label['name']
            break
    
    if not label_id:
        available_labels = [f"'{l['name']}'" for l in labels]
        return f"Label '{label_name}' not found. Available labels: {', '.join(available_labels)}"
    
    # Delete the label
    success = ctx.deps.gmail_service.delete_label(label_id)
    
    if success:
        return f"Label '{actual_name}' deleted successfully!"
    else:
        return f"Failed to delete label '{actual_name}'"
