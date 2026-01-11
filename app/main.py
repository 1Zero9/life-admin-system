import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import tempfile
import hashlib
from app.extractors import extract_pdf_text, extract_image_text

import boto3
from botocore.client import Config
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
from app.db import Base, engine, SessionLocal
from app.models import Item, AISummary, Insight
from fastapi import Request
from sqlalchemy.orm import joinedload
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.ui_helpers import normalize_title, format_date_display, format_source_type, get_file_type, get_file_icon_color
from app.ai_summary import generate_summary, delete_summary, get_summary, AI_ENABLED
from app.insights import get_active_insights, dismiss_insight




load_dotenv()

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET")
R2_PREFIX = os.getenv("R2_PREFIX", "documents")

missing = [k for k in ["R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"] if not os.getenv(k)]
if missing:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
)

app = FastAPI(title="Life Admin System (MVP)")
Base.metadata.create_all(bind=engine)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Mount documentation site (if it exists)
docs_site_path = Path("site")
if docs_site_path.exists():
    app.mount("/docs", StaticFiles(directory="site", html=True), name="docs")

templates = Jinja2Templates(directory="app/templates")



def build_object_key(original_filename: str) -> str:
    now = datetime.now(timezone.utc)
    ext = Path(original_filename).suffix.lower() or ".bin"
    item_id = str(uuid.uuid4())
    return f"{R2_PREFIX}/{now:%Y}/{now:%m}/{item_id}{ext}"


