"""Email database tool: add_email_to_database"""

from typing import Optional
from pydantic_ai import RunContext
from tinydb import Query
from datetime import datetime
from tools.gmail_tools.core import GmailDeps
from tools.database_tools.db import get_db


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
