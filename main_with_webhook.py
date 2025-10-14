"""Enhanced CLI that connects to webhook server and processes emails when notified"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    subprocess.check_call(["pip", "install", "websockets"])
    import websockets

from utils.logging import setup_logging, get_logger
from graph.builder import create_gmail_graph
from graph.state import GmailState
from config.settings import THREAD_ID, SEPARATOR_LENGTH
from tools.gmail_tools import GmailTools, GmailDeps
from agents.gmail_agent import get_gmail_agent

# Load environment variables
load_dotenv()

# Initialize
logger = get_logger()


class WebhookCLI:
    """Enhanced CLI that receives webhook notifications and processes emails interactively"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv(
            'WEBHOOK_URL',
            'ws://localhost:8000/ws/cli'  # Local for development
        )
        self.gmail_tools = GmailTools()
        self.agent = get_gmail_agent()
        self.graph = create_gmail_graph()
        self.websocket = None
        self.running = True
    
    async def connect_to_webhook(self):
        """Connect to webhook server and listen for notifications"""
        while self.running:
            try:
                print(f"\n🔌 Connecting to webhook server: {self.webhook_url}")
                
                async with websockets.connect(self.webhook_url) as websocket:
                    self.websocket = websocket
                    print("✓ Connected to webhook server")
                    print("⏰ Waiting for email notifications (every 3 hours)...\n")
                    
                    # Listen for notifications
                    async for message in websocket:
                        data = json.loads(message)
                        await self.handle_webhook_notification(data)
                        
            except websockets.exceptions.WebSocketException as e:
                print(f"\n⚠️  Webhook connection lost: {e}")
                print("Retrying in 30 seconds...")
                await asyncio.sleep(30)
            except Exception as e:
                print(f"\n❌ Error: {e}")
                await asyncio.sleep(30)
    
    async def handle_webhook_notification(self, data: dict):
        """Handle different types of notifications from webhook"""
        notification_type = data.get('type')
        
        if notification_type == 'connected':
            print(f"✓ {data.get('message')}")
            next_check = data.get('next_check')
            if next_check:
                print(f"   Next check: {next_check}")
            print()
        
        elif notification_type == 'new_emails':
            await self.process_new_emails(data)
        
        elif notification_type == 'check_complete':
            print(f"\n✓ {data.get('message')} - {data.get('timestamp')}")
    
    async def process_new_emails(self, data: dict):
        """Process new emails with the agent when notified by webhook"""
        email_count = data.get('email_count', 0)
        timestamp = data.get('timestamp')
        emails = data.get('emails', [])
        
        print("\n" + "="*SEPARATOR_LENGTH)
        print(f"🔔 NEW EMAILS NOTIFICATION")
        print("="*SEPARATOR_LENGTH)
        print(f"Time: {timestamp}")
        print(f"Count: {email_count} new emails")
        print()
        
        # Display email summaries
        print("📧 Email Preview:")
        for i, email in enumerate(emails[:10], 1):  # Show first 10
            print(f"\n{i}. From: {email.get('from')}")
            print(f"   Subject: {email.get('subject')}")
            print(f"   Preview: {email.get('snippet')}...")
        
        if email_count > 10:
            print(f"\n... and {email_count - 10} more emails")
        
        print("\n" + "-"*SEPARATOR_LENGTH)
        
        # Activate agent to analyze
        print("\n🤖 Activating agent to analyze emails...\n")
        
        # Fetch full email details
        full_emails = []
        for email_summary in emails:
            try:
                email = self.gmail_tools.get_email(email_summary['id'])
                full_emails.append(email)
            except Exception as e:
                logger.error(f"Error fetching email {email_summary['id']}: {e}")
        
        # Create email list for agent
        email_list = "\n\n".join([
            f"{i}. From: {e.get('from')}\n"
            f"   Subject: {e.get('subject')}\n"
            f"   Snippet: {e.get('snippet', '')[:150]}..."
            for i, e in enumerate(full_emails, 1)
        ])
        
        # Ask agent to analyze
        user_query = f"""
I just received {email_count} new emails:

{email_list}

Please:
1. Categorize them (urgent/important/normal/spam)
2. Identify any that need my immediate attention
3. Suggest what I should do with each category
4. Ask me what actions I'd like to take

Be conversational and help me decide what to do.
"""
        
        # Create dependencies
        deps = GmailDeps(
            emails=full_emails,
            gmail_service=self.gmail_tools
        )
        
        # Run agent
        try:
            result = await self.agent.run(user_query, deps=deps)
            
            print("\n" + "="*SEPARATOR_LENGTH)
            print("🤖 AGENT ANALYSIS:")
            print("="*SEPARATOR_LENGTH)
            print(result.data)
            print("="*SEPARATOR_LENGTH + "\n")
            
            # Now wait for user input to take actions
            await self.interactive_mode(full_emails)
            
        except Exception as e:
            logger.error(f"Error running agent: {e}", exc_info=True)
            print(f"\n❌ Error analyzing emails: {e}")
    
    async def interactive_mode(self, emails: list):
        """Interactive mode where user can give commands to the agent"""
        print("\n💬 What would you like to do with these emails?")
        print("   (Type your command, or 'done' to finish)\n")
        
        while True:
            try:
                user_input = input("You: ")
                
                if not user_input.strip():
                    continue
                
                if user_input.lower() in ['done', 'exit', 'quit', 'finish']:
                    print("\n✓ Done processing this batch\n")
                    break
                
                # Create dependencies
                deps = GmailDeps(
                    emails=emails,
                    gmail_service=self.gmail_tools
                )
                
                # Run agent with user's command
                result = await self.agent.run(user_input, deps=deps)
                
                print(f"\nAgent: {result.data}\n")
                
            except KeyboardInterrupt:
                print("\n\n✓ Interrupted\n")
                break
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
                print(f"\n❌ Error: {e}\n")
    
    async def run(self):
        """Run the enhanced CLI"""
        print("\n" + "="*SEPARATOR_LENGTH)
        print("Gmail Agent - Enhanced CLI with Webhook Integration")
        print("="*SEPARATOR_LENGTH)
        print()
        print("This CLI connects to your webhook server and:")
        print("  • Receives notifications every 3 hours about new emails")
        print("  • Activates the agent to analyze them")
        print("  • Lets you interactively decide what to do")
        print()
        print(f"Thread ID: {THREAD_ID}")
        print("="*SEPARATOR_LENGTH + "\n")
        
        # Start webhook listener
        await self.connect_to_webhook()


async def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please set it in your .env file")
        return
    
    # Get webhook URL from environment or use default
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if webhook_url:
        print(f"Using webhook URL: {webhook_url}")
    else:
        print("WEBHOOK_URL not set - using local development URL")
        print("For production, set WEBHOOK_URL=wss://your-app.railway.app/ws/cli")
    
    # Create and run CLI
    cli = WebhookCLI(webhook_url=webhook_url)
    
    try:
        await cli.run()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        cli.running = False


if __name__ == "__main__":
    asyncio.run(main())

