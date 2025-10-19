
#### File: `docs/technical/4_database_schema.md`

```markdown
# Database Schema

## Core Tables

### conversations
Stores every student-bot interaction with full metrics.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Unique conversation ID |
| created_at | TIMESTAMPTZ | When conversation started |
| phone_hash | VARCHAR(64) | SHA-256 hash of phone number |
| message_text | TEXT | Student's question |
| bot_response | TEXT | Bot's answer |
| language | VARCHAR(10) | Language code (en/tr/ar) |
| response_time | INTEGER | Response time in milliseconds |
| quality_score | DECIMAL(3,2) | 0.00-1.00 quality rating |
| had_fallback | BOOLEAN | True if bot used generic response |
| documents_retrieved | INTEGER | Number of RAG documents used |

### user_analytics
Aggregated user behavior metrics updated in real-time via triggers.

| Column | Type | Description |
|--------|------|-------------|
| phone_hash | VARCHAR(64) | Unique user identifier |
| first_interaction | TIMESTAMPTZ | First message timestamp |
| last_interaction | TIMESTAMPTZ | Last message timestamp |
| total_messages | INTEGER | Total messages sent |
| engagement_score | DECIMAL(3,2) | 0.00-1.00 engagement rating |

### question_categories
Predefined question categories for auto-classification.

| Column | Type | Description |
|--------|------|-------------|
| category_name | VARCHAR(100) | Category name (e.g., "admissions") |
| keywords | TEXT[] | Array of keywords for auto-classification |
| priority_level | VARCHAR(20) | high/medium/low |
| requires_human | BOOLEAN | True if needs human support |

## Materialized Views

### daily_metrics
Daily aggregated metrics for fast dashboard loading.

### hourly_patterns
Hourly message patterns for capacity planning.

### top_questions
Most frequently asked questions (updated daily).