import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
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

    # Relationship to AI summary (one-to-one)
    ai_summary = relationship("AISummary", back_populates="item", uselist=False, cascade="all, delete-orphan")


class AISummary(Base):
    """
    AI-generated summaries for documents.
    Layer 2 feature - clearly marked as generated, not factual.
    Regenerable and optional.
    """
    __tablename__ = "ai_summaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = Column(String, ForeignKey("items.id"), nullable=False, unique=True)

    # AI-generated fields (all nullable - AI might not extract everything)
    summary_text = Column(Text, nullable=True)  # One-sentence description
    document_type = Column(String, nullable=True)  # Invoice, Receipt, Letter, Statement, etc.
    extracted_date = Column(String, nullable=True)  # Date from content (as string, not parsed)
    extracted_amount = Column(String, nullable=True)  # Cost/amount as string (e.g., "€75.00")
    extracted_vendor = Column(String, nullable=True)  # Vendor/sender name

    # Metadata about the AI generation
    model_version = Column(String, nullable=False)  # e.g., "claude-sonnet-4-20250514"
    generated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationship back to item
    item = relationship("Item", back_populates="ai_summary")
