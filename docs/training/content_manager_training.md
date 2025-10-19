
#### File: `docs/training/content_manager_training.md`

```markdown
# Content Manager Training Guide

## Role Overview
As a Content Manager, you are responsible for:
- Maintaining accurate and up-to-date FAQ content
- Reviewing student questions and identifying knowledge gaps
- Updating college information (fees, dates, policies)
- Ensuring content quality and clarity

## Access Instructions

### Supabase Dashboard Access
1. Go to: `https://supabase.com/dashboard`
2. Log in with your college credentials
3. Select your project: "College WhatsApp Bot"
4. Navigate to: **Table Editor** → **knowledge_base_documents**

### Content Management Interface
The `knowledge_base_documents` table contains:
- **title**: Document title (e.g., "Tuition Fees 2025")
- **content**: Full text content (Markdown supported)
- **language**: Language code (en, tr, ar)
- **document_type**: Category (faq, policy, guide, etc.)
- **is_active**: Toggle to enable/disable content
- **version**: Version number (increment when updating)

## Content Update Process

### Step 1: Identify Content Needs
- Review **Top Questions** in admin dashboard
- Check **Failed Queries** (responses containing "I don't know")
- Monitor student feedback and complaints
- Stay updated on college policy changes

### Step 2: Prepare Content Updates
**Best Practices**:
- Use clear, simple language
- Include specific numbers and dates
- Provide contact information for complex topics
- Format with bullet points for readability
- Keep responses under 200 words when possible

**Content Structure**:

[Question]: What are the tuition fees for international students?

[Answer]: For the 2025-2026 academic year, undergraduate tuition is $8,500 per semester for full-time students (12-18 credit hours). Graduate tuition is $9,500 per semester. Additional fees may apply for specific programs or services.

[Contact]: For detailed fee breakdowns, contact the Bursar's Office at bursar@college.edu or +1-XXX-XXX-XXXX.