"""FastAPI webhook server for Gmail notifications - Notifies local CLI"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

from tools.gmail_tools import GmailTools
from utils.logging import get_logger

# Load environment variables
load_dotenv()

# Initialize
app = FastAPI(title="Gmail Agent Webhook", version="1.0.0")
scheduler = AsyncIOScheduler()
logger = get_logger()

# Track last check time
last_check_time: Optional[datetime] = None

# Store active CLI WebSocket connections
active_cli_connections: List[WebSocket] = []


@app.on_event("startup")
async def startup_event():
    """Start the scheduler when the app starts"""
    logger.info("Starting Gmail Agent Webhook Server (CLI Notifier Mode)")
    
    # Start the scheduler
    scheduler.add_job(
        notify_cli_about_emails,
        trigger=IntervalTrigger(hours=3),
        id='email_check_notifier',
        name='Check emails and notify CLI every 3 hours',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started - will notify CLI every 3 hours")
    logger.info("CLIs can connect at: ws://your-domain/ws/cli")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    scheduler.shutdown()
    logger.info("Scheduler stopped")


async def notify_cli_about_emails():
    """
    Scheduled job that runs every 3 hours to:
    1. Check for new emails
    2. Notify connected local CLI to wake up and process them interactively
    """
    global last_check_time
    
    logger.info("="*60)
    logger.info(f"EMAIL CHECK TRIGGERED - {datetime.now()}")
    logger.info("="*60)
    
    try:
        # Initialize Gmail tools
        gmail_tools = GmailTools()
        
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
            
            # Notify CLI anyway (so they know we checked)
            await notify_connected_clis({
                "type": "check_complete",
                "email_count": 0,
                "timestamp": datetime.now().isoformat(),
                "message": "No new emails"
            })
            return
        
        logger.info(f"Found {len(emails)} new emails")
        
        # Prepare email data for CLI
        email_summaries = []
        for email in emails:
            email_summaries.append({
                "id": email.get('id'),
                "from": email.get('from', 'Unknown'),
                "subject": email.get('subject', 'No Subject'),
                "snippet": email.get('snippet', '')[:150]
            })
        
        # Notify all connected CLIs
        notification = {
            "type": "new_emails",
            "email_count": len(emails),
            "timestamp": datetime.now().isoformat(),
            "emails": email_summaries
        }
        
        logger.info(f"Notifying {len(active_cli_connections)} connected CLI(s)")
        await notify_connected_clis(notification)
        
        logger.info("Check completed successfully")
        
    except Exception as e:
        logger.error(f"Error checking emails: {e}", exc_info=True)
    
    logger.info("="*60 + "\n")


async def notify_connected_clis(message: dict):
    """Send notification to all connected local CLIs"""
    disconnected = []
    
    for websocket in active_cli_connections:
        try:
            await websocket.send_json(message)
            logger.info(f"Notification sent to CLI")
        except Exception as e:
            logger.warning(f"Failed to send to CLI: {e}")
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for ws in disconnected:
        active_cli_connections.remove(ws)


@app.websocket("/ws/cli")
async def cli_websocket(websocket: WebSocket):
    """WebSocket endpoint for local CLI to connect and receive email notifications"""
    await websocket.accept()
    active_cli_connections.append(websocket)
    logger.info(f"CLI connected. Total active CLIs: {len(active_cli_connections)}")
    
    # Send welcome message
    await websocket.send_json({
        "type": "connected",
        "message": "Connected to webhook server. You'll be notified every 3 hours about new emails.",
        "next_check": scheduler.get_jobs()[0].next_run_time.isoformat() if scheduler.get_jobs() else None
    })
    
    try:
        # Keep connection alive and listen for heartbeats
        while True:
            data = await websocket.receive_text()
            # Client can send heartbeat to keep alive
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        active_cli_connections.remove(websocket)
        logger.info(f"CLI disconnected. Remaining: {len(active_cli_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_cli_connections:
            active_cli_connections.remove(websocket)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Gmail Agent Webhook (CLI Notifier)",
        "mode": "Notifies local CLI to process emails interactively",
        "scheduler_running": scheduler.running,
        "connected_clis": len(active_cli_connections),
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
    Hit this to immediately check for emails and notify CLI.
    """
    logger.info("Manual trigger requested")
    background_tasks.add_task(notify_cli_about_emails)
    return {
        "status": "triggered",
        "message": "Email check started - will notify connected CLIs"
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

