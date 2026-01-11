# Life Admin System

**AI-powered document capture that turns family paperwork into actionable intelligence with zero filing friction.**

This is a long-lived family system built to last 10-20+ years. It captures life admin documents with zero friction, uses AI to organize and understand them, then generates proactive insights about what needs attention.

## Quick Start

### 1. Install System Dependencies

**macOS:**
```bash
# Install Tesseract OCR (required for image text extraction)
brew install tesseract

# Verify installation
tesseract --version
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### 2. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add:
# - ANTHROPIC_API_KEY (get from https://console.anthropic.com)
# - R2 credentials (Cloudflare R2 for storage)
# - Other settings as needed
```

For Gmail auto-sync (optional):
- See `docs/google-cloud-setup.md`
- Download OAuth client JSON to `secrets/google_oauth_client.json`

### 4. Run

**Option A: Web Server (Terminal)**
```bash
uvicorn app.main:app --reload --port 8000
```
Then open: http://localhost:8000

**Option B: macOS Menu Bar App**
```bash
./launch.sh
```
See [Mac App Guide](README-MAC-APP.md) for details.

**Option C: Background Service**
See `docs/50-deployment.md` for production deployment options.

## What This Does

### Zero-Friction Capture
- Upload any document (drag & drop, mobile, or Gmail auto-sync)
- No categories, folders, or tags required
- No filing decisions at intake
- Works from anywhere (web, mobile, email)

### AI-Powered Intelligence
- **OCR** - Extracts text from PDFs and images
- **AI Summaries** - Extracts dates, amounts, vendors, document types
- **Entity Detection** - Knows WHO (people) or WHAT (vehicles, pets, properties) each document is about
- **Smart Categorization** - Auto-categorizes into life admin categories (vehicle, medical, utilities, tax, etc.)
- **Natural Language Search** - "Show me car insurance documents" or "Find medical bills from 2025"

### Proactive Insights
- **Rule-based alerts** - "[Toyota Corolla] NCT due in 30 days"
- **AI-powered analysis** - "Electricity bill jumped 40% vs last month"
- **Cross-document intelligence** - "Car insurance renewed but no payment found"
- **Recommendations** - "3 subscriptions from same vendor - bundle discount possible?"

## Core Features

### Multi-Entity Intelligence
- Track multiple people, vehicles, pets, properties independently
- AI auto-detects which entity each document is about
- Personalized insights per entity: "[Stephen] Prescription refill due" not generic "Prescription due"

### 14 Intelligence Agents
Specialized AI agents analyze documents by category:
- Vehicle (insurance, NCT, tax, service)
- Medical (appointments, prescriptions, results)
- Utilities (electricity, gas, water, broadband)
- Tax (returns, receipts, P60s)
- Financial, Insurance, Home, Legal, and more

### Natural Language Search
Ask in plain English:
- "Show me everything related to my car"
- "Find electricity bills from 2025"
- "Medical documents from The Plaza Clinic"

### macOS Native App
- Menu bar integration
- Server control (start/stop/restart)
- Quick actions (sync Gmail, generate insights)
- Live status indicators
- Native notifications

## Documentation

### Essential Reading
- **[CLAUDE.md](CLAUDE.md)** - Instructions for AI assistance (critical for development)
- **[ELEVATOR-PITCH.md](ELEVATOR-PITCH.md)** - What this is and why it exists
- **[Vision & Principles](docs/00-vision-and-principles.md)** - Core philosophy (read this first!)
- **[Build Log](docs/99-build-log.md)** - What was built, what worked, what failed

### User Guides
- **[User Guide](docs/60-user-guide.md)** - How to use the system
- **[Mac App Guide](README-MAC-APP.md)** - macOS menu bar app

### Development Guides
- **[Build Guidance](docs/10-build-guidance-prompt.md)** - How to work on this codebase
- **[Agent Development](docs/91-agent-development-guide.md)** - Building intelligence agents
- **[Business Framework](docs/90-business-framework.md)** - Optional business extraction paths

### Architecture
- **[MVP Architecture](docs/11-mvp-architecture.md)** - Technical architecture
- **[Deployment Guide](docs/50-deployment.md)** - Production deployment
- **[Agent Framework](AGENT_FRAMEWORK_COMPLETE.md)** - Modular intelligence system
- **[Entity Framework](ENTITY_FRAMEWORK_COMPLETE.md)** - Multi-person/multi-asset tracking

