"""Gmail tool: trash_email"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def trash_email(ctx: RunContext[GmailDeps], email_number: int) -> str:
    """
    Move an email to trash.
    
    Args:
        email_number: The number of the email from the most recent list
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.trash_email(email_id)
    
    if success:
        return f"Email {email_number} moved to trash successfully"
    else:
        return "Failed to trash email"
