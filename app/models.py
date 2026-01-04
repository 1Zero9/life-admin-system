import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String
from .db import Base
from sqlalchemy import Column, DateTime, Integer, String, Text


class Item(Base):
    __tablename__ = "items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    bucket = Column(String, nullable=False)
    object_key = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=True)
    extracted_text = Column(Text, nullable=True)
    parent_id = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    source_id = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)  # SHA256 hash for duplicate detection
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime, nullable=True)  # Soft delete - item hidden but not removed
