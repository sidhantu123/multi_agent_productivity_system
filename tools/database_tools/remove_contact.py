"""Email database tool: remove_contact_from_database"""

from pydantic_ai import RunContext
from tinydb import Query
from tools.gmail_tools.core import GmailDeps
from tools.database_tools.db import get_db


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
