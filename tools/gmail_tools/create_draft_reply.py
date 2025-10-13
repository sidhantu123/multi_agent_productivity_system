"""Gmail tool: create_draft_reply"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def create_draft_reply(ctx: RunContext[GmailDeps], email_number: int, reply_body: str) -> str:
    """
    Create a draft reply to an email (does NOT send it).
    
    Use this when the user wants to prepare a reply for review before sending.
    The draft reply will be saved in the same thread as the original email.
    
    Args:
        email_number: The number of the email to reply to (from the list)
        reply_body: The reply message text
    
    Returns:
        Confirmation message with draft ID
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails available. Please list emails first using list_emails or search_emails."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    original_subject = emails[email_number - 1]['subject']
    original_from = emails[email_number - 1]['from']
    
    draft_id = ctx.deps.gmail_service.create_draft_reply(email_id, reply_body)
    
    if draft_id:
        return f"Draft reply created successfully!\n\nReplying to: {original_from}\nSubject: Re: {original_subject}\n\nYou can review and send this draft reply from Gmail. Draft ID: {draft_id}"
    else:
        return "Failed to create draft reply"
