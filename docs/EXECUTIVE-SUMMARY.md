# Life Admin System — Executive Summary

**Prepared:** March 2026
**Status:** Operational (MVP Complete, Phase 2 In Progress)
**Stack:** Python / FastAPI · SQLite · Cloudflare R2 · Claude AI · Tesseract OCR

---

## The Problem Being Solved

Every household generates a continuous stream of administrative documents — insurance renewals, medical letters, vehicle certificates, utility bills, tax filings, contracts. The standard approach is a combination of physical folders, shared drives, and email archives. None of it works reliably. Documents are lost, missed, or found too late.

The reason existing tools fail isn't organisation — it's **friction at the point of capture**. If capturing a document requires a decision (Where does this go? What do I call it? Which folder?), people stop doing it. The pile grows. The chaos compounds.

**Life Admin System solves the friction problem, not the organisation problem.** Everything goes in. No decisions. AI handles the rest.

---

## What Has Been Built

A complete, production-grade document intelligence platform deployed and in active family use.

### Layer 1: Intake (Zero Friction)

Documents enter the system through multiple channels with no filing decisions required:

- **Web upload** — drag and drop, single or batch
- **Gmail auto-sync** — emails labelled `LifeAdmin` are ingested automatically, including attachments as linked child records
- **Mobile web** — responsive UI works on phone

Every document receives a SHA256 hash on arrival, preventing duplicates silently. Files are stored in Cloudflare R2 under a date-partitioned key (`documents/YYYY/MM/{uuid}.ext`) — no human-readable naming, no folder taxonomy, no decisions.

**Text is extracted at intake:**
- PDFs: full text extracted via pypdf
- Images and scanned documents: OCR pipeline using Tesseract with OpenCV preprocessing (contrast enhancement, noise reduction, thresholding for accuracy on poor-quality scans)
- File size cap at 10 MB for OCR (performance-bounded)

### Layer 2: Archive (Permanent, Portable)

- **Cloudflare R2**: S3-compatible object storage with no egress fees. The original file is never modified, never hidden, always downloadable.
- **SQLite**: Single-file relational database. Portable, proven, zero infrastructure overhead. Works the same in 20 years.
- **Soft deletes**: Items are hidden, never removed. The archive is permanent by design.

### Layer 3: Understanding (AI-Powered)

Once a document is stored, Claude AI (Haiku 3.5 for cost efficiency) processes it and extracts:

| Field | Example |
|---|---|
| Vendor / sender | "Aviva Insurance" |
| Document type | "Insurance Renewal" |
| Date | "2026-03-15" |
| Amount | "€847.00" |
| Category | "insurance" |
| Related entity | "BMW 5 Series (182-D-12345)" |

This runs asynchronously. The upload experience is never blocked by AI processing.

**Smart titles** are then generated from extracted data: `Aviva — Insurance Renewal — €847 — Mar 2026`. These replace unhelpful filenames like `scan_003.pdf` throughout the UI.

**15 life admin categories** are supported: vehicle, medical, home, utilities, financial, insurance, employment, tax, legal, education, travel, shopping, government, personal, other.

### Layer 4: Insight (Intelligence)

The system goes beyond storage and retrieval into active intelligence:

- **Vendor pattern detection**: Identifies recurring vendors and groups their documents
- **Renewal tracking**: Detects upcoming expirations (insurance, NCT, tax discs)
- **Spending summaries**: Category-level and vendor-level cost tracking from extracted amounts
- **Insight lifecycle**: Active → Dismissed → Resolved, with 30-day expiry and priority ranking

---

## The Agent Framework

The most significant architectural investment beyond the core product. A fully built, extensible intelligence layer designed to house specialised domain agents.

### How It Works

```
Documents → Agent Input → Claude AI Analysis → Structured Insights → Dashboard
```

Each agent:
1. Receives all documents for a given domain (e.g., all vehicle documents)
2. Is entity-aware — analyses each car, each person, each property separately
3. Makes a structured API call to Claude
4. Returns prioritised, actionable insights with confidence scores and estimated value

