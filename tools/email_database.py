"""Email database tools for caching known contacts"""

import os
from typing import List, Optional
from datetime import datetime
from pydantic_ai import RunContext
from tinydb import TinyDB, Query
from tools.gmail_tools import GmailDeps


# Initialize database
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'email_contacts.json')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_db():
    """Get database instance"""
    return TinyDB(DB_PATH)


async def query_email_database(ctx: RunContext[GmailDeps], person_name: str) -> str:
    """
    Query the email database for a person's email address.
    
    This is MUCH faster than searching through emails. Use this FIRST before using find_email_address.
    
    Args:
        person_name: The name of the person to find (e.g., "Mangesh", "John Smith")
    
    Returns:
        Email address(es) from the database if found, otherwise a message to use find_email_address
    """
    db = get_db()
    Contact = Query()
    
    # Search for contacts matching the name (case-insensitive partial match)
    results = db.search(Contact.name.search(person_name, flags=2))  # flags=2 for case-insensitive
    
    if not results:
        return f"No contact found in database for '{person_name}'. Use find_email_address to search email history."
    
    # Format results
    response = [f"\nFound {len(results)} contact(s) in database for '{person_name}':", "=" * 60]
    
    for contact in results:
        response.append(f"\n  {contact['email']}")
        response.append(f"   Name: {contact['name']}")
        response.append(f"   Added: {contact.get('added_date', 'Unknown')}")
        response.append(f"   Last updated: {contact.get('last_updated', 'Unknown')}")
        if contact.get('notes'):
            response.append(f"   Notes: {contact['notes']}")
    
    response.append("\n" + "=" * 60)
    
    db.close()
    return "\n".join(response)


async def add_email_to_database(
    ctx: RunContext[GmailDeps], 
    name: str, 
    email: str, 
    notes: Optional[str] = None
) -> str:
    """
    Add or update an email contact in the database.
    
    Use this to save email addresses for future quick lookups.
    
    Args:
        name: The person's name (e.g., "Mangesh Patel", "John Smith")
        email: The email address
        notes: Optional notes about this contact
    
    Returns:
        Confirmation message
    """
    db = get_db()
    Contact = Query()
    
    # Check if contact already exists
    existing = db.search((Contact.email == email.lower()) | (Contact.name == name))
    
    contact_data = {
        'name': name,
        'email': email.lower(),
        'notes': notes or '',
        'last_updated': datetime.now().isoformat()
    }
    
    if existing:
        # Update existing contact
        db.update(contact_data, Contact.email == email.lower())
        message = f"Updated contact: {name} ({email})"
    else:
        # Add new contact
        contact_data['added_date'] = datetime.now().isoformat()
        db.insert(contact_data)
        message = f"Added new contact: {name} ({email})"
    
    db.close()
    return message


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


async def list_all_contacts(ctx: RunContext[GmailDeps]) -> str:
    """
    List all contacts in the email database.
    
    Returns:
        List of all saved contacts
    """
    db = get_db()
    contacts = db.all()
    
    if not contacts:
        db.close()
        return "No contacts in database yet. Add contacts using add_email_to_database."
    
    # Sort by name
    contacts.sort(key=lambda x: x.get('name', '').lower())
    
    response = [f"\nEmail Database - {len(contacts)} contact(s):", "=" * 60]
    
    for i, contact in enumerate(contacts, 1):
        response.append(f"\n{i}. {contact['name']}")
        response.append(f"   Email: {contact['email']}")
        if contact.get('notes'):
            response.append(f"   Notes: {contact['notes']}")
    
    response.append("\n" + "=" * 60)
    
    db.close()
    return "\n".join(response)


async def remove_contact_from_database(ctx: RunContext[GmailDeps], email: str) -> str:
    """
    Remove a contact from the database.
    
    Args:
        email: The email address to remove
    
    Returns:
        Confirmation message
    """
    db = get_db()
    Contact = Query()
    
    removed = db.remove(Contact.email == email.lower())
    db.close()
    
    if removed:
        return f"Removed {email} from database"
    else:
        return f"Contact {email} not found in database"

