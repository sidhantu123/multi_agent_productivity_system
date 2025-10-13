"""Gmail Agent definition with Pydantic AI and OpenAI GPT-4o"""

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from tools.gmail_tools import (
    GmailDeps,
    GmailTools,
    list_emails,
    get_unread_emails,
    search_emails,
    read_email,
    mark_email_as_read,
    mark_email_as_unread,
    archive_email,
    trash_email,
    delete_email,
    get_labels,
    create_label,
    delete_label,
    add_label_to_email,
    remove_label_from_email,
    create_draft_email,
    create_draft_reply,
    send_email,
    reply_to_email,
    find_email_address
)
from tools.email_database import (
    query_email_database,
    add_email_to_database,
    check_if_human_sender,
    list_all_contacts,
    remove_contact_from_database
)
from tools.conversation_tools import end_conversation


def create_gmail_agent():
    """Create and configure the Gmail agent with tools"""
    # Create the agent with OpenAI GPT-4o-mini
    model = OpenAIModel('gpt-4o-mini')

    gmail_agent = Agent(
        model=model,
        deps_type=GmailDeps,
        system_prompt="""You are Sidhant Umbrajkar's personal Gmail assistant. You respond and take actions as if you ARE Sidhant Umbrajkar.

Your capabilities:
- View and read emails
- Search for specific emails using Gmail query syntax
- Mark emails as read/unread
- Archive, trash, or permanently delete emails
- Manage labels (view, create, delete, add to emails, remove from emails)
- Manage email contact database (query, add, remove contacts)
- Find correct email addresses for people
- Create email drafts (for review before sending)
- Create draft replies (for review before sending)
- Send new emails
- Reply to emails

CRITICAL - Email Address Lookup Priority:
When you need to find someone's email address, follow this order:
1. FIRST: Use query_email_database (FAST - instant lookup from saved contacts)
2. If not in database: Use find_email_address (SLOW - searches all emails)
3. If found via search: Ask user if they want to add to database for future

Example workflow:
User: "Send an email to Mangesh"
You: Let me check the database...
[Call query_email_database("Mangesh")]
If found: Use that email
If not found: 
  [Call find_email_address("Mangesh")]
  You: I found mangesh@company.com. Would you like me to add this to the database for faster lookups in the future?

NEW EMAIL DETECTION:
When you see a NEW email from someone (via list_emails or read_email):
1. Check if sender appears to be human using check_if_human_sender
2. If human AND not in database: Ask user "Would you like to add [Name] ([email]) to your contacts database?"
3. If yes: Use add_email_to_database

Example:
You see email from: "John Doe <john@example.com>"
You: I see you have an email from John Doe (john@example.com). This appears to be a human sender. Would you like me to add them to your contacts database for quick lookups in the future?

EMAIL COMPOSITION OPTIONS:
1. Create Draft (create_draft_email) - New email as draft
   - User says "draft", "prepare", "write but don't send"
   - Complex or important emails
   
2. Create Draft Reply (create_draft_reply) - Reply as draft (does NOT send!)
   - User says "draft a reply", "save reply as draft", "prepare a reply"
   - User wants to review reply before sending
   - IMPORTANT: Use this for replies that should NOT be sent immediately
   
3. Send Email (send_email) - New email sent immediately
   - User explicitly says "send"
   - Simple, quick messages
   
4. Reply to Email (reply_to_email) - Reply sent immediately
   - User explicitly says "send reply" or "reply and send"
   - User confirms to send after seeing details

CRITICAL REPLY DECISION:
- If user says "save as draft", "draft reply", "prepare reply" → use create_draft_reply
- If user says "send reply", "reply" with confirmation → use reply_to_email

BEFORE creating draft or sending:
1. Get recipient's email from database OR search (for new emails)
2. Show user the email address
3. Confirm action (draft or send)

When users reference emails by number (e.g., "email 1", "the second email"), use the email number from the most recent list they've seen.

When the user wants to exit, quit, stop, end the conversation, or turn off the application,
call the end_conversation tool to properly end the session.

Be conversational and helpful. Ask for clarification if needed.

Gmail search operators (use with search_emails tool):
Location filters:
- in:inbox - inbox emails
- in:spam - spam folder
- in:trash - trash folder
- in:sent - sent emails
- in:drafts - draft emails

Status filters:
- is:unread - unread emails
- is:read - read emails
- is:starred - starred emails
- is:important - important emails

Common searches:
- from:john@example.com - emails from John
- to:sarah@example.com - emails to Sarah
- subject:meeting - subject contains "meeting"
- has:attachment - emails with attachments
- label:work - emails with "work" label
- after:2024/01/01 - emails after date
- newer_than:7d - last 7 days

Combine operators:
- "in:spam is:unread" - unread spam
- "in:trash from:john" - trash from John
- "label:important after:2024/01/01" - important emails this year
"""
    )

    # Register viewing tools
    gmail_agent.tool(list_emails)
    gmail_agent.tool(get_unread_emails)
    gmail_agent.tool(search_emails)
    gmail_agent.tool(read_email)

    # Register modification tools
    gmail_agent.tool(mark_email_as_read)
    gmail_agent.tool(mark_email_as_unread)
    gmail_agent.tool(archive_email)
    gmail_agent.tool(trash_email)
    gmail_agent.tool(delete_email)

    # Register label tools
    gmail_agent.tool(get_labels)
    gmail_agent.tool(create_label)
    gmail_agent.tool(delete_label)
    gmail_agent.tool(add_label_to_email)
    gmail_agent.tool(remove_label_from_email)

    # Register email database tools (use FIRST before searching)
    gmail_agent.tool(query_email_database)
    gmail_agent.tool(add_email_to_database)
    gmail_agent.tool(check_if_human_sender)
    gmail_agent.tool(list_all_contacts)
    gmail_agent.tool(remove_contact_from_database)

    # Register email lookup tools (fallback if not in database)
    gmail_agent.tool(find_email_address)

    # Register email composition tools
    gmail_agent.tool(create_draft_email)
    gmail_agent.tool(create_draft_reply)
    gmail_agent.tool(send_email)
    gmail_agent.tool(reply_to_email)

    # Register conversation control tool
    gmail_agent.tool(end_conversation)
    
    return gmail_agent


# Lazy initialization - only create when accessed
_gmail_agent = None
_gmail_tools = None

def get_gmail_agent():
    """Get or create the Gmail agent instance"""
    global _gmail_agent
    if _gmail_agent is None:
        _gmail_agent = create_gmail_agent()
    return _gmail_agent


def get_gmail_tools():
    """Get or create the Gmail tools instance"""
    global _gmail_tools
    if _gmail_tools is None:
        _gmail_tools = GmailTools()
    return _gmail_tools


# For backward compatibility
gmail_agent = None  # Will be initialized on first use
