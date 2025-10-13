"""Gmail Tools - Modular Gmail API integration for Pydantic AI"""

# Core components
from tools.gmail_tools.core import GmailDeps, GmailTools, SCOPES

# Viewing tools
from tools.gmail_tools.list_emails import list_emails
from tools.gmail_tools.get_unread import get_unread_emails
from tools.gmail_tools.search_emails import search_emails
from tools.gmail_tools.read_email import read_email

# Modification tools
from tools.gmail_tools.mark_read import mark_email_as_read
from tools.gmail_tools.mark_unread import mark_email_as_unread
from tools.gmail_tools.archive_email import archive_email
from tools.gmail_tools.trash_email import trash_email
from tools.gmail_tools.delete_email import delete_email

# Label management tools
from tools.gmail_tools.get_labels import get_labels
from tools.gmail_tools.create_label import create_label
from tools.gmail_tools.delete_label import delete_label
from tools.gmail_tools.add_label import add_label_to_email
from tools.gmail_tools.remove_label import remove_label_from_email

# Composition tools
from tools.gmail_tools.send_email import send_email
from tools.gmail_tools.reply_to_email import reply_to_email
from tools.gmail_tools.create_draft import create_draft_email
from tools.gmail_tools.create_draft_reply import create_draft_reply

# Lookup tools
from tools.gmail_tools.find_email_address import find_email_address

# Unsubscribe tool
from tools.gmail_tools.unsubscribe import unsubscribe_from_email


__all__ = [
    # Core
    'GmailDeps',
    'GmailTools',
    'SCOPES',
    # Viewing
    'list_emails',
    'get_unread_emails',
    'search_emails',
    'read_email',
    # Modification
    'mark_email_as_read',
    'mark_email_as_unread',
    'archive_email',
    'trash_email',
    'delete_email',
    # Labels
    'get_labels',
    'create_label',
    'delete_label',
    'add_label_to_email',
    'remove_label_from_email',
    # Composition
    'send_email',
    'reply_to_email',
    'create_draft_email',
    'create_draft_reply',
    # Lookup
    'find_email_address',
    # Unsubscribe
    'unsubscribe_from_email',
]

