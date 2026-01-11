# Life Admin System

**AI-powered document capture that turns family paperwork into actionable intelligence with zero filing friction.**

---

## What Is This?

Life Admin System is a long-lived document capture and intelligence system for family life administration. It eliminates the friction of managing paperwork by:

1. **Zero-friction capture** - Upload anything, instantly, no questions asked
2. **AI organization** - Automatically extracts info, detects entities, categorizes
3. **Proactive insights** - Tells you what needs attention and when

Built to last 10-20+ years. Your data, your control.

---

## Quick Start

### 1. Install

```bash
# Clone the repository
git clone https://github.com/yourusername/life-admin-system.git
cd life-admin-system

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your keys:
# - ANTHROPIC_API_KEY (for AI summaries)
# - R2 credentials (for storage)
```

### 3. Run

**Option A: Web Server (Terminal)**
```bash
uvicorn app.main:app --reload --port 8000
```

**Option B: Mac Menu Bar App**
```bash
./launch.sh
```

**Option C: Create Native App**
See [Mac App Guide](README-MAC-APP.md) for creating a clickable .app bundle.

### 4. Use

- Open browser: http://localhost:8000
- Upload a document
- AI automatically extracts information
- View insights on dashboard

---

## Core Features

### Zero-Friction Upload
- Drag & drop or click to upload
- Mobile-friendly capture
- Gmail auto-sync (optional)
- No filing decisions needed

### AI-Powered Intelligence
- Automatic text extraction (OCR for images/PDFs)
- Entity detection (people, vehicles, pets, properties)
- Smart categorization (vehicle, medical, utilities, tax, etc.)
- Natural language search ("Show me car insurance documents")

### Proactive Insights
- **Rule-based alerts** - Renewals, expirations, deadlines
- **AI-powered analysis** - Bill anomalies, spending trends, recommendations
- **Entity-aware** - "[Toyota Corolla] NCT Due" not generic "NCT Due"
- **Actionable** - Every insight suggests what to do

### Built for Longevity
- SQLite database (portable, proven)
- Cloudflare R2 storage (S3-compatible)
- Open data formats (no vendor lock-in)
- Designed for 10-20+ year lifespan

---

## Key Concepts

### Documents Are Source of Truth
- Original files never modified
- All analysis is layered on top
- Can always access original document
- No information loss

### Zero Decision-Making at Intake
- If it's life admin, upload it
- No categories, no folders, no tags
- AI organizes after the fact
- Capture everything = build complete history

### Multi-Entity Intelligence
- Track multiple people, vehicles, pets, properties
- AI detects WHO or WHAT each document is about
- Personalized insights per entity
- Clear, unambiguous actions

### AI Assists, Humans Decide
- AI generates summaries and insights
- Humans review and take action
- No automated decisions
- Trust but verify

---

## Architecture Overview

```
┌─────────────┐
│   Intake    │ Upload files (web, mobile, Gmail sync)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Archive   │ R2 storage + SQLite metadata
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Understanding│ AI summaries, OCR, entity detection
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Insight   │ Intelligence agents + AI analysis
└─────────────┘
```

**One-way data flow:** Intake → Archive → Understanding → Insight

---

## Documentation

### For Users
- [User Guide](docs/60-user-guide.md) - How to use the system
- [Mac App Guide](README-MAC-APP.md) - macOS native menu bar app

### For Understanding
- [Vision & Principles](docs/00-vision-and-principles.md) - Philosophy and core rules
- [Elevator Pitch](ELEVATOR-PITCH.md) - What this is and why it exists
- [Core Concepts](docs/02-core-concepts-and-language.md) - Key terminology

### For Development
- [Build Guidance](docs/10-build-guidance-prompt.md) - How to work on this codebase
- [Agent Development Guide](docs/91-agent-development-guide.md) - Building intelligence agents
- [Build Log](docs/99-build-log.md) - What was built and how

### For Deployment
- [Deployment Guide](docs/50-deployment.md) - Production deployment options
- [MVP Architecture](docs/11-mvp-architecture.md) - Technical architecture

### Frameworks
- [Agent Framework](AGENT_FRAMEWORK_COMPLETE.md) - Modular intelligence system
- [Entity Framework](ENTITY_FRAMEWORK_COMPLETE.md) - Multi-person/multi-asset tracking

---

## Technology Stack

- **Backend:** FastAPI (Python)
- **Database:** SQLite (portable, proven)
- **Storage:** Cloudflare R2 (S3-compatible)
- **AI:** Claude (Anthropic - document understanding)
- **OCR:** Tesseract (open source)
- **Frontend:** Jinja2 templates, vanilla JavaScript
- **Desktop:** macOS menu bar app (rumps)

---

## Use Cases

### Family Life Admin (Primary)
- Car documents (insurance, NCT, tax, service)
- Medical records (appointments, prescriptions, test results)
- Utilities (electricity, gas, water, broadband bills)
- Financial (bank statements, credit cards, loans)
- Tax documents (P60s, tax returns, receipts)
- Home (mortgage, property tax, home insurance)
- School fees, pet records, travel documents

### Multi-Person Household
- Track 5 family members independently
- 2 cars analyzed separately
- Pet medical records organized
- Each person sees their own actions

### Small Business (Future Mode 2)
- Same code, different deployment
- Track employees, company vehicles
- Compliance documents organized
- Multi-tenant security built-in

---

## What's Different?

Most document management systems focus on:
- Better filing (folders, tags, metadata)
- Better search (full-text, filters)
- Better sharing (permissions, collaboration)

**Life Admin System focuses on:**
- **Zero-friction capture** - No filing decisions = captures everything
- **AI organization** - Organize after the fact, not during intake
- **Proactive intelligence** - Don't just store, actively help

**The insight:** If filing takes 30 seconds and 3 decisions, you won't capture everything. And if you don't capture everything, you can't build intelligence.

---

## Project Status

**Current:** Fully operational for personal/family use

**What's Working:**
- ✅ Zero-friction upload (web, mobile, Gmail)
- ✅ AI summaries and entity detection
- ✅ 14 category intelligence agents
- ✅ Natural language search
- ✅ AI-powered insights (anomaly detection, trends)
- ✅ macOS native menu bar app
- ✅ Dashboard with actionable items
- ✅ 500+ documents ingested and analyzed

**What's Next:**
- Mobile app for iOS/Android
- More intelligence agents (migration ongoing)
- Entity filtering in UI
- Weekly AI digest emails
- Multi-user access controls (for Mode 2)

---

## Getting Help

- Read the [User Guide](docs/60-user-guide.md)
- Check the [Build Log](docs/99-build-log.md) for how things work
- Review [Vision & Principles](docs/00-vision-and-principles.md) to understand the philosophy

---

## Philosophy

1. **Documents are source of truth** - Never hide, replace, or obscure originals
2. **Zero decision-making at intake** - No questions, no categories, no filing
3. **One-way data flow** - Intake → Archive → Understanding → Insight
4. **Longevity over novelty** - Built to last 10-20+ years
5. **Simple enough for family** - Non-technical users must understand it
6. **AI assists, humans decide** - AI suggests, humans act
7. **No feature bloat** - Reject anything that doesn't serve core mission

---

## License

This is a personal project. See LICENSE file for details.

---

## Contact

Built by Stephen Cranfield for family use. Documented for future maintainability and potential business extraction.

**Built 2025-2026. Operational. Ready for decades.**
