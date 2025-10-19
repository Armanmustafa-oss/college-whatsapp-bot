# Monitoring Guide

## Dashboard URL Structure

- **Main Dashboard:** `https://your-dashboard.railway.app`
- **Sentry Errors:** `https://sentry.io/organizations/your-org/issues`
- **Railway Metrics:** `https://railway.app/project/your-project`
- **Supabase DB:** `https://supabase.com/dashboard/project/your-project`

## Alert Configuration

### Email Alerts (configured in Sentry):
- Error rate > 5% for 5 minutes → Email IT team
- P95 response time > 3s for 10 minutes → Email on-call
- Database connection errors → Email + SMS to IT Director
- Cost exceeds $150/month → Email finance team

### Key Metrics to Watch

| Metric | Healthy Range | Warning Threshold | Critical Threshold |
|--------|---------------|-------------------|-------------------|
| Response Time (P95) | < 2s | > 3s | > 5s |
| Error Rate | < 1% | > 3% | > 5% |
| Quality Score | > 0.80 | < 0.70 | < 0.50 |
| Uptime | > 99% | < 98% | < 95% |
| Messages/Day | 30-100 | < 10 or > 500 | < 5 or > 1000 |