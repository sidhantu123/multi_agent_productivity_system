"""Gmail tool: create_draft_email"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def create_draft_email(ctx: RunContext[GmailDeps], to: str, subject: str, body: str) -> str:
    """
    Create a draft email (does NOT send it).
    
    Use this when you want to prepare an email for the user to review before sending.
    The user can then review and send it manually from Gmail.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
    
    Returns:
        Confirmation message with draft ID
    """
    draft_id = ctx.deps.gmail_service.create_draft(to, subject, body)
    
    if draft_id:
        return f"Draft created successfully!\n\nTo: {to}\nSubject: {subject}\n\nYou can review and send this draft from Gmail. Draft ID: {draft_id}"
    else:
        return "Failed to create draft"
