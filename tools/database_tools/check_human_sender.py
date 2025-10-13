"""Email database tool: check_if_human_sender"""

from pydantic_ai import RunContext
from tinydb import Query
from tools.gmail_tools.core import GmailDeps
from tools.database_tools.db import get_db


async def check_if_human_sender(ctx: RunContext[GmailDeps], email_address: str) -> str:
    """
    Analyze if an email address appears to be from a human (not automated/newsletter).
    
    Heuristics used:
    - Not from common no-reply addresses
    - Not from common automated domains
    - Has a personal-looking email format
    
    Args:
        email_address: The email address to check
    
    Returns:
        Assessment of whether this appears to be a human sender
    """
    email_lower = email_address.lower()
    
    # Common automated/no-reply patterns
    automated_patterns = [
        'noreply', 'no-reply', 'donotreply', 'do-not-reply',
        'notification', 'notifications', 'automated', 'auto-reply',
        'mailer-daemon', 'postmaster', 'bounces', 'newsletter',
        'updates', 'alerts', 'support@', 'help@', 'info@',
        'marketing@', 'news@', 'robot@'
    ]
    
    # Common automated domains
    automated_domains = [
        'noreply.', 'notifications.', 'updates.',
        'mail.google.com', 'facebookmail.com', 'linkedin.com',
        'github.com', 'notifications.', 'amazonses.com'
    ]
    
    # Check for automated patterns
    for pattern in automated_patterns:
        if pattern in email_lower:
            return f"'{email_address}' appears to be AUTOMATED (pattern: {pattern}). Not recommended to add to database."
    
    # Check for automated domains
    for domain in automated_domains:
        if domain in email_lower:
            return f"'{email_address}' appears to be AUTOMATED (domain: {domain}). Not recommended to add to database."
    
    # Looks like a human
    return f"'{email_address}' appears to be from a HUMAN. Safe to add to database."
