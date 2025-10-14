# Webhook + CLI Integration Guide

This guide explains how to run your Gmail agent locally while having it triggered by the webhook server every 3 hours.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         Railway (Webhook Server)                    │
│  - Checks emails every 3 hours                      │
│  - Sends notification via WebSocket                 │
└──────────────┬──────────────────────────────────────┘
               │ WebSocket
               │ ws://your-app.railway.app/ws/cli
               ↓
┌─────────────────────────────────────────────────────┐
│         Your Laptop (Enhanced CLI)                  │
│  - Connects to webhook via WebSocket               │
│  - Receives email notifications                     │
│  - Activates LOCAL agent to process                │
│  - Asks YOU what to do interactively               │
└─────────────────────────────────────────────────────┘
```

## Benefits

✅ **Agent runs locally** - All processing on your machine  
✅ **Gmail credentials stay local** - Never uploaded to cloud  
✅ **Interactive** - Agent asks YOU what to do with emails  
✅ **Scheduled** - Webhook triggers every 3 hours automatically  
✅ **Always-on webhook** - Railway runs 24/7 for free  
✅ **CLI only when you want** - Run CLI when you're working  

---

## Setup

### 1. Deploy Webhook to Railway

```bash
# Already committed - just deploy to Railway
# Railway will run: uvicorn webhook_server:app --host 0.0.0.0 --port $PORT
```

**Environment variables needed on Railway:**
```
# NOT NEEDED - webhook just checks Gmail, doesn't process
# No OPENAI_API_KEY needed
# No GOOGLE_TOKEN_JSON needed

# Just for checking emails (or you can skip and only use push notifications)
GOOGLE_API_KEY=your-gmail-api-key-for-checking
```

Actually, even simpler - the webhook will use your Gmail API to check, but you can configure it to just use push notifications instead.

### 2. Run Enhanced CLI Locally

```bash
# Set webhook URL in .env
echo "WEBHOOK_URL=wss://your-app.railway.app/ws/cli" >> .env

# Run enhanced CLI
python main_with_webhook.py
```

---

## How It Works

### Every 3 Hours:

1. **Webhook checks Gmail** (on Railway)
2. **Finds new emails** (from last 3 hours)
3. **Sends notification to your CLI** via WebSocket
   ```json
   {
     "type": "new_emails",
     "email_count": 15,
     "emails": [
       {"from": "john@example.com", "subject": "Meeting..."},
       ...
     ]
   }
   ```
4. **Your CLI receives notification**
5. **Fetches full email details** (locally)
6. **Activates agent** (locally with your OpenAI key)
7. **Agent analyzes and asks you:**
   ```
   🤖 I found:
   - 3 urgent emails (from boss, client)
   - 8 normal emails
   - 4 newsletters
   
   What would you like to do?
   ```
8. **You respond interactively:**
   ```
   You: Archive the newsletters
   Agent: ✓ Archived 4 newsletters
   
   You: Show me the urgent ones
   Agent: Here are the 3 urgent emails...
   
   You: Draft a reply to the client
   Agent: ✓ Draft created. Want to review it?
   ```

---

## Usage Examples

### Example 1: Normal Flow

```bash
# Terminal 1: Run enhanced CLI
$ python main_with_webhook.py

Gmail Agent - Enhanced CLI with Webhook Integration
====================================================

🔌 Connecting to webhook server: wss://your-app.railway.app/ws/cli
✓ Connected to webhook server
⏰ Waiting for email notifications (every 3 hours)...

# 3 hours later...

====================================================
🔔 NEW EMAILS NOTIFICATION
====================================================
Time: 2025-10-14T14:00:00
Count: 12 new emails

📧 Email Preview:

1. From: boss@company.com
   Subject: Urgent: Q4 Report
   Preview: Hi, can you send the Q4 report by...

2. From: client@example.com
   Subject: Contract Review
   Preview: We need to discuss the contract...

3. From: newsletter@site.com
   Subject: Weekly Update
   Preview: Here's what happened this week...

... and 9 more emails

🤖 Activating agent to analyze emails...

====================================================
🤖 AGENT ANALYSIS:
====================================================

I've analyzed your 12 new emails:

**URGENT (2):**
1. Boss: Q4 Report needed ASAP
2. Client: Contract review discussion

**IMPORTANT (3):**
3. Sarah: Meeting confirmation for tomorrow
4. John: Project update needed
5. Alice: Budget approval required

