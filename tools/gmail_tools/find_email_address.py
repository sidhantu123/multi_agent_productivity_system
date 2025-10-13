"""Gmail tool: find_email_address"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def find_email_address(ctx: RunContext[GmailDeps], person_name: str, max_results: int = 10) -> str:
    """
    Find email address(es) for a person by searching through past emails.
    
    This tool searches your email history to find the email addresses associated with a person's name.
    Use this BEFORE sending emails to verify you have the correct email address.
    
    Args:
        person_name: The name of the person to find (e.g., "Mangesh", "John Smith")
        max_results: Maximum number of results to search through (default 10)
    
    Returns:
        A list of email addresses found for that person with context from recent emails
    """
    # Search for emails from this person
    search_query = f"from:{person_name}"
    emails = ctx.deps.gmail_service.search_emails(search_query=search_query, max_results=max_results)
    
    if not emails:
        # Try searching in message body as well
        search_query = f"{person_name}"
        emails = ctx.deps.gmail_service.search_emails(search_query=search_query, max_results=max_results)
    
    if not emails:
        return f"No emails found from or mentioning '{person_name}'. Cannot determine email address."
    
    # Extract unique email addresses
    email_addresses = {}
    for email in emails:
        sender = email.get('from', '')
        # Extract email from "Name <email@example.com>" format
        if '<' in sender and '>' in sender:
            email_addr = sender.split('<')[1].split('>')[0].strip().lower()
            sender_name = sender.split('<')[0].strip()
        else:
            email_addr = sender.strip().lower()
            sender_name = sender
        
        # Check if this name matches what we're looking for
        if person_name.lower() in sender_name.lower():
            if email_addr not in email_addresses:
                email_addresses[email_addr] = {
                    'name': sender_name,
                    'count': 0,
                    'latest_subject': email.get('subject', 'No subject')
                }
            email_addresses[email_addr]['count'] += 1
    
    if not email_addresses:
        return f"Found emails mentioning '{person_name}', but couldn't extract their email address."
    
    # Format results
    result = [f"\nFound {len(email_addresses)} email address(es) for '{person_name}':", "=" * 60]
    
    # Sort by frequency (most emails first)
    sorted_addresses = sorted(email_addresses.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for email_addr, info in sorted_addresses:
        result.append(f"\n  {email_addr}")
        result.append(f"   Name: {info['name']}")
        result.append(f"   Email count: {info['count']} email(s)")
        result.append(f"   Latest: {info['latest_subject']}")
    
    result.append("\n" + "=" * 60)
    result.append("\n Tip: Use the most recent/frequently used email address for this person.")
    
    return "\n".join(result)
