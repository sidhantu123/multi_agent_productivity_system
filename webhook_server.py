"""FastAPI webhook server for Gmail notifications with scheduled batch processing"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

from tools.gmail_tools import GmailTools
from agents.gmail_agent import get_gmail_agent, get_gmail_tools
from tools.gmail_tools.core import GmailDeps
from utils.logging import get_logger

# Load environment variables
load_dotenv()

# Initialize
app = FastAPI(title="Gmail Agent Webhook", version="1.0.0")
scheduler = AsyncIOScheduler()
logger = get_logger()

# Track last check time
last_check_time: Optional[datetime] = None


@app.on_event("startup")
async def startup_event():
    """Start the scheduler when the app starts"""
    logger.info("Starting Gmail Agent Webhook Server")
    
    # Start the scheduler
    scheduler.add_job(
        process_email_batch,
        trigger=IntervalTrigger(hours=3),
        id='email_batch_processor',
        name='Process email batch every 3 hours',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started - will run every 3 hours")
    
    # Run immediately on startup (optional - comment out if you don't want this)
    asyncio.create_task(process_email_batch())


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    scheduler.shutdown()
    logger.info("Scheduler stopped")


async def process_email_batch():
    """
    Scheduled job that runs every 3 hours to:
    1. Fetch all new emails from the past 3 hours
    2. Activate the agent to analyze and process them
    3. Agent decides what to do with each email
    """
    global last_check_time
    
    logger.info("="*60)
    logger.info(f"EMAIL BATCH PROCESSOR STARTED - {datetime.now()}")
    logger.info("="*60)
    
    try:
        # Initialize Gmail tools
        gmail_tools = get_gmail_tools()
        
        # Build search query for last 3 hours
        if last_check_time:
            # Search for emails since last check
            time_str = last_check_time.strftime('%Y/%m/%d')
            query = f"after:{time_str}"
            logger.info(f"Searching for emails after: {time_str}")
        else:
            # First run - get last 3 hours
            query = "newer_than:3h"
            logger.info("First run - searching for emails from last 3 hours")
        
        # Fetch emails
        emails = gmail_tools.search_emails(query=query, max_results=50)
        last_check_time = datetime.now()
        
        if not emails:
            logger.info("No new emails found")
            logger.info("="*60)
            return
        
        logger.info(f"Found {len(emails)} new emails")
        
        # Create agent
        agent = get_gmail_agent()
        
        # Prepare email summary for agent
        email_summaries = []
        for i, email in enumerate(emails, 1):
            summary = (
                f"{i}. From: {email.get('from', 'Unknown')}\n"
                f"   Subject: {email.get('subject', 'No Subject')}\n"
                f"   Snippet: {email.get('snippet', '')[:100]}...\n"
                f"   ID: {email.get('id')}"
            )
            email_summaries.append(summary)
        
        email_list = "\n\n".join(email_summaries)
        
        # Create prompt for agent
        user_query = f"""
You have {len(emails)} new emails to review from the last 3 hours:

{email_list}

Please analyze these emails and:
1. Categorize them (important, normal, spam/newsletter)
2. Identify any urgent emails that need immediate attention
3. For newsletters/spam: automatically archive or unsubscribe
4. For important emails: provide a brief summary and suggested action
5. For normal emails: brief summary

Provide a structured report of your analysis and actions taken.
"""
        
        logger.info("Activating agent to process emails...")
        
        # Create dependencies
        deps = GmailDeps(
            emails=emails,
            gmail_service=gmail_tools
        )
        
        # Run agent
        result = await agent.run(user_query, deps=deps)
        
        # Log agent's response
        logger.info("\n" + "="*60)
        logger.info("AGENT ANALYSIS:")
        logger.info("="*60)
        logger.info(result.data)
        logger.info("="*60)
        
        # Log tool calls made by agent
        if hasattr(result, 'all_messages'):
            tool_calls = [
                msg for msg in result.all_messages() 
                if msg.get('role') == 'tool' or 
                   (msg.get('kind') == 'request' and msg.get('parts'))
            ]
            if tool_calls:
                logger.info(f"\nAgent made {len(tool_calls)} tool calls")
        
        logger.info("Batch processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing email batch: {e}", exc_info=True)
    
    logger.info("="*60 + "\n")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Gmail Agent Webhook",
        "scheduler_running": scheduler.running,
        "last_check": last_check_time.isoformat() if last_check_time else None,
        "next_run": scheduler.get_jobs()[0].next_run_time.isoformat() if scheduler.get_jobs() else None
    }


@app.post("/webhook/gmail")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Gmail push notification webhook endpoint.
    Google Cloud Pub/Sub will POST here when new emails arrive.
    
    For now, this just triggers an immediate batch process.
    In production, you'd verify the Pub/Sub signature.
    """
    try:
        data = await request.json()
        logger.info(f"Received Gmail webhook notification: {data}")
        
        # Trigger immediate batch processing in background
        background_tasks.add_task(process_email_batch)
        
        return JSONResponse(
            status_code=200,
            content={"status": "accepted", "message": "Processing in background"}
        )
    except Exception as e:
        logger.error(f"Error handling webhook: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


@app.post("/trigger-now")
async def trigger_now(background_tasks: BackgroundTasks):
    """
    Manual trigger endpoint for testing.
    Hit this to immediately run the batch processor.
    """
    logger.info("Manual trigger requested")
    background_tasks.add_task(process_email_batch)
    return {
        "status": "triggered",
        "message": "Email batch processing started"
    }


@app.get("/status")
async def status():
    """Get detailed status of the scheduler and last run"""
    jobs = scheduler.get_jobs()
    job_info = []
    
    for job in jobs:
        job_info.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "scheduler_running": scheduler.running,
        "jobs": job_info,
        "last_check_time": last_check_time.isoformat() if last_check_time else None,
        "current_time": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    # For local development
    uvicorn.run(
        "webhook_server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )

