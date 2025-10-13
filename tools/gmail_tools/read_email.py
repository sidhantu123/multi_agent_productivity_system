"""Gmail tool: read_email"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def read_email(ctx: RunContext[GmailDeps], email_number: int) -> str:
    """
    Read a specific email by its number from the most recent list.
    
    Args:
        email_number: The number of the email from the most recent list (e.g., 1 for first email)
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list or search for emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    email = ctx.deps.gmail_service.get_email(email_id)
    
    if not email:
        return "Could not retrieve email details."
    
    result = [
        "\n" + "=" * 60,
        "EMAIL DETAILS",
        "=" * 60,
        f"\nSubject: {email['subject']}",
        f"From: {email['from']}",
        f"Date: {email['date']}",
        f"\n{'-' * 60}",
        f"\n{email['body'][:1500]}",  # Limit body length
        f"\n{'-' * 60}",
        "=" * 60
    ]
    
    return "\n".join(result)
