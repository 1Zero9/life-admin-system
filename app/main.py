import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.client import Config
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from app.db import Base, engine, SessionLocal
from app.models import Item

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
            }
            for i in items
        ]
    finally:
        db.close()

from fastapi import Query

@app.get("/items/search")
def search(q: str = Query(..., min_length=1), limit: int = 25):
    limit = max(1, min(limit, 100))
    q_like = f"%{q}%"

    db = SessionLocal()
    try:
        items = (
            db.query(Item)
            .filter(Item.original_filename.ilike(q_like))
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
            }
            for i in items
        ]
    finally:
        db.close()
