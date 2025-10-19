# Incident Response Plan

## Severity Levels

### CRITICAL (P0): Bot completely down, no responses
- **Response Time:** Immediate (15 minutes)
- **Escalation:** Call on-call engineer + IT Director

### HIGH (P1): Degraded service (>50% errors or >10s response time)
- **Response Time:** 1 hour
- **Escalation:** Email IT team + on-call engineer

### MEDIUM (P2): Isolated issues (specific language not working, minor errors)
- **Response Time:** 4 hours
- **Escalation:** Email IT team

### LOW (P3): Cosmetic issues (dashboard display bug, minor typo)
- **Response Time:** 24 hours
- **Escalation:** Log ticket, address in next sprint

## Emergency Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| System Developer | [Your Email] | Mon-Fri 9-5 |
| Railway Support | support@railway.app | 24/7 (paid plan) |
| Twilio Support | +1-XXX | 24/7 |
| Groq API Support | support@groq.com | Business hours |

## Common Issues & Fixes

### Issue 1: Bot Not Responding

**Symptoms:** Students report no reply to messages

**Diagnosis:**
```bash
# Check if Railway service is running
curl https://your-bot.railway.app/health
# Expected response: {"status": "healthy"}