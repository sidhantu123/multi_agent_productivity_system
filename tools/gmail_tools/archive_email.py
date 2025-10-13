"""Gmail tool: archive_email"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def archive_email(ctx: RunContext[GmailDeps], email_number: int) -> str:
    """
    Archive an email (remove from inbox).
    
    Args:
        email_number: The number of the email from the most recent list
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.archive_email(email_id)
    
    if success:
        return f"Email {email_number} archived successfully"
    else:
        return "Failed to archive email"
