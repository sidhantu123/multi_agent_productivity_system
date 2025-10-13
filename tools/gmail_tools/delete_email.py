"""Gmail tool: delete_email"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def delete_email(ctx: RunContext[GmailDeps], email_number: int) -> str:
    """
    Permanently delete an email (WARNING: Cannot be undone!).
    
    Args:
        email_number: The number of the email from the most recent list
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.delete_email(email_id)
    
    if success:
        return f"Email {email_number} permanently deleted"
    else:
        return "Failed to delete email"
