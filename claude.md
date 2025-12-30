# Claude Instructions: Life Admin System

## What This System Is

A long-lived document capture system for family life administration. Documents are the source of truth. Capture happens with zero friction and zero decision-making. AI assists, humans decide.

## Core Principles (Never Violate These)

1. **Zero decision-making at intake** - If it's life admin, it goes in. No questions. No categorization. No filing.
2. **Documents are source of truth** - Never hide, replace, or obscure the original document.
3. **One-way data flow** - Intake → Archive → Understanding → Insight. No reversals.
4. **Longevity over novelty** - Build for 10-20+ year lifespan. No trendy features.
5. **Simple enough for family** - Non-technical users must understand it.
6. **AI assists, humans decide** - AI generates summaries and insights. Humans make all decisions.
7. **No feature bloat** - Reject anything that doesn't serve the core mission.

## What This Is NOT

- Not a filing system (no folders, no categories)
- Not a productivity tool
- Not a budgeting or finance tracker
- Not a task manager
- Not a replacement for specialized tools

## Architecture Layers

```
Intake → Archive → Understanding → Insight
```

- **Intake**: Upload with zero friction
- **Archive**: Permanent storage (R2 + SQLite metadata)
- **Understanding**: AI summaries, search, retrieval
- **Insight**: Future patterns, reminders, review windows

## When Working on This Codebase

### Always Do
- Read the comprehensive docs in `/docs/` before making changes
- Maintain the zero-friction upload experience
- Keep documents as permanent source of truth
- Follow the one-way data flow rule
- Test with the mindset: "Could a non-technical family member use this?"
- **Keep `/docs/99-build-log.md` updated** - Document what was built, what worked, what failed, resolution, and notes. This is critical for future understanding and legacy handover.
- Preserve data portability (no vendor lock-in)
- **Call out principle violations** - Actively warn if anything strays from the core ethos

### Never Do
- Add categorization, tagging, or filing at intake
- Hide or replace original documents
- Add features that require decision-making during upload
- Build anything that creates vendor lock-in
- Add complexity that obscures the core purpose
- Implement budgeting, spend tracking, or productivity features
- Make AI decisions on behalf of users

### MVP Scope (Current Phase)
- Upload files ✓
- Search by keyword (filename for now)
- Browse recent items ✓
- View original documents (UI needed)
- Basic AI summaries (not yet implemented)

**The critical next step is AI summaries** - this transforms storage into understanding.

## Key Files

- `/docs/00-vision-and-principles.md` - Start here
- `/docs/10-build-guidance-prompt.md` - Master guidance
- `/docs/11-mvp-architecture.md` - Current architecture
- `/app/main.py` - FastAPI application
- `/app/models.py` - Database models

## Data Model

- **Item**: A captured document with metadata
- **Document**: The original file in R2 storage (never modified)
- **Summary**: AI-generated description (future)
- **Insight**: Observed patterns, reminders (future)

## Environment

Uses Cloudflare R2 for storage, SQLite for metadata. See `.env.example` for configuration.

## When in Doubt

1. Check the docs in `/docs/`
2. Ask the user before adding features
3. Prefer simplicity over sophistication
4. Remember: this needs to work for 20 years
