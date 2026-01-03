import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import tempfile
from app.extractors import extract_pdf_text

import boto3
from botocore.client import Config
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from app.db import Base, engine, SessionLocal
from app.models import Item
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates




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


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/intake/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    object_key = build_object_key(file.filename)
    content_type = file.content_type or "application/octet-stream"

    extracted_text = None
    is_pdf = (content_type == "application/pdf") or (file.filename.lower().endswith(".pdf"))

    if is_pdf:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            file.file.seek(0)
            tmp.write(file.file.read())
            tmp.flush()
            extracted_text = extract_pdf_text(tmp.name)

        file.file.seek(0)

    # Try get size without reading the whole file
    size_bytes = None
    try:
        size_bytes = os.fstat(file.file.fileno()).st_size
    except Exception:
        pass

    try:
        s3.upload_fileobj(
            Fileobj=file.file,
            Bucket=R2_BUCKET,
            Key=object_key,
            ExtraArgs={"ContentType": content_type},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}") from e

    db = SessionLocal()
    try:
        item = Item(
            original_filename=file.filename,
            content_type=content_type,
            bucket=R2_BUCKET,
            object_key=object_key,
            size_bytes=size_bytes,
            extracted_text=extracted_text,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
    finally:
        db.close()

    return {
        "ok": True,
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
def ui_home(request: Request, q: str | None = None):
    items = None
    if q:
        q_like = f"%{q}%"
        db = SessionLocal()
        try:
            items = (
                db.query(Item)
                .filter(Item.original_filename.ilike(q_like))
                .order_by(Item.created_at.desc())
                .limit(25)
                .all()
            )
        finally:
            db.close()

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "q": q, "items": items},
    )


@app.post("/ui/upload")
async def ui_upload(file: UploadFile = File(...)):
    # reuse the existing upload logic by calling the API function directly
    await upload(file)  # calls your /intake/upload handler
    return RedirectResponse(url="/", status_code=303)


from fastapi import Query
from sqlalchemy import or_

@app.get("/items/search")
def search(q: str = Query(..., min_length=1), limit: int = 25):
    limit = max(1, min(limit, 100))
    q_like = f"%{q}%"

    db = SessionLocal()
    try:
        items = (
            db.query(Item)
            .filter(or_(
                Item.original_filename.ilike(q_like),
                Item.extracted_text.ilike(q_like),
            ))
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
