"""
Document Categorization - Uses Claude to intelligently categorize documents into life admin categories.

Categories:
- vehicle: Car-related (insurance, NCT, service, fuel, parking, fines)
- medical: Health documents (hospital, clinic, pharmacy, prescriptions, test results)
- home: Property-related (mortgage, rent, solicitor, property tax, home maintenance)
- utilities: Household services (electricity, gas, water, broadband, phone)
- financial: Banking and investments (bank statements, loans, credit cards, savings, pensions)
- insurance: Insurance policies (not car or home - general insurance)
- employment: Work-related (payslips, contracts, P60, employment letters)
- tax: Tax documents (tax returns, tax certs, revenue correspondence)
- legal: Legal documents (contracts, legal letters, court documents)
- education: Education-related (school fees, college, courses, certificates)
- travel: Travel documents (bookings, tickets, visas, travel insurance)
- shopping: General purchases (receipts, orders, warranties)
- government: Government correspondence (forms, licenses, permits, official letters)
- personal: Personal documents that don't fit other categories
- other: Uncategorized
"""

import os
from typing import Optional

from app.db import SessionLocal
from app.models import Item, AISummary

# Check if AI is enabled
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
AI_ENABLED = bool(ANTHROPIC_API_KEY)

if AI_ENABLED:
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    MODEL = "claude-sonnet-4-20250514"

# Standard categories
CATEGORIES = [
    "vehicle", "medical", "home", "utilities", "financial", "insurance",
    "employment", "tax", "legal", "education", "travel", "shopping",
    "government", "personal", "other"
]


def get_recent_corrections(limit: int = 20) -> list:
    """
    Get recent category corrections to help AI learn from user feedback.
    Returns list of correction examples with context.
    """
    db = SessionLocal()
    try:
        from app.models import CategoryCorrection

        corrections = (
            db.query(CategoryCorrection)
            .order_by(CategoryCorrection.corrected_at.desc())
            .limit(limit)
            .all()
        )

        examples = []
        for correction in corrections:
            examples.append({
                "filename": correction.filename,
                "document_type": correction.document_type,
                "vendor": correction.vendor,
                "ai_suggested": correction.old_category,
                "user_corrected_to": correction.new_category
            })

        return examples
    finally:
        db.close()


def categorize_document(item_id: str) -> Optional[str]:
    """
    Categorize a single document using Claude.
    Returns the category string or None if categorization failed.

    Learns from user corrections by including recent correction examples in the prompt.
    """
    if not AI_ENABLED:
        return None

    db = SessionLocal()
    try:
        # Get the item and its summary
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            return None

        summary = db.query(AISummary).filter(AISummary.item_id == item_id).first()

        # Prepare context for Claude
        context = {
            "filename": item.original_filename,
            "extracted_text": item.extracted_text[:2000] if item.extracted_text else ""
        }

        if summary:
            context["document_type"] = summary.document_type
            context["vendor"] = summary.extracted_vendor
            context["summary"] = summary.summary_text

        # Get recent corrections to learn from user feedback
        corrections = get_recent_corrections(limit=15)

        # Build correction examples section
        correction_section = ""
        if corrections:
            correction_section = "\n\nIMPORTANT - Learn from these user corrections:\n"
            correction_section += "The user has manually corrected categories for these documents. Use these as examples to improve accuracy:\n\n"
            for i, corr in enumerate(corrections[:10], 1):  # Show max 10 examples
                if corr["ai_suggested"] and corr["user_corrected_to"] != corr["ai_suggested"]:
                    correction_section += f"{i}. '{corr['filename']}' (Type: {corr['document_type']}, Vendor: {corr['vendor']})\n"
                    correction_section += f"   AI suggested: {corr['ai_suggested']} ✗\n"
                    correction_section += f"   User corrected to: {corr['user_corrected_to']} ✓\n\n"

        prompt = f"""Categorize this document into ONE of the following life admin categories:

Categories:
- vehicle: Car/transport (insurance, NCT, service, fuel, parking, fines)
- medical: Health (hospital, clinic, pharmacy, prescriptions, tests)
- home: Property (mortgage, rent, solicitor, property tax, maintenance)
- utilities: Services (electricity, gas, water, broadband, phone)
- financial: Banking (statements, loans, credit cards, savings, pensions)
- insurance: General insurance policies (not car/home)
- employment: Work (payslips, contracts, P60, letters)
- tax: Tax documents (returns, certs, revenue letters)
- legal: Legal (contracts, court, legal letters)
- education: Education (fees, courses, certificates)
- travel: Travel (bookings, tickets, visas)
- shopping: Purchases (receipts, orders, warranties)
- government: Government (forms, licenses, permits, official letters)
- personal: Personal documents
- other: Uncategorized
{correction_section}
Document info:
Filename: {context['filename']}
Type: {context.get('document_type', 'unknown')}
Vendor: {context.get('vendor', 'unknown')}
Summary: {context.get('summary', 'none')}
Content preview: {context['extracted_text'][:500]}

Respond with ONLY the category name, nothing else."""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )

            category = message.content[0].text.strip().lower()

            # Validate category
            if category in CATEGORIES:
                # Update the summary with the category
                if summary:
                    summary.category = category
                    db.commit()
                    return category
            else:
                # Invalid category, default to "other"
                if summary:
                    summary.category = "other"
                    db.commit()
                return "other"

        except Exception as e:
            print(f"Error calling Claude for categorization: {e}")
            return None

    finally:
        db.close()


def categorize_all_documents():
    """
    Categorize all documents that don't have a category yet.
    Returns the count of documents categorized.
    """
    if not AI_ENABLED:
        print("AI features disabled - set ANTHROPIC_API_KEY to enable")
        return 0

    db = SessionLocal()
    try:
        # Get all items with summaries but no category
        items = (
            db.query(Item)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category.is_(None)
            )
            .all()
        )

        print(f"Categorizing {len(items)} documents...")

        categorized = 0
        for item in items:
            category = categorize_document(item.id)
            if category:
                categorized += 1
                print(f"  {item.original_filename[:50]:<50} → {category}")

        print(f"\n✓ Categorized {categorized} documents")
        return categorized

    finally:
        db.close()


def get_category_stats():
    """Get statistics about document categories."""
    db = SessionLocal()
    try:
        from sqlalchemy import func

        stats = (
            db.query(AISummary.category, func.count(AISummary.id))
            .filter(AISummary.category.isnot(None))
            .group_by(AISummary.category)
            .order_by(func.count(AISummary.id).desc())
            .all()
        )

        # Get total uncategorized
        uncategorized = (
            db.query(func.count(Item.id))
            .outerjoin(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category.is_(None)
            )
            .scalar()
        )

        return {
            "categories": [{"category": cat, "count": count} for cat, count in stats],
            "uncategorized": uncategorized or 0
        }

    finally:
        db.close()
