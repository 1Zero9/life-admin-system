# Documentation System

This project has comprehensive documentation available in multiple ways.

## Quick Access

### 1. In-App Documentation (Easiest)

When the server is running, visit:

**http://localhost:8000/docs/**

This serves the complete MkDocs documentation site with:
- Beautiful book-like layout
- Full-text search
- Dark mode
- Mobile-friendly design
- All 25+ documentation pages

### 2. Documentation Info Page

**http://localhost:8000/docs-info**

This page provides:
- Links to all key documentation files
- Emergency information (if something happens to the owner)
- GitHub repository link
- Instructions for serving docs locally

### 3. Raw Markdown Files

All documentation lives in the `/docs/` directory:

```
docs/
├── index.md (homepage)
├── ELEVATOR-PITCH.md (what this system is)
├── CLAUDE.md (AI development guide)
├── 00-vision-and-principles.md (start here!)
├── 01-intake-rule.md
├── ... (25+ documentation files)
└── 99-build-log.md (complete build history)
```

You can read these files directly in any text editor or on GitHub.

## Documentation Structure

The documentation is organized like a book with 6 parts:

1. **Getting Started** - Quick start and overview
2. **Part I - Vision & Philosophy** - Core principles (8 chapters)
3. **Part II - Architecture** - Technical implementation (5 chapters)
4. **Part III - Major Frameworks** - Agent and entity systems
5. **Part IV - User Guide** - How to use the system
6. **Part V - Deployment** - Production deployment (2 chapters)
7. **Part VI - Development** - Building and extending (4 chapters)

## Viewing Documentation Locally

If the server isn't running or you want a standalone docs server:

```bash
# Option 1: Use the helper script
./serve-docs.sh

# Then open: http://localhost:8002

# Option 2: Manual build and serve
source .venv/bin/activate
mkdocs build
python3 -m http.server 8002 --directory site
```

## Essential Reading

If you're new to this system, read in this order:

1. **ELEVATOR-PITCH.md** - Understand what this is (2 minutes)
2. **docs/00-vision-and-principles.md** - Learn the philosophy (10 minutes)
3. **docs/index.md** - Quick start guide (5 minutes)
4. **docs/99-build-log.md** - See what was built (reference as needed)
5. **CLAUDE.md** - If doing development (5 minutes)

## Updating Documentation

**See CLAUDE.md for complete documentation requirements.**

Key rules:
- **Always update `docs/99-build-log.md`** when building features
- Update relevant docs when changing functionality
- Add code comments only where logic isn't self-evident
- Keep documentation in sync with code
- Verify MkDocs builds after updates: `mkdocs build`

## Why Documentation Matters

This system is built to last 10-20+ years.

Documentation ensures:
- Family members can maintain it if you're unavailable
- Future developers understand why decisions were made
- The system remains maintainable over decades
- Knowledge isn't lost

**Every undocumented decision is technical debt.**

## Documentation Checklist

Before marking work complete:
- [ ] Build log updated
- [ ] Relevant docs updated (README, architecture, user guide)
- [ ] New features documented
- [ ] MkDocs site still builds
- [ ] Complex logic has WHY comments

## GitHub Repository

Full source code and documentation:
**https://github.com/1Zero9/life-admin-system**

## Emergency Access

If something happened to the owner:

1. Read **docs/ELEVATOR-PITCH.md** - Understand the system
2. Read **docs/00-vision-and-principles.md** - Understand the philosophy
3. Read **docs/99-build-log.md** - See the complete history
4. Check `/docs-info` page in the web UI for data locations

All data is stored in:
- **Cloudflare R2** - Original documents (credentials in `.env`)
- **SQLite database** - Metadata (`life_admin.db` file)
- **backups/** directory - Database backups

---

**Built 2025-2026. Documentation-first. Ready for decades.**
