"""Gmail API Tools for reading and viewing emails"""

import os
import pickle
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass

from pydantic_ai import RunContext
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Gmail API scopes - includes full Gmail access for all operations including deletion
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',  # Read/write (labels, archive, trash)
    'https://www.googleapis.com/auth/gmail.compose',  # Create and send drafts
    'https://www.googleapis.com/auth/gmail.send',     # Send emails
    'https://mail.google.com/'                         # Full Gmail access (includes permanent deletion)
]


@dataclass
class GmailDeps:
    """Dependencies for Gmail tools - holds email context"""
    emails: List[dict]
    gmail_service: 'GmailTools'


class GmailTools:
    """Gmail API client for reading emails"""

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None
    ):
        self.credentials_path = credentials_path or os.getenv(
            'GOOGLE_CREDENTIALS_PATH',
            'config/google_credentials.json'
        )
        self.token_path = token_path or os.getenv(
            'GOOGLE_TOKEN_PATH',
            'config/google_token.json'
        )
        self.service = None
        self.authenticate()

    def authenticate(self) -> None:
        """Authenticate with Gmail API"""
        creds = None

        # Load existing token
        if Path(self.token_path).exists():
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not Path(self.credentials_path).exists():
                    raise FileNotFoundError(
                        f"Google credentials not found at {self.credentials_path}. "
                        "Please ensure google_credentials.json is in the config folder."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path,
                    SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials
            Path(self.token_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)

    def list_emails(
        self,
        max_results: int = 10,
        query: Optional[str] = None,
        label_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List emails from Gmail inbox

        Args:
            max_results: Maximum number of emails to return (default 10)
            query: Gmail query string (e.g., "is:unread", "from:example@gmail.com")
            label_ids: List of label IDs to filter by (e.g., ["INBOX", "UNREAD"])

        Returns:
            List of email dictionaries with id, subject, from, snippet, date
        """
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            # Build request parameters
            params = {
                'userId': 'me',
                'maxResults': max_results
            }
            
            if query:
                params['q'] = query
            if label_ids:
                params['labelIds'] = label_ids

            # Get message list
            results = self.service.users().messages().list(**params).execute()
            messages = results.get('messages', [])

            # Fetch full details for each message
            emails = []
            for msg in messages:
                email_data = self.get_email(msg['id'])
                if email_data:
                    emails.append(email_data)

            return emails

        except HttpError as error:
            print(f"Error fetching emails: {error}")
            return []

    def get_email(self, email_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full details of a specific email

        Args:
            email_id: Gmail message ID

        Returns:
            Dictionary with email details (id, subject, from, body, date, etc.)
        """
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            message = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()

            # Parse headers
            headers = {h['name']: h['value'] for h in message['payload']['headers']}
            
            # Extract sender info
            sender = headers.get('From', '')
            subject = headers.get('Subject', '')
            date_str = headers.get('Date', '')
            
            # Parse date
            try:
                from email.utils import parsedate_to_datetime
                received_at = parsedate_to_datetime(date_str)
            except:
                received_at = datetime.utcnow()

            # Get email body
            body = self._get_email_body(message['payload'])
            
            # Get snippet
            snippet = message.get('snippet', '')

            return {
                'id': message['id'],
                'thread_id': message.get('threadId'),
                'subject': subject,
                'from': sender,
                'date': received_at.isoformat(),
                'snippet': snippet,
                'body': body,
                'labels': message.get('labelIds', [])
            }

        except HttpError as error:
            print(f"Error fetching email {email_id}: {error}")
            return None

    def _get_email_body(self, payload: dict) -> str:
        """Extract email body from Gmail payload"""
        import base64
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html' and not any(p['mimeType'] == 'text/plain' for p in payload['parts']):
                    # Use HTML if no plain text available
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        elif 'body' in payload and 'data' in payload['body']:
            data = payload['body']['data']
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

        return ""

    def search_emails(
        self,
        search_query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search emails using Gmail query syntax

        Args:
            search_query: Gmail search query (e.g., "from:example@gmail.com subject:meeting")
            max_results: Maximum number of results to return

        Returns:
            List of matching emails
        """
        return self.list_emails(max_results=max_results, query=search_query)

    def get_unread_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get unread emails from inbox"""
        return self.list_emails(
            max_results=max_results,
            query="is:unread",
            label_ids=["INBOX", "UNREAD"]
        )

    # ==================== MODIFICATION TOOLS ====================

    def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read"""
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as error:
            print(f"Error marking email as read: {error}")
            return False

    def mark_as_unread(self, email_id: str) -> bool:
        """Mark an email as unread"""
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as error:
            print(f"Error marking email as unread: {error}")
            return False

    def archive_email(self, email_id: str) -> bool:
        """Archive an email (remove from inbox)"""
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            return True
        except HttpError as error:
            print(f"Error archiving email: {error}")
            return False

    def trash_email(self, email_id: str) -> bool:
        """Move an email to trash"""
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            self.service.users().messages().trash(
                userId='me',
                id=email_id
            ).execute()
            return True
        except HttpError as error:
            print(f"Error trashing email: {error}")
            return False

    def delete_email(self, email_id: str) -> bool:
        """Permanently delete an email"""
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            self.service.users().messages().delete(
                userId='me',
                id=email_id
            ).execute()
            return True
        except HttpError as error:
            print(f"Error deleting email: {error}")
            return False

    def get_labels(self) -> List[Dict[str, str]]:
        """Get all Gmail labels"""
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            return [{'id': label['id'], 'name': label['name']} for label in labels]
        except HttpError as error:
            print(f"Error fetching labels: {error}")
            return []

    def create_label(self, label_name: str) -> Optional[Dict[str, str]]:
        """
        Create a new Gmail label
        
        Args:
            label_name: Name for the new label
            
        Returns:
            Dictionary with label id and name if created successfully, None otherwise
        """
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            
            created_label = self.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            
            return {'id': created_label['id'], 'name': created_label['name']}
        except HttpError as error:
            print(f"Error creating label: {error}")
            return None

    def delete_label(self, label_id: str) -> bool:
        """
        Delete a Gmail label
        
        Args:
            label_id: ID of the label to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            self.service.users().labels().delete(
                userId='me',
                id=label_id
            ).execute()
            return True
        except HttpError as error:
            print(f"Error deleting label: {error}")
            return False

    def add_label(self, email_id: str, label_id: str) -> bool:
        """Add a label to an email"""
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': [label_id]}
            ).execute()
            return True
        except HttpError as error:
            print(f"Error adding label: {error}")
            return False

    def remove_label(self, email_id: str, label_id: str) -> bool:
        """Remove a label from an email"""
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': [label_id]}
            ).execute()
            return True
        except HttpError as error:
            print(f"Error removing label: {error}")
            return False

    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Create a draft email
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            
        Returns:
            Draft ID if created successfully, None otherwise
        """
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            import base64
            from email.mime.text import MIMEText

            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()
            
            return draft['id']
        except HttpError as error:
            print(f"Error creating draft: {error}")
            return None

    def create_draft_reply(
        self,
        email_id: str,
        reply_body: str
    ) -> Optional[str]:
        """
        Create a draft reply to an email (does NOT send it)
        
        Args:
            email_id: ID of the email to reply to
            reply_body: Reply message body
            
        Returns:
            Draft ID if created successfully, None otherwise
        """
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            import base64
            from email.mime.text import MIMEText
            
            # Get the original email details
            original = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Message-ID']
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in original['payload']['headers']}
            original_from = headers.get('From', '')
            original_subject = headers.get('Subject', '')
            message_id = headers.get('Message-ID', '')
            thread_id = original.get('threadId', '')
            
            # Prepare reply subject
            reply_subject = original_subject if original_subject.startswith('Re:') else f"Re: {original_subject}"
            
            # Create reply message
            message = MIMEText(reply_body)
            message['to'] = original_from
            message['subject'] = reply_subject
            
            # Add threading headers
            if message_id:
                message['In-Reply-To'] = message_id
                message['References'] = message_id
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Create draft with thread ID
            draft_body = {
                'message': {
                    'raw': raw_message,
                    'threadId': thread_id
                }
            }
            
            draft = self.service.users().drafts().create(
                userId='me',
                body=draft_body
            ).execute()
            
            return draft['id']
        except HttpError as error:
            print(f"Error creating draft reply: {error}")
            return None

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            import base64
            from email.mime.text import MIMEText

            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return True
        except HttpError as error:
            print(f"Error sending email: {error}")
            return False

    def reply_to_email(
        self,
        email_id: str,
        body: str
    ) -> bool:
        """
        Reply to an email
        
        Args:
            email_id: ID of the email to reply to
            body: Reply message body
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            # Get original email
            original = self.get_email(email_id)
            if not original:
                return False

            import base64
            from email.mime.text import MIMEText

            # Create reply
            message = MIMEText(body)
            message['to'] = original['from']
            message['subject'] = f"Re: {original['subject']}"
            message['In-Reply-To'] = email_id
            message['References'] = email_id

            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            self.service.users().messages().send(
                userId='me',
                body={
                    'raw': raw_message,
                    'threadId': original['thread_id']
                }
            ).execute()
            
            return True
        except HttpError as error:
            print(f"Error replying to email: {error}")
            return False


# ==================== PYDANTIC AI TOOL FUNCTIONS ====================

async def list_emails(ctx: RunContext[GmailDeps], max_results: int = 10) -> str:
    """
    List recent emails from inbox.
    
    Args:
        max_results: Number of emails to return (default 10, max 50)
    """
    emails = ctx.deps.gmail_service.list_emails(max_results=max_results)
    
    # Update emails in context
    ctx.deps.emails = emails
    
    if not emails:
        return "No emails found in your inbox."
    
    result = [f"\nFound {len(emails)} recent emails:", "=" * 60]
    for i, email in enumerate(emails, 1):
        result.append(f"\n{i}. {email['subject']}")
        result.append(f"   From: {email['from']}")
        result.append(f"   Date: {email['date']}")
        result.append(f"   {email['snippet'][:80]}...")
    
    result.append("\n" + "=" * 60)
    return "\n".join(result)


async def get_unread_emails(ctx: RunContext[GmailDeps], max_results: int = 10) -> str:
    """
    Get unread emails from inbox.
    
    Args:
        max_results: Number of emails to return (default 10, max 50)
    """
    emails = ctx.deps.gmail_service.get_unread_emails(max_results=max_results)
    
    # Update emails in context
    ctx.deps.emails = emails
    
    if not emails:
        return "No unread emails found."
    
    result = [f"\nFound {len(emails)} unread emails:", "=" * 60]
    for i, email in enumerate(emails, 1):
        result.append(f"\n{i}. {email['subject']}")
        result.append(f"   From: {email['from']}")
        result.append(f"   Date: {email['date']}")
        result.append(f"   {email['snippet'][:80]}...")
    
    result.append("\n" + "=" * 60)
    return "\n".join(result)


async def search_emails(ctx: RunContext[GmailDeps], query: str, max_results: int = 10) -> str:
    """
    Search emails using Gmail's full query syntax.
    
    Supports ALL Gmail search operators including location filters, labels, dates, and more.
    
    Args:
        query: Gmail search query string
        max_results: Number of results to return (default 10)
    
    Common Search Operators:
        Location:
          - "in:inbox" - emails in inbox
          - "in:spam" - emails in spam folder
          - "in:trash" - emails in trash
          - "in:sent" - sent emails
          - "in:drafts" - draft emails
          - "in:anywhere" - search all folders
        
        Status:
          - "is:unread" - unread emails
          - "is:read" - read emails
          - "is:starred" - starred emails
          - "is:important" - marked as important
        
        Labels:
          - "label:work" - emails with "work" label
          - "label:important" - important label
        
        Sender/Recipient:
          - "from:john@example.com" - from specific sender
          - "to:sarah@example.com" - to specific recipient
          - "cc:bob@example.com" - CC'd to someone
        
        Content:
          - "subject:meeting" - subject contains "meeting"
          - "has:attachment" - has attachments
          - "filename:pdf" - has PDF attachment
        
        Date:
          - "after:2024/01/01" - after date
          - "before:2024/12/31" - before date
          - "newer_than:7d" - last 7 days
          - "older_than:1y" - older than 1 year
        
        Combine with AND/OR:
          - "from:john subject:meeting" - AND (both conditions)
          - "from:john OR from:sarah" - OR (either condition)
          - "-in:spam" - NOT (exclude spam)
    
    Examples:
        - "in:spam" - show spam emails
        - "in:trash is:unread" - unread emails in trash
        - "label:important after:2024/01/01" - important emails from this year
        - "from:john has:attachment" - emails from John with attachments
        - "in:sent to:sarah" - emails I sent to Sarah
    """
    emails = ctx.deps.gmail_service.search_emails(search_query=query, max_results=max_results)
    
    # Update emails in context
    ctx.deps.emails = emails
    
    if not emails:
        return f"No emails found matching: {query}"
    
    result = [f"\nFound {len(emails)} emails matching '{query}':", "=" * 60]
    for i, email in enumerate(emails, 1):
        result.append(f"\n{i}. {email['subject']}")
        result.append(f"   From: {email['from']}")
        result.append(f"   Date: {email['date']}")
        result.append(f"   {email['snippet'][:80]}...")
    
    result.append("\n" + "=" * 60)
    return "\n".join(result)


async def read_email(ctx: RunContext[GmailDeps], email_number: int) -> str:
    """
    Read a specific email by its number from the most recent list.
    
    Args:
        email_number: The number of the email from the most recent list (e.g., 1 for first email)
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list or search for emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    email = ctx.deps.gmail_service.get_email(email_id)
    
    if not email:
        return "Could not retrieve email details."
    
    result = [
        "\n" + "=" * 60,
        "EMAIL DETAILS",
        "=" * 60,
        f"\nSubject: {email['subject']}",
        f"From: {email['from']}",
        f"Date: {email['date']}",
        f"\n{'-' * 60}",
        f"\n{email['body'][:1500]}",  # Limit body length
        f"\n{'-' * 60}",
        "=" * 60
    ]
    
    return "\n".join(result)


async def mark_email_as_read(ctx: RunContext[GmailDeps], email_number: int) -> str:
    """
    Mark an email as read.
    
    Args:
        email_number: The number of the email from the most recent list
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.mark_as_read(email_id)
    
    if success:
        return f"Email {email_number} marked as read successfully"
    else:
        return "Failed to mark email as read"


async def mark_email_as_unread(ctx: RunContext[GmailDeps], email_number: int) -> str:
    """
    Mark an email as unread.
    
    Args:
        email_number: The number of the email from the most recent list
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.mark_as_unread(email_id)
    
    if success:
        return f"Email {email_number} marked as unread successfully"
    else:
        return "Failed to mark email as unread"


async def archive_email(ctx: RunContext[GmailDeps], email_number: int) -> str:
    """
    Archive an email (remove from inbox).
    
    Args:
        email_number: The number of the email from the most recent list
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.archive_email(email_id)
    
    if success:
        return f"Email {email_number} archived successfully"
    else:
        return "Failed to archive email"


async def trash_email(ctx: RunContext[GmailDeps], email_number: int) -> str:
    """
    Move an email to trash.
    
    Args:
        email_number: The number of the email from the most recent list
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.trash_email(email_id)
    
    if success:
        return f"Email {email_number} moved to trash successfully"
    else:
        return "Failed to trash email"


async def send_email(ctx: RunContext[GmailDeps], to: str, subject: str, body: str) -> str:
    """
    Send a new email.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
    """
    success = ctx.deps.gmail_service.send_email(to, subject, body)
    
    if success:
        return f"Email sent successfully to {to}"
    else:
        return "Failed to send email"


async def reply_to_email(ctx: RunContext[GmailDeps], email_number: int, reply_body: str) -> str:
    """
    Reply to an email.
    
    Args:
        email_number: The number of the email from the most recent list to reply to
        reply_body: The reply message text
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.reply_to_email(email_id, reply_body)
    
    if success:
        return f"Reply sent successfully to email {email_number}"
    else:
        return "Failed to send reply"


async def delete_email(ctx: RunContext[GmailDeps], email_number: int) -> str:
    """
    Permanently delete an email (WARNING: Cannot be undone!).
    
    Args:
        email_number: The number of the email from the most recent list
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.delete_email(email_id)
    
    if success:
        return f"Email {email_number} permanently deleted"
    else:
        return "Failed to delete email"


async def get_labels(ctx: RunContext[GmailDeps]) -> str:
    """
    Get all available Gmail labels.
    
    Returns a list of all labels in the Gmail account with their IDs and names.
    """
    labels = ctx.deps.gmail_service.get_labels()
    
    if not labels:
        return "No labels found."
    
    result = [f"\nFound {len(labels)} labels:", "=" * 60]
    for label in labels:
        result.append(f"  • {label['name']} (ID: {label['id']})")
    
    result.append("=" * 60)
    return "\n".join(result)


async def create_label(ctx: RunContext[GmailDeps], label_name: str) -> str:
    """
    Create a new Gmail label.
    
    Use this to create custom labels/categories for organizing emails.
    
    Args:
        label_name: The name for the new label (e.g., "Work", "Personal", "Urgent")
    
    Returns:
        Confirmation message with the created label details
    """
    result = ctx.deps.gmail_service.create_label(label_name)
    
    if result:
        return f"Label '{label_name}' created successfully! (ID: {result['id']})"
    else:
        return f"Failed to create label '{label_name}'. It may already exist or there was an error."


async def delete_label(ctx: RunContext[GmailDeps], label_name: str) -> str:
    """
    Delete a Gmail label (WARNING: This cannot be undone!).
    
    This will remove the label from all emails and delete it permanently.
    Note: System labels (INBOX, SENT, etc.) cannot be deleted.
    
    Args:
        label_name: The name of the label to delete
    
    Returns:
        Confirmation message
    """
    # First, get all labels to find the ID
    labels = ctx.deps.gmail_service.get_labels()
    
    # Find the label by name (case-insensitive)
    label_id = None
    actual_name = None
    for label in labels:
        if label['name'].lower() == label_name.lower():
            label_id = label['id']
            actual_name = label['name']
            break
    
    if not label_id:
        available_labels = [f"'{l['name']}'" for l in labels]
        return f"Label '{label_name}' not found. Available labels: {', '.join(available_labels)}"
    
    # Delete the label
    success = ctx.deps.gmail_service.delete_label(label_id)
    
    if success:
        return f"Label '{actual_name}' deleted successfully!"
    else:
        return f"Failed to delete label '{actual_name}'"


async def add_label_to_email(ctx: RunContext[GmailDeps], email_number: int, label_name: str) -> str:
    """
    Add a label to an email.
    
    Args:
        email_number: The number of the email from the most recent list
        label_name: The name of the label to add (e.g., "IMPORTANT", "STARRED", or custom label name)
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    # Get all labels to find the matching label ID
    labels = ctx.deps.gmail_service.get_labels()
    label_id = None
    
    # Check for exact match or case-insensitive match
    for label in labels:
        if label['name'].upper() == label_name.upper() or label['id'].upper() == label_name.upper():
            label_id = label['id']
            break
    
    if not label_id:
        return f"Label '{label_name}' not found. Use get_labels to see available labels."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.add_label(email_id, label_id)
    
    if success:
        return f"Label '{label_name}' added to email {email_number}"
    else:
        return "Failed to add label"


async def remove_label_from_email(ctx: RunContext[GmailDeps], email_number: int, label_name: str) -> str:
    """
    Remove a label from an email.
    
    Args:
        email_number: The number of the email from the most recent list
        label_name: The name of the label to remove (e.g., "IMPORTANT", "STARRED", or custom label name)
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    # Get all labels to find the matching label ID
    labels = ctx.deps.gmail_service.get_labels()
    label_id = None
    
    # Check for exact match or case-insensitive match
    for label in labels:
        if label['name'].upper() == label_name.upper() or label['id'].upper() == label_name.upper():
            label_id = label['id']
            break
    
    if not label_id:
        return f"Label '{label_name}' not found. Use get_labels to see available labels."
    
    email_id = emails[email_number - 1]['id']
    success = ctx.deps.gmail_service.remove_label(email_id, label_id)
    
    if success:
        return f"Label '{label_name}' removed from email {email_number}"
    else:
        return "Failed to remove label"


async def create_draft_email(ctx: RunContext[GmailDeps], to: str, subject: str, body: str) -> str:
    """
    Create a draft email (does NOT send it).
    
    Use this when you want to prepare an email for the user to review before sending.
    The user can then review and send it manually from Gmail.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
    
    Returns:
        Confirmation message with draft ID
    """
    draft_id = ctx.deps.gmail_service.create_draft(to, subject, body)
    
    if draft_id:
        return f"Draft created successfully!\n\nTo: {to}\nSubject: {subject}\n\nYou can review and send this draft from Gmail. Draft ID: {draft_id}"
    else:
        return "Failed to create draft"


async def create_draft_reply(ctx: RunContext[GmailDeps], email_number: int, reply_body: str) -> str:
    """
    Create a draft reply to an email (does NOT send it).
    
    Use this when the user wants to prepare a reply for review before sending.
    The draft reply will be saved in the same thread as the original email.
    
    Args:
        email_number: The number of the email to reply to (from the list)
        reply_body: The reply message text
    
    Returns:
        Confirmation message with draft ID
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails available. Please list emails first using list_emails or search_emails."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    original_subject = emails[email_number - 1]['subject']
    original_from = emails[email_number - 1]['from']
    
    draft_id = ctx.deps.gmail_service.create_draft_reply(email_id, reply_body)
    
    if draft_id:
        return f"Draft reply created successfully!\n\nReplying to: {original_from}\nSubject: Re: {original_subject}\n\nYou can review and send this draft reply from Gmail. Draft ID: {draft_id}"
    else:
        return "Failed to create draft reply"


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

