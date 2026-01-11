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
- **Keep documentation updated** - This system is built to last 10-20+ years. Documentation is critical.
- Preserve data portability (no vendor lock-in)
- **Call out principle violations** - Actively warn if anything strays from the core ethos

### Documentation Requirements (CRITICAL)

**Every change must update documentation.** This system needs to be maintainable for decades.

#### 1. Build Log (`docs/99-build-log.md`)
**ALWAYS update the build log** when you:
- Build a new feature
- Fix a bug
- Make architectural changes
- Add new dependencies
- Modify the data model

**Format:**
```
## YYYY-MM-DD – Feature Name

### Goal
What you're trying to achieve

### What Was Built
- File: path/to/file.py
- What it does
- How it works

### What Worked
- ✅ What succeeded

### What Failed
- ❌ What didn't work initially

### Resolution
- How you fixed it

### Notes
- Important decisions
- Why you chose this approach
- Cost implications
- Future considerations
```

#### 2. Update Relevant Docs
When changing functionality, update:
- **README.md** - If setup/quick start changes
- **ELEVATOR-PITCH.md** - If core value proposition changes
- **Vision docs** (`00-07-*.md`) - If philosophy/principles change
- **Architecture docs** (`08-11-*.md`, `20-*.md`) - If technical architecture changes
- **User Guide** (`60-user-guide.md`) - If user-facing features change
- **Deployment** (`50-deployment.md`) - If deployment process changes
- **Agent/Entity Framework docs** - If frameworks evolve

#### 3. Framework Documentation
When building new frameworks or systems:
- Create a `*_FRAMEWORK_COMPLETE.md` file (like AGENT_FRAMEWORK_COMPLETE.md)
- Document what it is, why it exists, how it works
- Include examples and use cases
- Update `mkdocs.yml` to include it in navigation

#### 4. Code Comments
**Only add comments where logic isn't self-evident:**
- Complex AI prompts (explain intent)
- Database queries (explain what data you're fetching and why)
- Business logic (explain the rule being implemented)
- Workarounds (explain why the workaround exists)

**Don't comment:**
- Obvious code (`x = x + 1  # increment x` ❌)
- Standard patterns (CRUD operations, etc.)
- Framework conventions (FastAPI routes, etc.)

#### 5. Why Documentation Matters

**This is a 10-20+ year system.**

When you're gone or unavailable:
- Family members need to understand it
- Future maintainers need context
- The owner needs to remember why decisions were made

**Every undocumented decision is technical debt.**

#### 6. Documentation Checklist

Before marking work complete, verify:
- [ ] Build log updated with what was built
- [ ] Relevant docs updated (README, architecture, user guide, etc.)
- [ ] New features explained in appropriate doc files
- [ ] Breaking changes documented
- [ ] Complex logic has comments explaining WHY (not what)
- [ ] MkDocs site still builds (`mkdocs build`)

#### 7. Where Documentation Lives

- **`/docs/*.md`** - All markdown documentation
- **MkDocs site** - Built from `/docs/`, served via `./serve-docs.sh`
- **In-app** - Accessible at http://localhost:8000/docs/ in web UI
- **GitHub** - https://github.com/1Zero9/life-admin-system
- **Build log** - `/docs/99-build-log.md` (master record of all changes)

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