The framework includes:
- **Abstract base class** (`IntelligenceAgent`) — enforces a consistent `analyze()` interface
- **Auto-discovery registry** — drop a new agent file into `agents_library/` and it registers itself
- **Execution engine** — tracks run time, cost, and success/failure per agent
- **Unified data contracts** — `Document` and `Insight` dataclasses ensure agents are interchangeable

### Deployed: VehicleAgent

The first production agent. For each vehicle in the system it:

- Assesses document **completeness** (insurance, NCT, road tax, service history — all present?)
- Detects **upcoming renewals** with lead time warnings
- Analyses **maintenance patterns** against manufacturer intervals
- Flags **cost anomalies** (e.g., service costs spiking vs. historical baseline)
- Monitors **compliance** (are insurance and NCT both current and valid?)

Output is a prioritised insight list surfaced on the dashboard. Cost per vehicle analysis: approximately $0.008.

### 13 Agents Designed, Not Yet Built

The architecture is ready. The remaining agents — Medical, Utilities, Tax, Financial, Insurance, Employment, Home, Legal, Education, Travel, Shopping, Government, Personal — are specified but await implementation. Each follows an identical pattern to VehicleAgent.

---

## OCR: How Scanning Works

For physical documents (photos, scans), the pipeline is:

```
Uploaded image → OpenCV preprocessing → Tesseract OCR → extracted_text stored in DB
```

**Preprocessing steps applied:**
1. Greyscale conversion
2. Contrast enhancement (CLAHE)
3. Gaussian blur (noise reduction)
4. Adaptive thresholding (handles uneven lighting)
5. Deskew (straighten slightly rotated pages)

This significantly improves accuracy on phone-photographed documents versus raw Tesseract. The extracted text is then available for AI summarisation, full-text search, and agent analysis — the same as a digital PDF.

**Current limitation:** Heavily skewed or multi-column documents can still produce poor results. Advanced layout analysis (e.g., document segmentation before OCR) is a future improvement path.

---

## What Is Working Well

| Area | Status |
|---|---|
| Zero-friction intake | ✅ Fully operational |
| Gmail auto-sync | ✅ Fully operational |
| Duplicate detection | ✅ Fully operational |
| PDF text extraction | ✅ Fully operational |
| OCR for images | ✅ Operational (basic preprocessing) |
| AI summaries (all documents) | ✅ Fully operational |
| Entity detection & matching | ✅ Fully operational |
| Document categorisation (15 types) | ✅ Fully operational |
| Smart title generation | ✅ Fully operational |
| Natural language search | ✅ Operational |
| Rule-based insights | ✅ Operational |
| VehicleAgent intelligence | ✅ Operational |
| Entity management UI | ✅ Fully operational |
| Document preview (PDF / image) | ✅ Fully operational |
| Modern responsive UI | ✅ Complete (refactored Jan 2026) |
| Comprehensive documentation | ✅ 24-file docs site built with MkDocs |

The system has processed 500+ real family documents. It is not a prototype.

---

## What Is Not Yet Working / Blockers

### Agent Coverage Gap
The most significant gap. One agent is operational out of fourteen designed. The framework is proven — VehicleAgent demonstrates the pattern end-to-end — but the remaining domains (medical, financial, tax, utilities, etc.) are unbuilt. This limits the insight layer's breadth significantly.

**Effort to resolve**: Each agent is a self-contained Python file following an established pattern. A new agent can be built and deployed in a focused session. No architectural changes required.

### Insight Generation Is Manual
Insights are currently generated on-demand rather than on a schedule. There is no automated nightly or weekly run. This means insights are only as fresh as the last time someone clicked "Generate."

**Effort to resolve**: A background scheduler (APScheduler or a simple cron job against the `/insights/generate-ai` endpoint) would resolve this with minimal code.

