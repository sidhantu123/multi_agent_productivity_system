# Webhook Server Setup Guide

This guide will help you deploy the Gmail Agent webhook server to Railway's free tier, which will automatically process your emails every 3 hours.

## Architecture

```
┌─────────────────────────────────────┐
│     Scheduled Job (Every 3 hours)   │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│    Fetch New Emails (Gmail API)     │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Activate LangGraph Gmail Agent    │
│   - Categorize emails                │
│   - Identify urgent items            │
│   - Auto-archive spam/newsletters    │
│   - Provide summary & actions        │
└─────────────────────────────────────┘
```

## Deployment Steps

### 1. Prerequisites

- GitHub account
- Railway account ([railway.app](https://railway.app)) - Free tier available
- Your Gmail Agent repository pushed to GitHub

### 2. Push Code to GitHub

```bash
# Commit webhook changes
git add .
git commit -m "Add webhook server for scheduled email processing"
git push origin main
```

### 3. Deploy to Railway

#### Option A: Via Railway Dashboard (Easiest)

1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Click "Deploy from GitHub repo"
4. Select your `multi_agent_assistants` repository
5. Railway will auto-detect Python and deploy

#### Option B: Via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Deploy
railway up
```

### 4. Configure Environment Variables

In Railway Dashboard → Your Project → Variables, add:

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional (for LangSmith tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=Gmail-Agent-Webhook
```

**Important:** Railway needs access to your Gmail credentials. You have two options:

#### Option A: Gmail Service Account (Recommended for Production)
- Create a service account in Google Cloud
- Grant it access to your Gmail
- Add service account JSON as environment variable

#### Option B: OAuth Token (Simpler for Personal Use)
- Generate `google_token.json` locally
- Copy the token contents to Railway as env variable `GOOGLE_TOKEN_JSON`
- Update code to load from env variable instead of file

### 5. Add Gmail Credentials to Railway

Since `google_credentials.json` and `google_token.json` are gitignored, you need to add them as environment variables:

```bash
# In Railway Dashboard → Variables, add:
GOOGLE_CREDENTIALS_JSON='{"installed": {...}}'  # Paste your credentials.json content
GOOGLE_TOKEN_JSON='{"token": "...", ...}'        # Paste your token.json content
```

Then update `tools/gmail_tools/core.py` to load from environment variables when in production:

```python
import json

# In GmailTools.__init__
if os.getenv('RAILWAY_ENVIRONMENT'):  # Detect Railway
    # Load from environment variables
    creds_data = json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON'))
    token_data = json.loads(os.getenv('GOOGLE_TOKEN_JSON'))
    # Use these instead of files
```

### 6. Verify Deployment

After deployment, Railway will give you a URL like: `https://your-app.railway.app`

**Test endpoints:**

```bash
# Health check
curl https://your-app.railway.app/

# Check scheduler status
curl https://your-app.railway.app/status

# Manually trigger a batch (for testing)
curl -X POST https://your-app.railway.app/trigger-now
```

**Expected response:**
```json
{
  "status": "ok",
  "service": "Gmail Agent Webhook",
  "scheduler_running": true,
  "last_check": "2025-10-14T10:00:00",
  "next_run": "2025-10-14T13:00:00"
}
```

### 7. View Logs

In Railway Dashboard → Your Project → Deployments → View Logs

You should see:
```
INFO: Starting Gmail Agent Webhook Server
INFO: Scheduler started - will run every 3 hours
INFO: EMAIL BATCH PROCESSOR STARTED - 2025-10-14 10:00:00
INFO: Found 15 new emails
INFO: Activating agent to process emails...
INFO: AGENT ANALYSIS:
...
```

## How It Works

### Every 3 Hours:

1. **Fetch Emails**: Searches Gmail for emails from the last 3 hours
2. **Agent Analysis**: Sends all emails to your LangGraph agent
3. **Categorization**: Agent categorizes as important/normal/spam
4. **Actions**: Agent automatically:
   - Archives newsletters
   - Unsubscribes from spam
   - Identifies urgent emails
   - Provides summaries
5. **Logging**: All actions logged in Railway dashboard

### Manual Triggers:

You can also trigger processing manually:

```bash
# Trigger immediate processing
curl -X POST https://your-app.railway.app/trigger-now
```

## Customization

### Change Schedule Frequency

Edit `webhook_server.py`:

```python
# Every 1 hour
scheduler.add_job(
    process_email_batch,
    trigger=IntervalTrigger(hours=1),  # Change this
    ...
)

# Every 30 minutes
scheduler.add_job(
    process_email_batch,
    trigger=IntervalTrigger(minutes=30),  # Or this
    ...
)
```

### Customize Agent Behavior

Edit the `user_query` in `process_email_batch()`:

```python
user_query = f"""
You have {len(emails)} new emails to review:

{email_list}

Custom instructions:
- Auto-delete anything from unsubscribe@company.com
- Always flag emails from boss@company.com as urgent
- Archive all emails with "newsletter" in subject
- Create draft replies for client emails
"""
```

## Gmail Push Notifications (Optional - Real-time)

For instant notifications instead of 3-hour batches:

### 1. Set up Google Cloud Pub/Sub

```bash
# Create Pub/Sub topic
gcloud pubsub topics create gmail-notifications

# Subscribe Gmail to topic
# (Use Gmail API watch endpoint)
```

### 2. Point Pub/Sub to your webhook

Configure Pub/Sub push subscription to:
```
https://your-app.railway.app/webhook/gmail
```

Now emails trigger webhook immediately instead of on schedule.

## Monitoring

### Check Scheduler Status

```bash
curl https://your-app.railway.app/status
```

### View Recent Runs

Railway Dashboard → Logs → Filter by "EMAIL BATCH PROCESSOR"

### Get Next Run Time

```bash
curl https://your-app.railway.app/ | jq .next_run
```

## Troubleshooting

### "No new emails found" every run

- Check your Gmail API credentials are correct
- Verify Gmail API is enabled in Google Cloud Console
- Check Railway logs for authentication errors

### Agent not running

- Verify `OPENAI_API_KEY` is set in Railway environment variables
- Check Railway logs for errors
- Ensure all dependencies are in `requirements.txt`

### Scheduler not running

- Check Railway logs on startup
- Verify Railway service isn't sleeping (free tier sleeps after inactivity)
- Use Railway "Keep Alive" feature or ping endpoint every 10 minutes

### Gmail credentials issues

- Make sure credentials are added as environment variables
- Update code to load from env vars instead of files
- Regenerate token if expired

## Cost

**Railway Free Tier:**
- $5 free credit per month
- 500 hours execution time
- Should be plenty for running this webhook 24/7

**This webhook uses:**
- ~0.01 hours per 3-hour batch = ~0.08 hours/day = ~2.4 hours/month
- Well within free tier limits

## Next Steps

1. Deploy to Railway
2. Monitor first few runs in logs
3. Customize agent prompts for your needs
4. Optional: Add Gmail push notifications for real-time processing
5. Optional: Add notification service (Slack/SMS) to alert you of important emails

## Support

- Railway Docs: https://docs.railway.app
- Gmail API Docs: https://developers.google.com/gmail/api
- FastAPI Docs: https://fastapi.tiangolo.com

