"""Gmail tool: send_email"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def send_email(ctx: RunContext[GmailDeps], to: str, subject: str, body: str) -> str:
    """
    Send a new email.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
    """
    success = ctx.deps.gmail_service.send_email(to, subject, body)
    
    if success:
        return f"Email sent successfully to {to}"
    else:
        return "Failed to send email"
