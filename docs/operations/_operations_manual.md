# Operations Manual - Daily Checklist

## Morning Routine (5 minutes)

### 1. Check System Health Dashboard
- Navigate to: `https://your-dashboard.railway.app`
- Verify all services show green status
- Review overnight message volume (should be 10-50 messages)

### 2. Review Error Logs
- Check Sentry dashboard: `https://sentry.io/your-project`
- Investigate any errors marked "high priority"
- Most errors auto-resolve; only escalate if pattern emerges

### 3. Verify Bot Responsiveness
- Send test message to WhatsApp bot: `+1-XXX-XXX-XXXX`
- Expected response time: < 3 seconds
- If no response in 10 seconds, check Railway deployment status

## Weekly Tasks

**Monday Morning:**
- Review weekly analytics report (auto-emailed)
- Check top 10 questions for any new trends
- Verify data retention policy compliance (auto-deletes after 90 days)

**Wednesday:**
- Review cost usage on Railway dashboard
- Expected monthly: $85 ± $10
- Alert if costs exceed $120 in any week

**Friday:**
- Refresh dashboard materialized views (automatic, verify completion)
- Export weekly report for stakeholders
- Review any pending content updates

## Monthly Tasks

1. **Performance Review**
   - Export monthly metrics from Supabase
   - Calculate: message volume, unique users, avg response time
   - Prepare report for leadership

2. **Cost Optimization**
   - Review Groq API usage
   - Check for unused database rows
   - Archive old conversations (>90 days)

3. **Content Audit**
   - Review top 20 unanswered questions
   - Update knowledge base with new information
   - Remove outdated content (e.g., last year's fees)