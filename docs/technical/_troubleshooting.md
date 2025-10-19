# Troubleshooting Guide

## Common Issues

### Issue 1: 502 Bad Gateway on Dashboard

**Cause**: Dashboard service can't connect to Supabase or has missing columns.

**Solution**:
1. Verify Supabase URL and key in Railway environment variables
2. Run `SELECT * FROM conversations LIMIT 1;` in Supabase SQL Editor
3. Ensure all required columns exist (quality_score, response_time, etc.)
4. Redeploy dashboard service

### Issue 2: Bot Says "I Don't Know" Too Often

**Cause**: Knowledge base not loaded or semantic search failing.

**Solution**:
1. Check ChromaDB logs for errors
2. Verify PDF files exist in `/data/college_docs/`
3. Test semantic search with known queries
4. Update synonym mapping in `semantic_enhancer.py`

### Issue 3: Slow Response Times

**Cause**: Groq API rate limiting or database performance issues.

**Solution**:
1. Check Groq API usage dashboard
2. Verify Supabase connection pool settings
3. Add Redis caching for frequent queries
4. Optimize ChromaDB index performance

### Issue 4: Language Detection Failing

**Cause**: Language detection logic needs improvement.

**Solution**:
1. Review `detect_language()` function in `ai_service.py`
2. Add more language-specific keywords
3. Consider using `langdetect` library for better accuracy
4. Test with native speakers of each language

## Debugging Commands

### Check Railway Logs
```bash
railway logs --service bot-service
railway logs --service dashboard-service

## Test Supabase Connection

from supabase import create_client
supabase = create_client("your_url", "your_key")
result = supabase.table('conversations').select('*').limit(1).execute()
print(result.data)

## Test Groq API

from groq import Groq
client = Groq(api_key="your_key")
completion = client.chat.completions.create(
    model="mixtral-8x7b-32768",
    messages=[{"role": "user", "content": "Hello"}]
)
print(completion.choices[0].message.content)