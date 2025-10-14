"""Load Gmail credentials from environment variables or files"""

import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send',
    'https://mail.google.com/'
]


def load_credentials():
    """
    Load Gmail credentials from environment variables (for deployment)
    or from files (for local development)
    """
    creds = None
    
    # Check if running in cloud environment
    is_cloud = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER')
    
    if is_cloud:
        # Load from environment variables
        return load_credentials_from_env()
    else:
        # Load from files (local development)
        return load_credentials_from_files()


def load_credentials_from_env():
    """Load credentials from environment variables (for Railway/Render)"""
    token_json = os.getenv('GOOGLE_TOKEN_JSON')
    
    if not token_json:
        raise ValueError(
            "GOOGLE_TOKEN_JSON environment variable not set. "
            "Please add your Gmail token to the deployment environment."
        )
    
    try:
        token_data = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("Credentials refreshed successfully")
        
        return creds
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in GOOGLE_TOKEN_JSON: {e}")


def load_credentials_from_files():
    """Load credentials from local files (for development)"""
    from config.settings import GOOGLE_TOKEN_PATH, GOOGLE_CREDENTIALS_PATH
    
    creds = None
    
    # Load existing token
    if os.path.exists(GOOGLE_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH, SCOPES)
    
    # If no valid credentials, trigger OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(GOOGLE_TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    
    return creds


def get_token_json_for_deployment():
    """
    Helper function to get token JSON string for deployment.
    Run this locally after authenticating to get the value for GOOGLE_TOKEN_JSON.
    """
    from config.settings import GOOGLE_TOKEN_PATH
    
    if not os.path.exists(GOOGLE_TOKEN_PATH):
        print("❌ No token file found. Please run the agent locally first to authenticate.")
        return None
    
    with open(GOOGLE_TOKEN_PATH, 'r') as f:
        token_json = f.read().strip()
    
    print("\n" + "="*60)
    print("Copy this value to your Railway/Render environment variable:")
    print("Variable name: GOOGLE_TOKEN_JSON")
    print("="*60)
    print(token_json)
    print("="*60 + "\n")
    
    return token_json


if __name__ == "__main__":
    # Run this to get your token JSON for deployment
    get_token_json_for_deployment()

