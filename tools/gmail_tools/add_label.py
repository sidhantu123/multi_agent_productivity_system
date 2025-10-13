"""Gmail tool: add_label_to_email"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def add_label_to_email(ctx: RunContext[GmailDeps], email_number: int, label_name: str) -> str:
    """
    Add a label to an email.
    
    Args:
        email_number: The number of the email from the most recent list
        label_name: The name of the label to add (e.g., "IMPORTANT", "STARRED", or custom label name)
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    # Get all labels to find the matching label ID
    labels = ctx.deps.gmail_service.get_labels()
    label_id = None
    
    # Check for exact match or case-insensitive match
    for label in labels:
        if label['name'].upper() == label_name.upper() or label['id'].upper() == label_name.upper():
            label_id = label['id']
            break
    
    if not label_id:
        return f"Label '{label_name}' not found. Use get_labels to see available labels."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.add_label(email_id, label_id)
    
    if success:
        return f"Label '{label_name}' added to email {email_number}"
    else:
        return "Failed to add label"
