"""Gmail tool: get_unread_emails"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def get_unread_emails(ctx: RunContext[GmailDeps], max_results: int = 10) -> str:
    """
    Get unread emails from inbox.
    
    Args:
        max_results: Number of emails to return (default 10, max 50)
    """
    emails = ctx.deps.gmail_service.get_unread_emails(max_results=max_results)
    
    # Update emails in context
    ctx.deps.emails = emails
    
    if not emails:
        return "No unread emails found."
    
    result = [f"\nFound {len(emails)} unread emails:", "=" * 60]
    for i, email in enumerate(emails, 1):
        result.append(f"\n{i}. {email['subject']}")
        result.append(f"   From: {email['from']}")
        result.append(f"   Date: {email['date']}")
        result.append(f"   {email['snippet'][:80]}...")
    
    result.append("\n" + "=" * 60)
    return "\n".join(result)
