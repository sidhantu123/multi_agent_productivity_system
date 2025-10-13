"""Email database tool: list_all_contacts"""

from typing import List
from pydantic_ai import RunContext
from tinydb import Query
from tools.gmail_tools.core import GmailDeps
from tools.database_tools.db import get_db


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