### Full Documentation Site
```bash
# Install mkdocs (included in requirements.txt)
pip install -r requirements.txt

# Serve documentation locally
mkdocs serve

# Build static site
mkdocs build
```

Then open: http://localhost:8001

## Philosophy

**Documentation-First**
- The `docs/` folder defines the system's intent, constraints, and behavior
- All code must conform to the documentation
- If implementation conflicts with docs, the docs win

**Core Principles** (Never violate these)
1. **Zero decision-making at intake** - If it's life admin, it goes in. No questions.
2. **Documents are source of truth** - Never hide, replace, or obscure originals
3. **One-way data flow** - Intake → Archive → Understanding → Insight
4. **Longevity over novelty** - Built for 10-20+ year lifespan
5. **Simple enough for family** - Non-technical users must understand it
6. **AI assists, humans decide** - AI generates insights, humans make decisions
7. **No feature bloat** - Reject anything that doesn't serve core mission

**Read [docs/00-vision-and-principles.md](docs/00-vision-and-principles.md) before making changes.**

## Technology Stack

- **Backend:** FastAPI (Python) - maintainable for decades
- **Database:** SQLite - portable, proven, simple
- **Storage:** Cloudflare R2 - S3-compatible, predictable costs
- **AI:** Claude (Anthropic) - best-in-class document understanding
- **OCR:** Tesseract - open source, robust
- **Frontend:** Jinja2 templates, vanilla JavaScript
- **Desktop:** macOS menu bar app (rumps)

## Project Status

**Fully Operational** (January 2026)

### What's Working
- ✅ Zero-friction upload (web, mobile, Gmail auto-sync)
- ✅ AI summaries (date, amount, vendor, document type extraction)
- ✅ Entity detection (people, vehicles, pets, properties)
- ✅ 14 category intelligence agents (1/14 entity-aware so far)
- ✅ AI-powered insights (anomaly detection, trend analysis)
- ✅ Natural language search
- ✅ Dashboard with actionable items
- ✅ macOS native menu bar app
- ✅ 500+ documents ingested and analyzed
- ✅ Production-ready deployment on Mac Mini

### What's Next
- Migrate remaining 13 agents to entity-aware
- Entity filtering in dashboard/vault UI
- Mobile app (iOS/Android)
- Weekly AI digest emails
- More intelligence agents

## Common Tasks

### Run the Web Server
```bash
uvicorn app.main:app --reload --port 8000
```

### Run the Mac Menu Bar App
```bash
./launch.sh
```

### Sync Gmail
```bash
python3 -m scripts.gmail_ingest
```

### Generate AI Summaries
```bash
python3 -m scripts.batch_generate_summaries
```

### Generate Insights
```bash
python3 -m app.insights
```

### Backup Database
```bash
python3 -m scripts.backup_db
```

### View Logs
```bash
# Server logs
tail -f logs/server.log

# Gmail sync logs
tail -f logs/gmail_sync.log

# All logs
ls -la logs/
```

## Development

### Running Tests
```bash
# Test agent framework
python3 test_agents.py

# Test specific module
python3 -m pytest tests/
```

### Building Intelligence Agents
See [Agent Development Guide](docs/91-agent-development-guide.md) for:
- 6-step development workflow
- Agent templates
- 18 agent ideas
- Portfolio growth strategy

### Database Migrations
```bash
# Add entities (if not already run)
python3 scripts/migrate_add_entities.py
```

## Getting Help

1. **Read the docs** - Start with [Vision & Principles](docs/00-vision-and-principles.md)
2. **Check the build log** - See [Build Log](docs/99-build-log.md) for implementation details
3. **Review CLAUDE.md** - Instructions for AI-assisted development
4. **Search the code** - Natural language search works on the docs too!

## Important Files

- **CLAUDE.md** - AI development instructions (critical!)
- **ELEVATOR-PITCH.md** - What this is and why
- **docs/00-vision-and-principles.md** - Core philosophy
- **docs/99-build-log.md** - Complete implementation history
- **app/main.py** - FastAPI application entry point
- **app/models.py** - Database models
- **app/agents/** - Intelligence agent framework
- **app/agents_library/** - Individual intelligence agents

## License

Personal project. See LICENSE file for details.

## Contact

Built by Stephen Cranfield for family use. Documented for future maintainability and potential business extraction.

**Built 2025-2026. Operational. Ready for decades.**