### AI Feedback Loop Is Incomplete
When a user corrects a document category, the correction is recorded in the `CategoryCorrection` table. However, this data is not yet fed back into the AI prompt to improve future accuracy. The correction data exists and accumulates — the loop just isn't closed.

**Effort to resolve**: Inject the most recent N corrections as few-shot examples in the categorisation prompt. Moderate effort.

### No Push Notifications
The system surfaces insights on the dashboard, but nothing reaches the user proactively. If an insurance renewal is 30 days away, the user only knows if they open the app.

**Effort to resolve**: Email digest (weekly or on high-priority insight creation) via a simple SMTP integration. This is intentionally deferred — the UI-first approach was the right call for MVP.

### UI Refactoring Not Committed
The January 2026 UI modernisation (new design system, reusable components, ~1,000 lines of code removed) is complete and working but not yet committed to git. This represents a risk — the work exists only in the working tree.

**Immediate action required**: Commit this work.

---

## Design Decisions Worth Calling Out

**Why SQLite, not PostgreSQL?**
A 20-year system needs to survive the operator. SQLite is a single file. It backs up with `cp`. It has no server to maintain, no connection strings to rotate, no version upgrades to manage. For personal use at this data volume, it will never be a bottleneck.

**Why Cloudflare R2, not S3 or iCloud?**
No egress fees. S3 charges per GB downloaded — a system built to retrieve documents constantly would accumulate meaningful costs over decades. R2 is also S3-compatible, meaning a migration to any other provider is a configuration change.

**Why server-side rendering, not React?**
JavaScript frameworks age poorly. The UI built in 2026 with React 18 will be a maintenance headache in 2034. Server-rendered Jinja2 templates will still work unchanged.

**Why no categorisation at intake?**
Because friction kills adoption. The most important behaviour change this system requires is consistent document capture. Making it frictionless is the product. Categories can always be applied retroactively by AI — a missed document cannot be retrospectively captured.

---

## What Should Be Built Next

In order of value delivered per effort:

### 1. Commit the UI work and remaining migration script
_Effort: 30 minutes. Risk: High if deferred._

### 2. Build the next 3–4 agents (Medical, Utilities, Financial, Insurance)
_Effort: 1–2 sessions each. These cover the highest-frequency document types after vehicle._

### 3. Automated insight scheduling
_Effort: Half a day. Transform insights from on-demand to always-current._

### 4. Email digest notification
_Effort: 1 day. High-value for family use — surfaces intelligence without requiring app visits._

### 5. Close the AI feedback loop (CategoryCorrection → prompt injection)
_Effort: Half a day. Improves accuracy over time without model retraining._

### 6. Advanced OCR preprocessing
_Effort: 1–2 days. Multi-column layout support, better rotation correction for phone photos._

---

## Commercial Optionality

The system is built for personal use. It is not being sold. However, the architecture has five documented extraction paths if commercialisation becomes relevant:

| Path | Model | Estimated ARR |
|---|---|---|
| Open Source + Services | Framework release, paid services | $120k–1.2M |
| Agent Marketplace | Third-party agents, revenue share | $45k–450k |
| Vertical SaaS | Life admin platform for consumers | $180k–3.6M |
| Enterprise Platform | Compliance document management | $250k–1.25M |
| Consulting/Advisory | System architecture consulting | $576k |

These are optionality paths only. The system is being built to the standard they would require — not to pursue them.

---

## Summary

Life Admin System is a complete, operational, and thoughtfully architected document intelligence platform. It solves the right problem (friction at capture), is built on technology choices that will age well, and has a clear and achievable roadmap for expanding its intelligence layer.

The core value proposition is working today: upload anything, AI understands it, the family has a permanent, searchable, intelligent archive of their administrative life.

The gaps are well-understood, bounded in scope, and don't touch the foundation. The foundation is solid.

---

_This document is part of the Life Admin System documentation suite. See `/docs/` for full technical and architecture documentation._
