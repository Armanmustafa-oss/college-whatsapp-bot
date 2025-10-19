
---

### 🔹 Step 5: Create Compliance Documents

#### File: `docs/compliance/data_retention_policy.md`

```markdown
# Data Retention Policy

## Policy Statement
All conversation data will be automatically deleted after 90 days to comply with GDPR and minimize data storage risks.

## Data Categories and Retention Periods

| Data Type | Retention Period | Deletion Method |
|-----------|------------------|-----------------|
| Conversation logs | 90 days | Automated cron job |
| User analytics | 2 years | Manual review required |
| Error logs | 365 days | Automated cleanup |
| System metrics | 5 years | Archival storage |

## Implementation Details

### Automated Cleanup
A scheduled job runs every Sunday at 3 AM to delete conversations older than 90 days:

```sql
SELECT cleanup_old_conversations(90);

Manual Deletion Requests:
**Students can request immediate data deletion by**:
Sending "DELETE MY DATA" to the WhatsApp bot
Emailing privacy@college.edu with phone number
Calling the IT help desk

## Verification Process:

**All deletion requests are verified through**:
Phone number hash matching
Identity verification questions
Manager approval for bulk requests

## Compliance Verification:

Monthly audit of deletion logs
Quarterly review of retention policy
Annual third-party security assessment