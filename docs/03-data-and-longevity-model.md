# Life Admin System – Data and Longevity Model

This system is designed to outlive technologies, vendors, and software trends.

Data must always be accessible, understandable, and exportable.

## Types of data in the system

### 1. Source documents
The original artefacts:
- PDFs
- photos
- scans
- emails
- text notes

These are the source of truth.

They must never be altered, replaced, or hidden.

---

### 2. Extracted facts
Information derived from documents:
- dates
- vendors
- amounts
- reference numbers
- contract terms

Extracted facts may be incomplete or corrected over time.

---

### 3. Human-readable summaries
Plain-English explanations for understanding.

Summaries are helpers.
They are not authoritative.

---

### 4. System metadata
Information about:
- when something was added
- who added it
- relationships between items
- review windows

---

## Longevity principles

- Documents stored in standard, widely supported formats
- Metadata stored in simple, exportable formats (e.g. JSON, CSV)
- No proprietary-only formats required to understand data
- Full export must be possible at any time

---

## Offline survivability scenario

If the system no longer exists:

- A single archive can be opened without internet access
- A human-readable index explains the contents
- Documents are accessible directly
- No specialist software is required

---

## What this avoids

- Vendor lock-in
- Database-only storage
- “Black box” AI systems
- Data that cannot be understood without the app
