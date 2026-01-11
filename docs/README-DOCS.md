# Documentation Guide

This directory contains all documentation for the Life Admin System, organized for MkDocs.

## Viewing the Documentation

### Option 1: MkDocs Site (Recommended)

The best way to read the documentation is through the MkDocs site:

```bash
# From project root
source .venv/bin/activate
mkdocs serve
```

Then open: **http://localhost:8001**

This gives you:
- Beautiful book-like layout
- Full-text search
- Dark mode
- Mobile-friendly design
- Easy navigation between chapters

### Option 2: Direct File Reading

All markdown files can be read directly in any editor or on GitHub.

## Documentation Structure

The documentation is organized like a book with 6 parts:

### Getting Started
- **ELEVATOR-PITCH.md** - What this system is (read this first!)
- **README-MAC-APP.md** - macOS menu bar app guide

### Part I - Vision & Philosophy
Core principles that define the system:
- `00-vision-and-principles.md` - Start here to understand the philosophy
- `01-intake-rule.md` - The zero-friction intake rule
- `02-core-concepts-and-language.md` - Key terminology
- `03-data-and-longevity-model.md` - Built to last 10-20+ years
- `04-security-and-access-model.md` - Security approach
- `05-user-experience-and-habits.md` - UX philosophy
- `06-ai-responsibilities-and-limits.md` - AI's role
- `07-efficiency-and-insight-layer.md` - Intelligence layer

### Part II - Architecture & Implementation
Technical design and implementation:
- `08-architecture-options.md` - Architecture decisions
- `09-mvp-scope-and-phasing.md` - MVP scope
- `10-build-guidance-prompt.md` - How to work on this codebase
- `11-mvp-architecture.md` - Technical architecture
- `20-vault-ui-evolution.md` - UI design evolution

### Part III - Major Frameworks
Core systems that power the intelligence:
- **AGENT_FRAMEWORK_COMPLETE.md** - Modular intelligence system
  - `app/agents/README.md` - Technical implementation details
- **ENTITY_FRAMEWORK_COMPLETE.md** - Multi-person/multi-asset tracking

### Part IV - User Guide
- `60-user-guide.md` - How to use the system

### Part V - Deployment
- `50-deployment.md` - Production deployment guide
- `google-cloud-setup.md` - Google Cloud configuration

### Part VI - Development
For developers and future maintainers:
- **CLAUDE.md** - AI development guide (critical for AI-assisted work)
- `91-agent-development-guide.md` - Building intelligence agents
- `90-business-framework.md` - Optional business extraction paths
- `99-build-log.md` - Complete build history (what worked, what failed)

## Essential Reading Order

If you're new to this system:

1. **ELEVATOR-PITCH.md** - Understand what this is (2 minutes)
2. **00-vision-and-principles.md** - Learn the core philosophy (10 minutes)
3. **index.md** (at docs/index.md) - Quick start guide (5 minutes)
4. **99-build-log.md** - See what was built and why (as needed)
5. **CLAUDE.md** - If doing development work (5 minutes)

## For Emergencies

If something happened to the owner and you need to maintain this system:

1. Read **ELEVATOR-PITCH.md** - Understand what this system does
2. Read **00-vision-and-principles.md** - Understand the philosophy
3. Read **99-build-log.md** - See the complete implementation history
4. Read **11-mvp-architecture.md** - Understand the technical architecture

All data is stored in:
- **Cloudflare R2** - Original documents (credentials in `.env`)
- **SQLite database** - Metadata (file: `life_admin.db`)
- **backups/** directory - Database backups

## File Organization

```
docs/
├── README-DOCS.md (this file)
├── index.md (homepage)
├── ELEVATOR-PITCH.md
├── README-MAC-APP.md
├── CLAUDE.md
├── AGENT_FRAMEWORK_COMPLETE.md
├── ENTITY_FRAMEWORK_COMPLETE.md
├── 00-vision-and-principles.md
├── 01-intake-rule.md
├── 02-core-concepts-and-language.md
├── 03-data-and-longevity-model.md
├── 04-security-and-access-model.md
├── 05-user-experience-and-habits.md
├── 06-ai-responsibilities-and-limits.md
├── 07-efficiency-and-insight-layer.md
├── 08-architecture-options.md
├── 09-mvp-scope-and-phasing.md
├── 10-build-guidance-prompt.md
├── 11-mvp-architecture.md
├── 20-vault-ui-evolution.md
├── 50-deployment.md
├── 60-user-guide.md
├── 90-business-framework.md
├── 91-agent-development-guide.md
├── 99-build-log.md
├── google-cloud-setup.md
└── app/
    └── agents/
        └── README.md
```

## Contributing to Documentation

When adding or updating documentation:

1. Add the file to the `docs/` directory
2. Update `mkdocs.yml` in the project root to include it in the navigation
3. Use clear, descriptive titles
4. Follow the existing structure and tone
5. Update this README if adding new sections

## MkDocs Configuration

The MkDocs site is configured in `/mkdocs.yml` at the project root.

Features enabled:
- Material theme with dark mode
- Navigation tabs and sections
- Search with suggestions
- Code copy buttons
- Emoji support
- GitHub integration

## Questions?

- Check the **99-build-log.md** for implementation details
- Review **00-vision-and-principles.md** for philosophy questions
- Read **CLAUDE.md** for AI-assisted development guidance