def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA256 hash of file content for duplicate detection."""
    return hashlib.sha256(file_content).hexdigest()


@app.get("/health")
def health():
    """Health check endpoint for monitoring."""
    db = SessionLocal()
    try:
        # Check database connectivity
        item_count = db.query(Item).filter(Item.deleted_at.is_(None)).count()
        db_healthy = True
    except Exception as e:
        item_count = 0
        db_healthy = False
    finally:
        db.close()

    # Check R2 connectivity (basic check - endpoint configured)
    r2_configured = bool(R2_ENDPOINT and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY)

    return {
        "ok": True,
        "database": {
            "healthy": db_healthy,
            "items": item_count,
        },
        "storage": {
            "configured": r2_configured,
        },
        "ai": {
            "enabled": AI_ENABLED,
        },
    }


async def process_single_file(file: UploadFile) -> dict:
    """Process a single file upload. Extracted for reuse in bulk uploads."""
    if not file.filename:
        return {"ok": False, "error": "Missing filename"}

    # Read file content once
    file_content = await file.read()
    size_bytes = len(file_content)

    # Calculate file hash for duplicate detection
    file_hash = calculate_file_hash(file_content)

    # Check for duplicates
    db = SessionLocal()
    try:
        existing = db.query(Item).filter(Item.file_hash == file_hash).first()
        if existing:
            return {
                "ok": True,
                "duplicate": True,
                "id": existing.id,
                "message": f"File already exists: {existing.original_filename}",
                "original_filename": existing.original_filename,
                "created_at": existing.created_at.isoformat(),
            }
    finally:
        db.close()

    object_key = build_object_key(file.filename)
    content_type = file.content_type or "application/octet-stream"

    # Text extraction
    extracted_text = None

    # Check if it's a PDF
    is_pdf = (content_type == "application/pdf") or (file.filename.lower().endswith(".pdf"))

    # Check if it's an image
    is_image = (
        content_type and content_type.startswith("image/")
    ) or file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic'))

    if is_pdf:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            tmp.write(file_content)
            tmp.flush()
            text = extract_pdf_text(tmp.name)
            if text:
                extracted_text = f"PDF:\n{text}"

    elif is_image:
        # Apply 10 MB limit for OCR (same as email attachments)
        max_ocr_size = 10 * 1024 * 1024  # 10 MB

        if size_bytes <= max_ocr_size:
            with tempfile.NamedTemporaryFile(suffix=Path(file.filename).suffix, delete=True) as tmp:
                tmp.write(file_content)
                tmp.flush()
                text = extract_image_text(tmp.name)
                if text:
                    extracted_text = f"OCR:\n{text}"
                    print(f"OCR extracted {len(text)} characters from {file.filename}")
        else:
            size_mb = size_bytes / (1024 * 1024)
            print(f"Skipping OCR for {file.filename} (size {size_mb:.1f} MB exceeds {max_ocr_size / (1024 * 1024):.0f} MB limit)")

    # Upload to R2
    try:
        s3.put_object(
            Bucket=R2_BUCKET,
            Key=object_key,
            Body=file_content,
            ContentType=content_type,
        )
    except Exception as e:
        return {"ok": False, "error": f"Upload failed: {e}", "filename": file.filename}

    # Store in database
    db = SessionLocal()
    try:
        item = Item(
            original_filename=file.filename,
            content_type=content_type,
            bucket=R2_BUCKET,
            object_key=object_key,
            size_bytes=size_bytes,
            extracted_text=extracted_text,
            file_hash=file_hash,
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        return {
            "ok": True,
            "duplicate": False,
            "id": item.id,
            "bucket": item.bucket,
            "object_key": item.object_key,
            "original_filename": item.original_filename,
            "content_type": item.content_type,
            "size_bytes": item.size_bytes,
            "created_at": item.created_at.isoformat(),
        }
    finally:
        db.close()


@app.post("/intake/upload")
async def upload(file: UploadFile = File(...)):
    """Upload a single file."""
    result = await process_single_file(file)
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error", "Upload failed"))
    return result


@app.post("/intake/upload-multiple")
async def upload_multiple(files: List[UploadFile] = File(...)):
    """Upload multiple files at once."""
    results = []

    for file in files:
        result = await process_single_file(file)
        results.append(result)

    # Count successes and failures
    successful = sum(1 for r in results if r.get("ok") and not r.get("duplicate"))
    duplicates = sum(1 for r in results if r.get("ok") and r.get("duplicate"))
    failed = sum(1 for r in results if not r.get("ok"))

    return {
        "ok": True,
        "total": len(files),
        "successful": successful,
        "duplicates": duplicates,
        "failed": failed,
        "results": results,
    }


@app.get("/items/recent")
def recent(limit: int = 25):
    limit = max(1, min(limit, 100))

    db = SessionLocal()
    try:
        items = (
            db.query(Item)
            .filter(Item.deleted_at.is_(None))
            .order_by(Item.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": i.id,
                "original_filename": i.original_filename,
                "content_type": i.content_type,
                "bucket": i.bucket,
                "object_key": i.object_key,
                "size_bytes": i.size_bytes,
                "created_at": i.created_at.isoformat(),
                "parent_id": i.parent_id,
                "source_type": i.source_type,
                "source_id": i.source_id,
            }
            for i in items
        ]
    finally:
        db.close()


@app.get("/")
def ui_home(
    request: Request,
    q: str | None = None,
    source: str | None = None,
    view: str = "all"
):
    """
    Vault UI home screen.
    Shows items with normalized titles, formatted dates, and file type icons.
    Supports search, filtering by source type, and different views.

    Parameters:
    - q: search query
    - source: filter by source_type (email, upload, attachment)
    - view: all, recent (default: all)
    """
    db = SessionLocal()
    try:
        # Build query based on filters
        # Always exclude deleted items
        # Eager load AI summaries
        query = db.query(Item).options(joinedload(Item.ai_summary)).filter(Item.deleted_at.is_(None))

        # Apply source filter if specified
        if source and source != "all":
            query = query.filter(Item.source_type == source)

        # Apply search if specified
        if q:
            q_like = f"%{q}%"
            query = query.filter(or_(
                Item.original_filename.ilike(q_like),
                Item.extracted_text.ilike(q_like),
            ))

        # For table view, we want all items (not grouped)
        # Sort by most recent first
        raw_items = query.order_by(Item.created_at.desc()).limit(100).all()

        # Format items for display
        items = []
        for i in raw_items:
            file_type = get_file_type(i.original_filename, i.content_type)

            # Include AI summary if it exists
            ai_summary = None
            if i.ai_summary:
                ai_summary = {
                    "summary_text": i.ai_summary.summary_text,
                    "document_type": i.ai_summary.document_type,
                    "extracted_date": i.ai_summary.extracted_date,
                    "extracted_amount": i.ai_summary.extracted_amount,
                    "extracted_vendor": i.ai_summary.extracted_vendor,
                    "category": i.ai_summary.category,
                    "generated_at": i.ai_summary.generated_at.strftime("%d %b %Y") if i.ai_summary.generated_at else None,
                }

            items.append({
                "id": i.id,
                "title": normalize_title(i.original_filename, i.source_type, i.created_at),
                "date": format_date_display(i.created_at),
                "source": format_source_type(i.source_type),
                "file_type": file_type,
                "file_icon_color": get_file_icon_color(file_type),
                "original_filename": i.original_filename,
                "parent_id": i.parent_id,
                "size_bytes": i.size_bytes,
                "ai_summary": ai_summary,
                "has_extracted_text": bool(i.extracted_text),
            })

        # Get filter counts for sidebar (exclude deleted items)
        all_count = db.query(Item).filter(Item.deleted_at.is_(None)).count()
        email_count = db.query(Item).filter(Item.source_type == "email", Item.deleted_at.is_(None)).count()
        upload_count = db.query(Item).filter(Item.source_type.is_(None), Item.deleted_at.is_(None)).count()
        attachment_count = db.query(Item).filter(Item.source_type == "attachment", Item.deleted_at.is_(None)).count()

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "items": items,
                "q": q,
                "source": source or "all",
                "view": view,
                "ai_enabled": AI_ENABLED,
                "counts": {
                    "all": all_count,
                    "email": email_count,
                    "upload": upload_count,
                    "attachment": attachment_count,
                }
            },
        )
    finally:
        db.close()


@app.get("/upload")
def ui_upload_page(request: Request):
    """Upload page"""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.get("/docs-info")
def docs_info_page(request: Request):
    """Documentation information page"""
    return templates.TemplateResponse("docs-info.html", {"request": request})


@app.get("/items/{item_id}")
def item_detail(request: Request, item_id: str):
    """
    Item detail page.
    Shows full metadata, download link, attachments (if email), parent (if attachment).
    Layer 1 only - no AI summaries.
    """
    db = SessionLocal()
    try:
        # Get the item
        item = db.query(Item).filter(Item.id == item_id, Item.deleted_at.is_(None)).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Format item for display
        file_type = get_file_type(item.original_filename, item.content_type)

        item_data = {
            "id": item.id,
            "title": normalize_title(item.original_filename, item.source_type, item.created_at),
            "original_filename": item.original_filename,
            "date": format_date_display(item.created_at),
            "date_full": item.created_at.strftime("%-d %B %Y, %H:%M"),
            "size_bytes": item.size_bytes,
            "size_human": format_file_size(item.size_bytes) if item.size_bytes else "Unknown",
            "content_type": item.content_type,
            "source": format_source_type(item.source_type),
            "file_type": file_type,
            "extracted_text": item.extracted_text,
            "extracted_chars": len(item.extracted_text) if item.extracted_text else 0,
            "parent_id": item.parent_id,
        }

        # Get attachments if this is an email
        attachments = []
        if item.source_type == "email":
            raw_attachments = (
                db.query(Item)
                .filter(Item.parent_id == item_id, Item.deleted_at.is_(None))
                .order_by(Item.created_at.asc())
                .all()
            )

            for att in raw_attachments:
                attachments.append({
                    "id": att.id,
                    "title": normalize_title(att.original_filename, att.source_type, att.created_at),
                    "original_filename": att.original_filename,
                    "size_human": format_file_size(att.size_bytes) if att.size_bytes else "Unknown",
                    "file_type": get_file_type(att.original_filename, att.content_type),
                })

        # Get parent email if this is an attachment
        parent = None
        if item.parent_id:
            parent_item = db.query(Item).filter(Item.id == item.parent_id).first()
            if parent_item:
                parent = {
                    "id": parent_item.id,
                    "title": normalize_title(parent_item.original_filename, parent_item.source_type, parent_item.created_at),
                    "date": format_date_display(parent_item.created_at),
                }

        # Get AI summary if exists
        ai_summary = get_summary(item_id) if AI_ENABLED else None

        return templates.TemplateResponse(
            "item_detail.html",
            {
                "request": request,
                "item": item_data,
                "attachments": attachments,
                "parent": parent,
                "ai_summary": ai_summary,
                "ai_enabled": AI_ENABLED,
            },
        )
    finally:
        db.close()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


@app.post("/items/{item_id}/summary")
def generate_item_summary(item_id: str):
    """
    Generate AI summary for an item (Layer 2).
    Requires extracted text and Anthropic API key.
    """
    if not AI_ENABLED:
        raise HTTPException(status_code=501, detail="AI summaries not enabled. Set ANTHROPIC_API_KEY in .env")

    result = generate_summary(item_id)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to generate summary")

    return {"ok": True, "summary": result}


@app.delete("/items/{item_id}/summary")
def delete_item_summary(item_id: str):
    """Delete AI summary for an item."""
    deleted = delete_summary(item_id)
    return {"ok": True, "deleted": deleted}


@app.get("/items/{item_id}/summary")
def get_item_summary(item_id: str):
    """Get existing AI summary for an item."""
    summary = get_summary(item_id)
    if not summary:
        raise HTTPException(status_code=404, detail="No summary found")

    return {"ok": True, "summary": summary}


@app.post("/summaries/generate-all")
def generate_all_summaries(skip_existing: bool = True):
    """
    Generate AI summaries for all items that don't have one.
    This can be a long-running operation for many items.
    """
    if not AI_ENABLED:
        raise HTTPException(status_code=501, detail="AI summaries not enabled. Set ANTHROPIC_API_KEY in .env")

    db = SessionLocal()
    try:
        # Get all items without summaries (and with extracted text)
        if skip_existing:
            items = (
                db.query(Item)
                .outerjoin(AISummary)
                .filter(
                    Item.deleted_at.is_(None),
                    Item.extracted_text.isnot(None),
                    AISummary.id.is_(None)  # No summary exists
                )
                .all()
            )
        else:
            # Regenerate all (even if summary exists)
            items = (
                db.query(Item)
                .filter(
                    Item.deleted_at.is_(None),
                    Item.extracted_text.isnot(None)
                )
                .all()
            )

        total = len(items)
        if total == 0:
            return {
                "ok": True,
                "message": "No items need summaries",
                "total": 0,
                "successful": 0,
                "failed": 0,
            }

        successful = 0
        failed = 0
        results = []

        for item in items:
            try:
                summary = generate_summary(item.id)
                if summary:
                    successful += 1
                    results.append({"id": item.id, "filename": item.original_filename, "ok": True})
                else:
                    failed += 1
                    results.append({"id": item.id, "filename": item.original_filename, "ok": False, "error": "Generation failed"})
            except Exception as e:
                failed += 1
                results.append({"id": item.id, "filename": item.original_filename, "ok": False, "error": str(e)})

        return {
            "ok": True,
            "total": total,
            "successful": successful,
            "failed": failed,
            "results": results,
        }

    finally:
        db.close()


@app.get("/summaries/stats")
def summary_stats():
    """Get statistics about AI summaries."""
    db = SessionLocal()
    try:
        total_items = db.query(Item).filter(Item.deleted_at.is_(None)).count()
        items_with_text = db.query(Item).filter(
            Item.deleted_at.is_(None),
            Item.extracted_text.isnot(None)
        ).count()
        items_with_summaries = (
            db.query(Item)
            .join(AISummary)
            .filter(Item.deleted_at.is_(None))
            .count()
        )
        items_needing_summaries = (
            db.query(Item)
            .outerjoin(AISummary)
            .filter(
                Item.deleted_at.is_(None),
                Item.extracted_text.isnot(None),
                AISummary.id.is_(None)
            )
            .count()
        )

        return {
            "ok": True,
            "total_items": total_items,
            "items_with_text": items_with_text,
            "items_with_summaries": items_with_summaries,
            "items_needing_summaries": items_needing_summaries,
            "ai_enabled": AI_ENABLED,
        }

    finally:
        db.close()


@app.get("/insights")
def get_insights():
    """
    Get all active insights (Layer 3).
    Returns insights ordered by priority (high → low) and date.
    """
    insights = get_active_insights()
    return {"ok": True, "insights": insights}


@app.post("/insights/{insight_id}/dismiss")
def dismiss_insight_route(insight_id: str):
    """Dismiss an insight."""
    dismissed = dismiss_insight(insight_id)
    if not dismissed:
        raise HTTPException(status_code=404, detail="Insight not found")

    return {"ok": True, "dismissed": True}


@app.post("/insights/{insight_id}/resolve")
def resolve_insight_route(insight_id: str):
    """Mark an insight action as resolved/completed."""
    db = SessionLocal()
    try:
        from app.models import Insight

        insight = db.query(Insight).filter(Insight.id == insight_id).first()
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")

        # Mark as resolved
        insight.status = "resolved"
        db.commit()

        return {"ok": True, "resolved": True}
    finally:
        db.close()


@app.post("/insights/{insight_id}/unresolve")
def unresolve_insight_route(insight_id: str):
    """Mark an insight action as unresolved (reopen it)."""
    db = SessionLocal()
    try:
        from app.models import Insight

        insight = db.query(Insight).filter(Insight.id == insight_id).first()
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")

        # Mark as active again
        insight.status = "active"
        db.commit()

        return {"ok": True, "unresolved": True}
    finally:
        db.close()


@app.post("/insights/generate-ai")
def generate_ai_insights_route():
    """
    Generate AI-powered insights using Claude to analyze documents.
    This goes beyond simple database queries to provide intelligent analysis.
    """
    if not AI_ENABLED:
        raise HTTPException(status_code=501, detail="AI features not enabled")

    try:
        from app.insights_ai import generate_all_ai_insights
        total = generate_all_ai_insights()

        return {
            "ok": True,
            "insights_generated": total,
            "message": f"Generated {total} AI-powered insights"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")


@app.post("/categories/categorize-all")
def categorize_all_documents_route():
    """Categorize all uncategorized documents using Claude."""
    if not AI_ENABLED:
        raise HTTPException(status_code=501, detail="AI features not enabled")

    try:
        from app.categorization import categorize_all_documents
        count = categorize_all_documents()

        return {
            "ok": True,
            "categorized": count,
            "message": f"Categorized {count} documents"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error categorizing: {str(e)}")


@app.get("/categories/stats")
def get_category_stats_route():
    """Get statistics about document categories."""
    try:
        from app.categorization import get_category_stats
        stats = get_category_stats()

        return {
            "ok": True,
            **stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@app.post("/categories/generate-intelligence")
def generate_category_intelligence_route():
    """Generate intelligent insights for all document categories."""
    if not AI_ENABLED:
        raise HTTPException(status_code=501, detail="AI features not enabled")

    try:
        from app.category_intelligence import generate_all_category_intelligence
        total = generate_all_category_intelligence()

        return {
            "ok": True,
            "insights_generated": total,
            "message": f"Generated {total} category intelligence insights"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating category intelligence: {str(e)}")


@app.post("/gmail/sync")
def sync_gmail_route():
    """Trigger Gmail sync to ingest new emails."""
    import subprocess
    from pathlib import Path

    try:
        # Run the Gmail sync script
        project_root = Path(__file__).parent.parent
        script_path = project_root / "scripts" / "gmail_sync.py"

        if not script_path.exists():
            raise HTTPException(status_code=404, detail="Gmail sync script not found")

        # Run the script
        result = subprocess.run(
            [str(project_root / ".venv" / "bin" / "python3"), str(script_path)],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse output to get counts
        output_lines = result.stdout.split('\n')
        summary_line = [line for line in output_lines if 'Sync complete:' in line]

        message = "Gmail sync completed"
        if summary_line:
            message = summary_line[0].split(' - ')[-1]  # Get the message part after timestamp

        return {
            "ok": True,
            "message": message,
            "output": result.stdout,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Gmail sync timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing Gmail: {str(e)}")


@app.get("/search/nl")
def natural_language_search_route(q: str, limit: int = 50):
    """
    Natural language search endpoint.

    Examples:
    - /search/nl?q=show me everything related to my car
    - /search/nl?q=find electricity bills from 2025
    - /search/nl?q=medical documents from The Plaza Clinic
    """
    if not AI_ENABLED:
        raise HTTPException(status_code=501, detail="AI features not enabled")

    if not q or len(q.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters")

    try:
        from app.nl_search import natural_language_search
        result = natural_language_search(q, limit=limit)

        if not result.get("ok"):
            raise HTTPException(status_code=500, detail=result.get("error", "Search failed"))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/insights/{insight_id}/details")
def get_insight_details(insight_id: str):
    """Get detailed information about an insight including related documents."""
    db = SessionLocal()
    try:
        from app.models import Insight, Item, AISummary
        import json

        # Get the insight
        insight = db.query(Insight).filter(Insight.id == insight_id).first()
        if not insight:
            return {"ok": False, "error": "Insight not found"}

        # Get related item IDs
        related_item_ids = json.loads(insight.related_items) if insight.related_items else []

        # Fetch related documents
        documents = []
        for item_id in related_item_ids:
            item = db.query(Item).filter(Item.id == item_id).first()
            if item:
                # Get AI summary if exists
                summary = db.query(AISummary).filter(AISummary.item_id == item_id).first()

                documents.append({
                    "id": item.id,
                    "filename": item.original_filename,
                    "created_at": item.created_at.isoformat(),
                    "content_type": item.content_type,
                    "summary": {
                        "type": summary.document_type if summary else None,
                        "vendor": summary.extracted_vendor if summary else None,
                        "amount": summary.extracted_amount if summary else None,
                        "date": summary.extracted_date if summary else None,
                    } if summary else None
                })

        return {
            "ok": True,
            "insight": {
                "id": insight.id,
                "type": insight.insight_type,
                "priority": insight.priority,
                "title": insight.title,
                "description": insight.description,
                "metadata": json.loads(insight.insight_metadata) if insight.insight_metadata else {},
                "generated_at": insight.generated_at.isoformat(),
            },
            "documents": documents
        }
    finally:
        db.close()


# ============================================================================
# Entity Management (Family members, vehicles, pets, properties)
# ============================================================================

@app.get("/entities")
def list_entities(active_only: bool = True):
    """
    List all entities (people, vehicles, pets, properties).
    """
    from app.models import Entity

    db = SessionLocal()
    try:
        query = db.query(Entity)
        if active_only:
            query = query.filter(Entity.is_active == True)

        entities = query.order_by(Entity.entity_type, Entity.entity_name).all()

        return {
            "ok": True,
            "entities": [
                {
                    "id": e.id,
                    "type": e.entity_type,
                    "name": e.entity_name,
                    "identifier": e.entity_identifier,
                    "metadata": e.entity_metadata,
                    "owner_id": e.owner_id,
                    "is_active": e.is_active,
                    "created_at": e.created_at.isoformat(),
                    "updated_at": e.updated_at.isoformat(),
                }
                for e in entities
            ]
        }
    finally:
        db.close()


@app.post("/entities")
def create_entity(
    entity_type: str,
    entity_name: str,
    entity_identifier: str = None,
    metadata: dict = None,
    owner_id: str = None
):
    """
    Create a new entity (person, vehicle, pet, property, etc.).
    """
    from app.models import Entity
    import uuid

    db = SessionLocal()
    try:
        entity = Entity(
            id=str(uuid.uuid4()),
            entity_type=entity_type,
            entity_name=entity_name,
            entity_identifier=entity_identifier,
            entity_metadata=metadata,
            owner_id=owner_id,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        db.add(entity)
        db.commit()
        db.refresh(entity)

        return {
            "ok": True,
            "entity": {
                "id": entity.id,
                "type": entity.entity_type,
                "name": entity.entity_name,
                "identifier": entity.entity_identifier,
                "metadata": entity.entity_metadata,
                "owner_id": entity.owner_id,
                "is_active": entity.is_active,
            }
        }
    finally:
        db.close()


@app.get("/entities/{entity_id}")
def get_entity(entity_id: str):
    """
    Get a specific entity by ID.
    """
    from app.models import Entity

    db = SessionLocal()
    try:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()

        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")

        # Count associated documents
        doc_count = db.query(AISummary).filter(AISummary.entity_id == entity_id).count()

        return {
            "ok": True,
            "entity": {
                "id": entity.id,
                "type": entity.entity_type,
                "name": entity.entity_name,
                "identifier": entity.entity_identifier,
                "metadata": entity.entity_metadata,
                "owner_id": entity.owner_id,
                "is_active": entity.is_active,
                "created_at": entity.created_at.isoformat(),
                "updated_at": entity.updated_at.isoformat(),
                "document_count": doc_count,
            }
        }
    finally:
        db.close()


@app.patch("/entities/{entity_id}")
def update_entity(
    entity_id: str,
    entity_name: str = None,
    entity_identifier: str = None,
    metadata: dict = None,
    owner_id: str = None,
    is_active: bool = None,
):
    """
    Update an entity's information.
    """
    from app.models import Entity

    db = SessionLocal()
    try:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()

        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")

        # Update fields if provided
        if entity_name is not None:
            entity.entity_name = entity_name
        if entity_identifier is not None:
            entity.entity_identifier = entity_identifier
        if metadata is not None:
            entity.entity_metadata = metadata
        if owner_id is not None:
            entity.owner_id = owner_id
        if is_active is not None:
            entity.is_active = is_active

        entity.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(entity)

        return {
            "ok": True,
            "entity": {
                "id": entity.id,
                "type": entity.entity_type,
                "name": entity.entity_name,
                "identifier": entity.entity_identifier,
                "metadata": entity.entity_metadata,
                "owner_id": entity.owner_id,
                "is_active": entity.is_active,
            }
        }
    finally:
        db.close()


@app.delete("/entities/{entity_id}")
def archive_entity(entity_id: str):
    """
    Archive an entity (soft delete - sets is_active = False).
    Entity and associations are preserved but hidden from active lists.
    """
    from app.models import Entity

    db = SessionLocal()
    try:
        entity = db.query(Entity).filter(Entity.id == entity_id).first()

        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")

        entity.is_active = False
        entity.updated_at = datetime.now(timezone.utc)

        db.commit()

        return {"ok": True, "message": f"Entity '{entity.entity_name}' archived"}
    finally:
        db.close()


@app.get("/dashboard")
def ui_dashboard(request: Request):
    """
    Dashboard page showing insights (Layer 3).
    Displays proactive insights, patterns, and upcoming dates.
    """
    insights = get_active_insights()

    # Group insights by priority
    high_priority = [i for i in insights if i["priority"] == "high"]
    medium_priority = [i for i in insights if i["priority"] == "medium"]
    low_priority = [i for i in insights if i["priority"] == "low"]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "insights": insights,
            "high_priority": high_priority,
            "medium_priority": medium_priority,
            "low_priority": low_priority,
            "ai_enabled": AI_ENABLED,
        },
    )


@app.get("/actions")
def ui_actions(request: Request, filter: str = "active"):
    """
    Actions/Todo list page showing category intelligence insights.
    Shows actionable items that need to be resolved.
    """
    db = SessionLocal()
    try:
        from app.models import Insight
        import json

        # Query based on filter
        query = db.query(Insight).filter(Insight.insight_type == "category_intelligence")

        if filter == "active":
            query = query.filter(Insight.status == "active")
        elif filter == "resolved":
            query = query.filter(Insight.status == "resolved")
        # "all" shows everything

        insights_raw = query.order_by(
            Insight.priority.desc(),
            Insight.generated_at.desc()
        ).all()

        # Format insights
        actions = []
        for insight in insights_raw:
            metadata = json.loads(insight.insight_metadata) if insight.insight_metadata else {}

            actions.append({
                "id": insight.id,
                "type": insight.insight_type,
                "priority": insight.priority,
                "status": insight.status,
                "title": insight.title,
                "description": insight.description,
                "action": insight.action,
                "category": metadata.get("category", "unknown"),
                "urgency_days": metadata.get("urgency_days"),
                "generated_at": insight.generated_at.strftime("%d %b %Y"),
            })

        # Count stats
        total_active = db.query(Insight).filter(
            Insight.insight_type == "category_intelligence",
            Insight.status == "active"
        ).count()

        total_resolved = db.query(Insight).filter(
            Insight.insight_type == "category_intelligence",
            Insight.status == "resolved"
        ).count()

        return templates.TemplateResponse(
            "actions.html",
            {
                "request": request,
                "actions": actions,
                "filter": filter,
                "total_active": total_active,
                "total_resolved": total_resolved,
                "ai_enabled": AI_ENABLED,
            },
        )
    finally:
        db.close()


@app.get("/category/{category_id}")
def ui_category_detail(request: Request, category_id: str):
    """
    Category Detail Page - Shows documents, insights, and actions for a specific category.
    """
    from app.category_intelligence import generate_category_overview
    import json

    db = SessionLocal()
    try:
        # Get category overview data
        overview = generate_category_overview()

        if category_id not in overview["categories"]:
            raise HTTPException(status_code=404, detail="Category not found")

        category = overview["categories"][category_id]

        # Get documents in this category
        documents = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == category_id
            )
            .order_by(Item.created_at.desc())
            .limit(50)
            .all()
        )

        doc_list = []
        for item, summary in documents:
            doc_list.append({
                "id": item.id,
                "filename": item.original_filename,
                "summary": summary.summary_text,
                "document_type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "date": summary.extracted_date,
                "amount": summary.extracted_amount,
                "entity_id": summary.entity_id,
                "created_at": item.created_at.isoformat(),
            })

        # Get insights for this category
        insights = (
            db.query(Insight)
            .filter(
                Insight.status == "active",
                Insight.insight_type == "category_intelligence"
            )
            .order_by(
                Insight.priority.desc(),
                Insight.generated_at.desc()
            )
            .all()
        )

        # Filter insights for this category
        category_insights = []
        for insight in insights:
            if insight.insight_metadata:
                try:
                    metadata = json.loads(insight.insight_metadata)
                    if metadata.get("category") == category_id:
                        category_insights.append({
                            "id": insight.id,
                            "title": insight.title,
                            "description": insight.description,
                            "action": insight.action,
                            "priority": insight.priority,
                            "generated_at": insight.generated_at.isoformat(),
                        })
                except:
                    pass

        return templates.TemplateResponse(
            "category-detail.html",
            {
                "request": request,
                "category_id": category_id,
                "category": category,
                "documents": doc_list,
                "insights": category_insights,
                "ai_enabled": AI_ENABLED,
            },
        )
    finally:
        db.close()


@app.get("/categories")
def ui_categories(request: Request):
    """
    Category Overview Dashboard - Master control panel showing all categories.
    Displays document counts, insights, status, and overall life admin health.
    """
    from app.category_intelligence import generate_category_overview

    overview = generate_category_overview()

    # Sort categories by status priority (urgent first) then by doc count
    status_priority = {"urgent": 0, "warning": 1, "info": 2, "good": 3, "empty": 4}
    sorted_categories = sorted(
        overview["categories"].items(),
        key=lambda x: (status_priority.get(x[1]["status"], 5), -x[1]["doc_count"])
    )

    return templates.TemplateResponse(
        "categories.html",
        {
            "request": request,
            "overview": overview,
            "sorted_categories": sorted_categories,
            "ai_enabled": AI_ENABLED,
        },
    )


@app.get("/agents")
def ui_agents(request: Request):
    """
    Agent Portfolio Dashboard - Shows all intelligence agents.
    Displays agent metadata, capabilities, and migration status.
    """
    from app.agents import get_registry

    registry = get_registry()
    agents = registry.list_agents()

    # Group agents by license type
    agents_by_license = {}
    for agent in agents:
        license_type = agent['license_type']
        agents_by_license.setdefault(license_type, []).append(agent)

    # Calculate migration status
    total_categories = 14  # We have 14 category analyzers
    migrated_count = len([a for a in agents if a['id'].startswith('core.')])
    migration_progress = (migrated_count / total_categories * 100) if total_categories > 0 else 0

    return templates.TemplateResponse(
        "agents.html",
        {
            "request": request,
            "agents": agents,
            "agents_by_license": agents_by_license,
            "total_agents": len(agents),
            "migrated_count": migrated_count,
            "total_categories": total_categories,
            "migration_progress": migration_progress,
            "ai_enabled": AI_ENABLED,
        },
    )


@app.get("/entities-manage")
def ui_entities_manage(request: Request):
    """
    Entity Management UI - Manage family members, vehicles, pets, properties.
    """
    from app.models import Entity

    db = SessionLocal()
    try:
        # Get all active entities
        entities = db.query(Entity).filter(Entity.is_active == True).order_by(Entity.entity_type, Entity.entity_name).all()

        # Group by entity type
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.entity_type
            entities_by_type.setdefault(entity_type, []).append({
                "id": entity.id,
                "name": entity.entity_name,
                "identifier": entity.entity_identifier,
                "metadata": entity.entity_metadata,
                "owner_id": entity.owner_id,
                "document_count": db.query(AISummary).filter(AISummary.entity_id == entity.id).count(),
                "created_at": entity.created_at.isoformat(),
            })

        # Count total documents and insights per entity type
        type_stats = {}
        for entity_type, entity_list in entities_by_type.items():
            total_docs = sum(e["document_count"] for e in entity_list)
            type_stats[entity_type] = {
                "count": len(entity_list),
                "total_docs": total_docs,
            }

        # Entity type metadata
        entity_type_info = {
            "person": {"icon": "👤", "label": "People", "color": "blue"},
            "vehicle": {"icon": "🚗", "label": "Vehicles", "color": "orange"},
            "pet": {"icon": "🐾", "label": "Pets", "color": "green"},
            "property": {"icon": "🏠", "label": "Properties", "color": "purple"},
            "business": {"icon": "💼", "label": "Businesses", "color": "gray"},
            "family": {"icon": "👨‍👩‍👧‍👦", "label": "Family/Groups", "color": "teal"},
        }

        return templates.TemplateResponse(
            "entities-manage.html",
            {
                "request": request,
                "entities_by_type": entities_by_type,
                "type_stats": type_stats,
                "entity_type_info": entity_type_info,
                "total_entities": len(entities),
            },
        )
    finally:
        db.close()


@app.post("/ui/upload")
async def ui_upload(file: UploadFile = File(...)):
    # reuse the existing upload logic by calling the API function directly
    await upload(file)  # calls your /intake/upload handler
    return RedirectResponse(url="/", status_code=303)


from fastapi import Query
from sqlalchemy import or_


@app.delete("/items/{item_id}")
def delete_item(item_id: str):
    """
    Soft delete an item. Marks it as deleted but doesn't remove from storage.
    Preserves data integrity while allowing cleanup of unwanted items.
    """
    db = SessionLocal()
    try:
        item = db.query(Item).filter(Item.id == item_id, Item.deleted_at.is_(None)).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Soft delete - mark as deleted but don't remove from R2
        item.deleted_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "ok": True,
            "id": item_id,
            "message": "Item marked as deleted",
        }
    finally:
        db.close()


@app.get("/download/{item_id}")
def download(item_id: str):
    """Generate presigned URL and redirect to download an item from R2."""
    db = SessionLocal()
    try:
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item or item.deleted_at:
            raise HTTPException(status_code=404, detail="Item not found")

        # Generate presigned URL (5 minutes expiry)
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': item.bucket,
                'Key': item.object_key,
                'ResponseContentType': item.content_type or 'application/octet-stream',
                'ResponseContentDisposition': f'attachment; filename="{item.original_filename}"'
            },
            ExpiresIn=300
        )

        return RedirectResponse(url=presigned_url, status_code=307)
    finally:
        db.close()


@app.get("/preview/{item_id}")
def preview(item_id: str):
    """Generate presigned URL for inline preview (no download prompt)."""
    db = SessionLocal()
    try:
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item or item.deleted_at:
            raise HTTPException(status_code=404, detail="Item not found")

        # Generate presigned URL with inline disposition (15 minutes expiry)
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': item.bucket,
                'Key': item.object_key,
                'ResponseContentType': item.content_type or 'application/octet-stream',
                'ResponseContentDisposition': 'inline'
            },
            ExpiresIn=900  # 15 minutes for preview
        )

        return {
            "ok": True,
            "url": presigned_url,
            "content_type": item.content_type,
            "filename": item.original_filename
        }
    finally:
        db.close()


@app.patch("/items/{item_id}/category")
def update_item_category(item_id: str, new_category: str):
    """
    Update an item's category and track the correction for learning.

    Args:
        item_id: The item ID
        new_category: The new category to assign
    """
    from app.models import CategoryCorrection
    from app.categorization import CATEGORIES

    # Validate category
    if new_category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {', '.join(CATEGORIES)}")

    db = SessionLocal()
    try:
        # Get item and its summary
        item = db.query(Item).filter(Item.id == item_id, Item.deleted_at.is_(None)).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        summary = db.query(AISummary).filter(AISummary.item_id == item_id).first()
        if not summary:
            # Create summary if it doesn't exist
            summary = AISummary(
                item_id=item_id,
                category=new_category,
                model_version="manual",
                generated_at=datetime.now(timezone.utc)
            )
            db.add(summary)
        else:
            old_category = summary.category

            # Track the correction for learning
            if old_category != new_category:
                correction = CategoryCorrection(
                    item_id=item_id,
                    old_category=old_category,
                    new_category=new_category,
                    document_type=summary.document_type,
                    vendor=summary.extracted_vendor,
                    filename=item.original_filename,
                    corrected_at=datetime.now(timezone.utc)
                )
                db.add(correction)

            # Update category
            summary.category = new_category

        db.commit()

        return {
            "ok": True,
            "item_id": item_id,
            "new_category": new_category,
            "message": "Category updated successfully"
        }

    finally:
        db.close()


@app.get("/items/search")
def search(q: str = Query(..., min_length=1), limit: int = 25):
    limit = max(1, min(limit, 100))
    q_like = f"%{q}%"

    db = SessionLocal()
    try:
        items = (
            db.query(Item)
            .filter(
                Item.deleted_at.is_(None),
                or_(
                    Item.original_filename.ilike(q_like),
                    Item.extracted_text.ilike(q_like),
                )
            )
            .order_by(Item.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": i.id,
                "original_filename": i.original_filename,
                "content_type": i.content_type,
                "bucket": i.bucket,
                "object_key": i.object_key,
                "size_bytes": i.size_bytes,
                "created_at": i.created_at.isoformat(),
                "parent_id": i.parent_id,
                "source_type": i.source_type,
                "source_id": i.source_id,
            }
            for i in items
        ]
    finally:
        db.close()
