"""Shared database utilities for email contacts"""

import os
from tinydb import TinyDB

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'email_contacts.json')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_db():
    """Get database instance"""
    return TinyDB(DB_PATH)
