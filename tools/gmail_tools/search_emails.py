"""Gmail tool: search_emails"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def search_emails(ctx: RunContext[GmailDeps], query: str, max_results: int = 10) -> str:
    """
    Search emails using Gmail's full query syntax.
    
    Supports ALL Gmail search operators including location filters, labels, dates, and more.
    
    Args:
        query: Gmail search query string
        max_results: Number of results to return (default 10)
    
    Common Search Operators:
        Location:
          - "in:inbox" - emails in inbox
          - "in:spam" - emails in spam folder
          - "in:trash" - emails in trash
          - "in:sent" - sent emails
          - "in:drafts" - draft emails
          - "in:anywhere" - search all folders
        
        Status:
          - "is:unread" - unread emails
          - "is:read" - read emails
          - "is:starred" - starred emails
          - "is:important" - marked as important
        
        Labels:
          - "label:work" - emails with "work" label
          - "label:important" - important label
        
        Sender/Recipient:
          - "from:john@example.com" - from specific sender
          - "to:sarah@example.com" - to specific recipient
          - "cc:bob@example.com" - CC'd to someone
        
        Content:
          - "subject:meeting" - subject contains "meeting"
          - "has:attachment" - has attachments
          - "filename:pdf" - has PDF attachment
        
        Date:
          - "after:2024/01/01" - after date
          - "before:2024/12/31" - before date
          - "newer_than:7d" - last 7 days
          - "older_than:1y" - older than 1 year
        
        Combine with AND/OR:
          - "from:john subject:meeting" - AND (both conditions)
          - "from:john OR from:sarah" - OR (either condition)
          - "-in:spam" - NOT (exclude spam)
    
    Examples:
        - "in:spam" - show spam emails
        - "in:trash is:unread" - unread emails in trash
        - "label:important after:2024/01/01" - important emails from this year
        - "from:john has:attachment" - emails from John with attachments
        - "in:sent to:sarah" - emails I sent to Sarah
    """
    emails = ctx.deps.gmail_service.search_emails(search_query=query, max_results=max_results)
    
    # Update emails in context
    ctx.deps.emails = emails
    
    if not emails:
        return f"No emails found matching: {query}"
    
    result = [f"\nFound {len(emails)} emails matching '{query}':", "=" * 60]
    for i, email in enumerate(emails, 1):
        result.append(f"\n{i}. {email['subject']}")
        result.append(f"   From: {email['from']}")
        result.append(f"   Date: {email['date']}")
        result.append(f"   {email['snippet'][:80]}...")
    
    result.append("\n" + "=" * 60)
    return "\n".join(result)
