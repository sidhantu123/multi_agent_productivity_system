"""Gmail tool: reply_to_email"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def reply_to_email(ctx: RunContext[GmailDeps], email_number: int, reply_body: str) -> str:
    """
    Reply to an email.
    
    Args:
        email_number: The number of the email from the most recent list to reply to
        reply_body: The reply message text
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.reply_to_email(email_id, reply_body)
    
    if success:
        return f"Reply sent successfully to email {email_number}"
    else:
        return "Failed to send reply"
