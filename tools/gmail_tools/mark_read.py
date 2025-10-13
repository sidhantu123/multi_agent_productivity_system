"""Gmail tool: mark_email_as_read"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def mark_email_as_read(ctx: RunContext[GmailDeps], email_number: int) -> str:
    """
    Mark an email as read.
    
    Args:
        email_number: The number of the email from the most recent list
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.mark_as_read(email_id)
    
    if success:
        return f"Email {email_number} marked as read successfully"
    else:
        return "Failed to mark email as read"
