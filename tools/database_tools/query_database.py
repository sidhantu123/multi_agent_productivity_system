"""Email database tool: query_email_database"""

from pydantic_ai import RunContext
from tinydb import Query
from tools.gmail_tools.core import GmailDeps
from tools.database_tools.db import get_db


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
