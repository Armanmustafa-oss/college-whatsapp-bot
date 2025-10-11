# Emergency Runbook

## 1. Bot Not Responding
- Check Railway logs: `railway logs`
- Verify Twilio webhook URL: must be `https://bot.up.railway.app/webhook`
- Restart service: Railway UI → “Restart”

## 2. Dashboard Down
- Check if Supabase vars are set in Dashboard service
- Re-deploy dashboard

## 3. Wrong Answers
- Rebuild knowledge base: delete `chroma_db/` and restart bot
- Add missing synonyms in `semantic_enhancer.py`