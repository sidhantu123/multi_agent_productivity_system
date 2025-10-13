"""Gmail tool: get_labels"""

from pydantic_ai import RunContext
from tools.gmail_tools.core import GmailDeps


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
