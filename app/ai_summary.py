"""
AI summary generation for documents.
Layer 2 feature - clearly marked as generated, not factual.
"""

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from anthropic import Anthropic
from dotenv import load_dotenv

from app.db import SessionLocal
from app.models import Item, AISummary

load_dotenv()

# Model version for tracking - using Haiku for cost-effective structured extraction
CLAUDE_MODEL = "claude-3-5-haiku-20241022"

# Check if API key is configured
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
AI_ENABLED = bool(ANTHROPIC_API_KEY)

if AI_ENABLED:
    anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
else:
    anthropic_client = None


def generate_summary(item_id: str) -> Optional[Dict[str, Any]]:
    """
    Generate AI summary for an item.
    Returns summary data dict or None if generation fails.
    """
    if not AI_ENABLED:
        return None

    db = SessionLocal()
    try:
        # Get the item
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            return None

        # Check if item has extracted text
        if not item.extracted_text:
            return None

        # Build the prompt
        prompt = f"""You are analysing a document for a household document management system.

The document text is below. Generate a structured summary with the following fields:

1. summary: A single sentence describing what this document is (in plain language for a family)
2. document_type: The type of document (e.g., Invoice, Receipt, Letter, Statement, Bill, Insurance, Medical, etc.)
3. extracted_date: Any date mentioned in the document (as a string, e.g., "3 January 2026")
4. extracted_amount: Any monetary amount (as a string with currency, e.g., "€75.00" or "$20.00")
5. extracted_vendor: The name of the company, organization, or person who issued this document

If any field cannot be determined, use null.

Return ONLY a JSON object with these exact keys. No other text.

Document text:
{item.extracted_text[:3000]}
"""

        # Call Claude API
        response = anthropic_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse response
        response_text = response.content[0].text.strip()

        # Try to extract JSON from response
        try:
            # Sometimes Claude wraps JSON in markdown code blocks
            if response_text.startswith("```"):
                # Extract content between ``` markers
                lines = response_text.split("\n")
                json_lines = []
                in_code = False
                for line in lines:
                    if line.strip().startswith("```"):
                        if in_code:
                            break
                        in_code = True
                        continue
                    if in_code:
                        json_lines.append(line)
                response_text = "\n".join(json_lines)

            summary_data = json.loads(response_text)
        except json.JSONDecodeError:
            print(f"Failed to parse Claude response as JSON: {response_text[:200]}")
            return None

        # Delete existing summary if present
        existing = db.query(AISummary).filter(AISummary.item_id == item_id).first()
        if existing:
            db.delete(existing)
            db.flush()  # Ensure delete is committed before insert

        # Create new summary
        ai_summary = AISummary(
            item_id=item_id,
            summary_text=summary_data.get("summary"),
            document_type=summary_data.get("document_type"),
            extracted_date=summary_data.get("extracted_date"),
            extracted_amount=summary_data.get("extracted_amount"),
            extracted_vendor=summary_data.get("extracted_vendor"),
            model_version=CLAUDE_MODEL,
            generated_at=datetime.now(timezone.utc),
        )

        db.add(ai_summary)
        db.commit()
        db.refresh(ai_summary)

        return {
            "id": ai_summary.id,
            "summary_text": ai_summary.summary_text,
            "document_type": ai_summary.document_type,
            "extracted_date": ai_summary.extracted_date,
            "extracted_amount": ai_summary.extracted_amount,
            "extracted_vendor": ai_summary.extracted_vendor,
            "model_version": ai_summary.model_version,
            "generated_at": ai_summary.generated_at.isoformat(),
        }

    except Exception as e:
        print(f"Error generating AI summary: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def delete_summary(item_id: str) -> bool:
    """Delete AI summary for an item. Returns True if deleted."""
    db = SessionLocal()
    try:
        summary = db.query(AISummary).filter(AISummary.item_id == item_id).first()
        if summary:
            db.delete(summary)
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_summary(item_id: str) -> Optional[Dict[str, Any]]:
    """Get existing AI summary for an item."""
    db = SessionLocal()
    try:
        summary = db.query(AISummary).filter(AISummary.item_id == item_id).first()
        if not summary:
            return None

        return {
            "id": summary.id,
            "summary_text": summary.summary_text,
            "document_type": summary.document_type,
            "extracted_date": summary.extracted_date,
            "extracted_amount": summary.extracted_amount,
            "extracted_vendor": summary.extracted_vendor,
            "model_version": summary.model_version,
            "generated_at": summary.generated_at.isoformat(),
        }
    finally:
        db.close()
