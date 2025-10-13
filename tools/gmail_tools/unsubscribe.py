"""Gmail tool: unsubscribe_from_email"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


async def unsubscribe_from_email(ctx: RunContext[GmailDeps], email_number: int) -> str:
    """
    Unsubscribe from marketing emails using standard unsubscribe methods.
    
    This tool intelligently handles different unsubscribe mechanisms:
    - One-Click Unsubscribe (RFC 8058): Automatically executes (safe)
    - HTTP/HTTPS Links: Provides link for user to click
    - Mailto: Creates draft unsubscribe email for user to send
    
    Args:
        email_number: The number of the email from the most recent list
    
    Returns:
        Status of unsubscribe attempt with instructions if needed
    """
    emails = ctx.deps.emails
    
    if not emails:
        return "No emails in context. Please list emails first using list_emails or search_emails."
    
    if email_number < 1 or email_number > len(emails):
        return f"Invalid email number. Please choose between 1 and {len(emails)}."
    
    email_id = emails[email_number - 1]['id']
    email_from = emails[email_number - 1]['from']
    email_subject = emails[email_number - 1]['subject']
    
    # Get unsubscribe information
    unsub_info = ctx.deps.gmail_service.get_unsubscribe_info(email_id)
    
    if not unsub_info:
        return (
            f"No unsubscribe mechanism found in this email.\n\n"
            f"From: {email_from}\n"
            f"Subject: {email_subject}\n\n"
            f"This email doesn't appear to have standard unsubscribe links. "
            f"You may need to contact the sender directly or check their website."
        )
    
    result = [
        f"Found unsubscribe options for:",
        f"From: {email_from}",
        f"Subject: {email_subject}",
        ""
    ]
    
    # Track what we've done
    auto_executed = False
    manual_steps = []
    
    # Process each unsubscribe method
    for i, method in enumerate(unsub_info['methods'], 1):
        if method.get('one_click') and not method['requires_confirmation']:
            # One-Click Unsubscribe - Safe to automate
            result.append(f"Method {i}: One-Click Unsubscribe (Automatic)")
            
            success = ctx.deps.gmail_service.unsubscribe_one_click(
                url=method['url'],
                post_data=method.get('post_data', 'List-Unsubscribe=One-Click')
            )
            
            if success:
                result.append("  Status: Successfully unsubscribed!")
                auto_executed = True
            else:
                result.append("  Status: Failed to unsubscribe automatically")
                result.append(f"  Fallback: Visit {method['url']}")
                manual_steps.append(('http', method['url']))
        
        elif method['type'] == 'mailto':
            # Mailto unsubscribe - Create draft email
            result.append(f"Method {i}: Email Unsubscribe")
            result.append(f"  To: {method['address']}")
            
            # Create a draft unsubscribe email
            draft_id = ctx.deps.gmail_service.create_draft(
                to=method['address'],
                subject="Unsubscribe",
                body="Please unsubscribe me from this mailing list."
            )
            
            if draft_id:
                result.append(f"  Action: Created draft email (ID: {draft_id})")
                result.append(f"  Next Step: Review and send the draft from Gmail")
                manual_steps.append(('mailto', method['address']))
            else:
                result.append(f"  Action: Failed to create draft")
                result.append(f"  Manual Step: Send email to {method['address']}")
                manual_steps.append(('mailto', method['address']))
        
        elif method['type'] == 'http':
            # HTTP/HTTPS link - Provide to user
            result.append(f"Method {i}: Web Link")
            result.append(f"  URL: {method['url']}")
            
            if method.get('found_in') == 'body':
                result.append(f"  Source: Found in email body")
            else:
                result.append(f"  Source: List-Unsubscribe header (trusted)")
            
            result.append(f"  Action Required: Click the link above to unsubscribe")
            manual_steps.append(('http', method['url']))
    
    # Summary
    result.append("")
    result.append("=" * 60)
    
    if auto_executed:
        result.append("AUTOMATED: One-click unsubscribe executed successfully!")
        if manual_steps:
            result.append("Note: Additional manual steps available above if needed.")
    elif manual_steps:
        result.append("ACTION REQUIRED: Please complete the steps above to unsubscribe.")
        result.append("These methods require manual action for security.")
    
    return "\n".join(result)