**NORMAL (5):**
6-10. Various project updates and team messages

**SPAM/NEWSLETTERS (2):**
11-12. Marketing emails from newsletters

What would you like to do with these?
====================================================

💬 What would you like to do with these emails?
   (Type your command, or 'done' to finish)

You: Archive the newsletters and show me the urgent ones

Agent: ✓ Archived 2 newsletters

Here are the 2 urgent emails:

1. **From: boss@company.com**
   Subject: Urgent: Q4 Report
   
   "Hi, can you send the Q4 report by end of day? 
   We have the board meeting tomorrow morning."
   
2. **From: client@example.com**
   Subject: Contract Review
   
   "We need to discuss contract terms before signing.
   Can we schedule a call this week?"

Would you like to:
- Draft replies to these?
- Mark them for later?
- Take any other action?

You: Draft a reply to my boss saying I'll have it ready in 2 hours

Agent: ✓ Draft created

**To:** boss@company.com
**Subject:** Re: Urgent: Q4 Report

"I'll have the Q4 report ready and sent to you within 
the next 2 hours, well before end of day."

Draft saved. You can review and send it from Gmail.

You: Perfect. Mark the client email as important and remind me tomorrow

Agent: ✓ Marked email as important
✓ Added to-do: "Follow up with client about contract"

You: done

✓ Done processing this batch

⏰ Waiting for email notifications (every 3 hours)...
```

---

## Configuration

### Change Check Frequency

Edit `webhook_server.py`:

```python
scheduler.add_job(
    notify_cli_about_emails,
    trigger=IntervalTrigger(minutes=30),  # Every 30 minutes instead of 3 hours
    ...
)
```

### Manual Trigger (Testing)

```bash
# Trigger immediate check (don't wait 3 hours)
curl -X POST https://your-app.railway.app/trigger-now
```

Your CLI will receive notification immediately.

---

## Running Both Modes

You can run both the original CLI and the webhook-enhanced CLI:

### Original CLI (Manual, No Webhook)
```bash
python main.py
```
Use when you want full manual control.

### Enhanced CLI (Webhook-Triggered)
```bash
python main_with_webhook.py
```
Use when you want automatic notifications every 3 hours.

---

## Deployment Checklist

- [ ] Deploy `webhook_server.py` to Railway
- [ ] Set `WEBHOOK_URL` in local `.env`
- [ ] Install `websockets`: `pip install websockets`
- [ ] Run `python main_with_webhook.py`
- [ ] Test with `/trigger-now` endpoint
- [ ] Verify connection in Railway logs

---

## Troubleshooting

### "Connection refused"

**Problem:** Can't connect to webhook server  
**Solution:** 
1. Make sure webhook is deployed to Railway
2. Check `WEBHOOK_URL` is correct (use `wss://` for HTTPS)
3. Verify Railway app is running

### "Disconnects frequently"

**Problem:** WebSocket keeps disconnecting  
**Solution:**
1. CLI auto-reconnects after 30 seconds
2. This is normal - Railway may restart occasionally
3. Connection will resume automatically

### "No notifications received"

**Problem:** CLI connected but no emails  
**Solution:**
1. Check Railway logs to see if scheduler is running
2. Manually trigger: `curl -X POST https://your-app.railway.app/trigger-now`
3. Verify you have new emails in the time window

---

## Benefits vs Pure Cloud Deployment

| Aspect | Webhook + Local CLI | Pure Cloud |
|--------|-------------------|------------|
| **Agent Processing** | Local (your laptop) | Cloud (Railway) |
| **Credentials** | Stay local | Need to upload |
| **Interactivity** | Full - agent asks you | None - agent decides |
| **Cost** | $0 | $0 (free tier) |
| **Always-On** | Only when you run CLI | 24/7 |
| **Best For** | Personal use, interactive | Fully automated |

---

## What This Solves

✅ **"I want the agent to run on my laptop but be triggered automatically"** - YES  
✅ **"I don't want to upload Gmail credentials to the cloud"** - Credentials stay local  
✅ **"I want to approve actions before they happen"** - Agent asks you first  
✅ **"I want to be notified about new emails every X hours"** - Webhook does this  
✅ **"I want full control"** - Everything runs locally, you decide  

---

## Next Steps

1. Deploy webhook to Railway
2. Run `python main_with_webhook.py`
3. Test with manual trigger
4. Wait for first 3-hour notification
5. Enjoy interactive email management!

