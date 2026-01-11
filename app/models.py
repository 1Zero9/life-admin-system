import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Float, Boolean, JSON
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


class Entity(Base):
    """
    Represents a person, vehicle, pet, property, or any trackable entity in the system.
    Enables multi-person/multi-asset family intelligence.

    Examples:
    - Person: Stephen, Lauren, children
    - Vehicle: Car 1 (161-D-12345), Car 2 (182-KE-67890)
    - Pet: Buddy the dog
    - Property: Family home, rental property
    - Group: "Family" (for shared items)
    """
    __tablename__ = "entities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Core identity
    entity_type = Column(String, nullable=False)  # person, vehicle, pet, property, business, family
    entity_name = Column(String, nullable=False)  # Display name: "Stephen", "Toyota Corolla", "Buddy"
    entity_identifier = Column(String, nullable=True)  # Unique ID: registration, email, address, etc.

    # Flexible metadata (type-specific data stored as JSON)
    entity_metadata = Column(JSON, nullable=True)  # {
                                                    #   "person": {"relation": "self", "email": "..."},
                                                    #   "vehicle": {"make": "Toyota", "model": "Corolla", "year": 2015},
                                                    #   "pet": {"species": "dog", "breed": "Labrador"}
                                                    # }

    # Ownership/relationships
    owner_id = Column(String, ForeignKey("entities.id"), nullable=True)  # FK to another entity (car owned by person)
    owner = relationship("Entity", remote_side=[id], backref="owned_entities")

    # Status
    is_active = Column(Boolean, nullable=False, default=True)  # Can archive (sold car, moved out, etc.)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


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
    category = Column(String, nullable=True)  # Life admin category (vehicle, medical, home, utilities, etc.)

    # Entity association (who/what this document is about)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=True)  # Linked entity (person, vehicle, etc.)
    entity_confidence = Column(Float, nullable=True)  # AI confidence in entity match (0.0-1.0)
    suggested_entity_data = Column(JSON, nullable=True)  # If no match, AI suggests new entity: {"type": "vehicle", "name": "Car 161-D-12345", ...}

    # Metadata about the AI generation
    model_version = Column(String, nullable=False)  # e.g., "claude-sonnet-4-20250514"
    generated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    item = relationship("Item", back_populates="ai_summary")
    entity = relationship("Entity", foreign_keys=[entity_id])


class Insight(Base):
    """
    Generated insights - Layer 3 feature.
    Patterns, anomalies, and proactive suggestions.
    Regenerable and dismissable.
    """
    __tablename__ = "insights"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Insight type and priority
    insight_type = Column(String, nullable=False)  # renewal, pattern, anomaly, summary
    priority = Column(String, nullable=False)  # high, medium, low
    status = Column(String, nullable=False, default="active")  # active, dismissed, resolved

    # Content
    title = Column(String, nullable=False)  # Short headline
    description = Column(Text, nullable=True)  # Detailed explanation
    action = Column(String, nullable=True)  # Suggested action

    # Related items (JSON array of item IDs)
    related_items = Column(Text, nullable=True)  # JSON: ["id1", "id2"]

    # Entity association (who/what this insight is about)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=True)  # Which entity this insight relates to
    entity_name = Column(String, nullable=True)  # Cached entity name for display
    entity_type = Column(String, nullable=True)  # Cached entity type (person, vehicle, etc.)

    # Metadata
    insight_metadata = Column(Text, nullable=True)  # JSON: additional data for rendering
    generated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)  # When insight is no longer relevant
    dismissed_at = Column(DateTime, nullable=True)  # When user dismissed it

    # Relationships
    entity = relationship("Entity", foreign_keys=[entity_id])


class CategoryCorrection(Base):
    """
    Track manual category corrections for learning.
    When a user manually changes a document's category, we store it here
    so the AI can learn from these corrections.
    """
    __tablename__ = "category_corrections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = Column(String, ForeignKey("items.id"), nullable=False)

    # Correction details
    old_category = Column(String, nullable=True)  # AI's original suggestion (or null if uncategorized)
    new_category = Column(String, nullable=False)  # User's correction

    # Context for learning
    document_type = Column(String, nullable=True)  # Document type at time of correction
    vendor = Column(String, nullable=True)  # Vendor at time of correction
    filename = Column(String, nullable=True)  # Filename at time of correction

    # Metadata
    corrected_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationship to item
    item = relationship("Item", foreign_keys=[item_id])
