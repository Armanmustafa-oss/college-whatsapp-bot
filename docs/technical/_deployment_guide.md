# Deployment Guide

## Initial Deployment

### 1. Fork GitHub Repository
```bash
git clone https://github.com/yourusername/college-whatsapp-bot
cd college-whatsapp-bot

### 2. Configure Environment Variables
Create .env file:

GROQ_API_KEY=your_groq_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
SENTRY_DSN=your_sentry_dsn
ENVIRONMENT=production

3. Deploy to Railway

# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

4. Configure Twilio Webhook

Go to Twilio Console
Navigate to WhatsApp Sandbox/Number
Set webhook URL: https://your-app.railway.app/webhook
Method: POST

5. Verify Deployment

curl https://your-app.railway.app/health
# Should return: {"status": "healthy"}

6. Update Deployment

git pull origin main
railway up