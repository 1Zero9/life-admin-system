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
from app.db import Base, engine, SessionLocal
from app.models import Item
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.ui_helpers import normalize_title, format_date_display, format_source_type, get_file_type, get_file_icon_color




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
    return {"ok": True}


@app.post("/intake/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

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
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}") from e

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
    finally:
        db.close()

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
        query = db.query(Item).filter(Item.deleted_at.is_(None))

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
