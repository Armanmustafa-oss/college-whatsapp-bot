# Content Management Guide

## How to Update FAQ Content

### Option A: Update via Supabase Dashboard (Recommended)

1. Log into Supabase: `https://supabase.com/dashboard`
2. Navigate to: `knowledge_base_documents` table
3. Find the document you want to update
4. Click "Edit" → Update `content` field
5. Update `last_modified` timestamp
6. Increment `version` number
7. Click "Save"

**The bot will automatically use updated content within 5 minutes.**

### Option B: Upload New PDF

1. Prepare your PDF with updated information
2. Upload to: `/data/college_docs/` folder in GitHub repository
3. The bot will automatically reindex on next restart
4. Verify in dashboard that new content appears

## Content Best Practices

### ✅ DO:
- Use simple, clear language
- Include specific numbers (dates, fees, deadlines)
- Provide contact information for complex questions
- Update seasonal content (registration dates, holidays)

### ❌ DON'T:
- Use jargon or abbreviations without explanation
- Include outdated information
- Add sensitive student data
- Use complex sentence structures (bot may misinterpret)

## Adding New Languages

Currently supported: English, Turkish, Arabic

To add a new language (e.g., Spanish):

1. Translate your knowledge base documents
2. Add language code to configuration: `SUPPORTED_LANGUAGES = ['en', 'tr', 'ar', 'es']`
3. Update prompt templates in `prompts.py`
4. Test with native speaker
5. Deploy update

**Estimated time:** 4-6 hours for basic setup + translation time