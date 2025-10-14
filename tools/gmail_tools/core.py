"""Core Gmail API service layer - GmailTools class and dependencies"""

import os
import pickle
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass

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
    """Gmail API client for reading and modifying emails"""

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
        # Check if running in cloud environment
        is_cloud = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER')
        
        if is_cloud:
            # Cloud deployment - load from environment variables
            from tools.gmail_tools.credentials_loader import load_credentials_from_env
            creds = load_credentials_from_env()
        else:
            # Local development - load from files
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

    def get_unsubscribe_info(self, email_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract unsubscribe information from an email
        
        Args:
            email_id: Gmail message ID
            
        Returns:
            Dictionary with unsubscribe methods found, or None if none found
        """
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")

        try:
            # Get email with full headers
            message = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()

            # Parse headers
            headers = {h['name'].lower(): h['value'] for h in message['payload']['headers']}
            
            unsubscribe_info = {
                'has_unsubscribe': False,
                'methods': []
            }
            
            # Check for List-Unsubscribe header (RFC 2369)
            if 'list-unsubscribe' in headers:
                unsubscribe_info['has_unsubscribe'] = True
                list_unsub = headers['list-unsubscribe']
                
                # Parse List-Unsubscribe header (can contain multiple URLs)
                import re
                
                # Extract mailto: links
                mailto_matches = re.findall(r'<mailto:([^>]+)>', list_unsub)
                for mailto in mailto_matches:
                    unsubscribe_info['methods'].append({
                        'type': 'mailto',
                        'address': mailto,
                        'requires_confirmation': True
                    })
                
                # Extract HTTP/HTTPS links
                http_matches = re.findall(r'<(https?://[^>]+)>', list_unsub)
                for url in http_matches:
                    unsubscribe_info['methods'].append({
                        'type': 'http',
                        'url': url,
                        'requires_confirmation': True
                    })
            
            # Check for List-Unsubscribe-Post header (RFC 8058 - One-Click)
            if 'list-unsubscribe-post' in headers:
                # One-click unsubscribe is available
                # Find the HTTP URL from List-Unsubscribe
                for method in unsubscribe_info['methods']:
                    if method['type'] == 'http':
                        method['one_click'] = True
                        method['requires_confirmation'] = False  # Safe to automate
                        method['post_data'] = headers['list-unsubscribe-post']
                        break
            
            # If no List-Unsubscribe header, try to find unsubscribe link in body
            if not unsubscribe_info['has_unsubscribe']:
                body = self._get_email_body(message['payload'])
                import re
                
                # Look for common unsubscribe link patterns
                unsub_patterns = [
                    r'<a[^>]*href=["\']([^"\']*unsubscribe[^"\']*)["\']',
                    r'(https?://[^\s<>"]+unsubscribe[^\s<>"]*)',
                ]
                
                for pattern in unsub_patterns:
                    matches = re.findall(pattern, body, re.IGNORECASE)
                    if matches:
                        unsubscribe_info['has_unsubscribe'] = True
                        # Take first match only
                        unsubscribe_info['methods'].append({
                            'type': 'http',
                            'url': matches[0],
                            'requires_confirmation': True,
                            'found_in': 'body'
                        })
                        break
            
            return unsubscribe_info if unsubscribe_info['has_unsubscribe'] else None

        except HttpError as error:
            print(f"Error getting unsubscribe info: {error}")
            return None

    def unsubscribe_one_click(self, url: str, post_data: str = "List-Unsubscribe=One-Click") -> bool:
        """
        Execute one-click unsubscribe via POST request
        
        Args:
            url: Unsubscribe URL
            post_data: POST data (from List-Unsubscribe-Post header)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import httpx
            
            response = httpx.post(
                url,
                data=post_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10.0,
                follow_redirects=True
            )
            
            # Success codes: 2xx or 3xx
            return response.status_code < 400
            
        except Exception as error:
            print(f"Error executing one-click unsubscribe: {error}")
            return False

