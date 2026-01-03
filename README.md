# Life Admin System

This repository contains the design, principles, and future implementation of a Life Admin system.

This is a long-lived family system intended to:
- capture life admin information with zero friction
- store documents as the source of truth
- make information easy to find and understand
- remain usable and understandable decades into the future

## Important

This repository is intentionally documentation-first.

The `docs/` folder defines the system’s intent, constraints, and behaviour.
All future code must conform to those documents.

If implementation decisions conflict with the docs, the docs win.

## Status

MVP implemented and operational:
- FastAPI web application
- Gmail ingestion via Gmail API
- PDF text extraction
- OCR for image attachments
- Cloudflare R2 storage
- SQLite metadata database
- Search functionality

## Setup

### System Dependencies

Install Tesseract OCR (required for image text extraction):

```bash
# macOS
brew install tesseract

# Verify installation
tesseract --version
```

### Python Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` to `.env` and configure:
   - Cloudflare R2 credentials
   - Other environment variables

2. For Gmail ingestion, set up OAuth:
   - See `docs/google-cloud-setup.md`
   - Download OAuth client JSON to `secrets/google_oauth_client.json`

### Running

```bash
# Start web server
uvicorn app.main:app --reload

# Ingest labeled Gmail messages
python3 -m scripts.gmail_ingest
```
