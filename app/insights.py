"""
Insight generation engine - Layer 3 feature.
Analyzes documents and AI summaries to generate proactive insights.
"""

import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

from app.db import SessionLocal
from app.models import Item, AISummary, Insight


def clear_expired_insights():
    """Remove insights that have expired or been dismissed."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Delete expired insights
        db.query(Insight).filter(Insight.expires_at < now).delete()

        # Delete old dismissed insights (> 30 days)
        thirty_days_ago = now - timedelta(days=30)
        db.query(Insight).filter(
            Insight.dismissed_at.isnot(None),
            Insight.dismissed_at < thirty_days_ago
        ).delete()

        db.commit()
    finally:
        db.close()


def generate_vendor_patterns():
    """
    Detect recurring vendors and generate spending summaries.
    Insight type: 'pattern'
    """
    db = SessionLocal()
    insights = []

    try:
        # Get all items with AI summaries that have vendors
        items_with_vendors = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.extracted_vendor.isnot(None)
            )
            .all()
        )

        # Group by vendor
        vendor_data = defaultdict(list)
        for item, summary in items_with_vendors:
            vendor = summary.extracted_vendor
            vendor_data[vendor].append({
                "item_id": item.id,
                "date": item.created_at,
                "amount": summary.extracted_amount,
                "type": summary.document_type,
            })

        # Generate insights for vendors with 3+ documents
        for vendor, documents in vendor_data.items():
            if len(documents) < 3:
                continue

            # Check if insight already exists for this vendor
            existing = db.query(Insight).filter(
                Insight.insight_type == "pattern",
                Insight.status == "active",
                Insight.insight_metadata.contains(f'"vendor": "{vendor}"')
            ).first()

            if existing:
                continue  # Skip if already exists

            # Calculate metadata
            doc_count = len(documents)
            amounts = [d["amount"] for d in documents if d["amount"]]
            types = list(set(d["type"] for d in documents if d["type"]))

            insight = Insight(
                insight_type="pattern",
                priority="low",
                title=f"Recurring vendor: {vendor}",
                description=f"You have {doc_count} documents from {vendor}. " +
                           (f"Document types: {', '.join(types)}." if types else ""),
                action=f"View all documents from {vendor}",
                related_items=json.dumps([d["item_id"] for d in documents]),
                insight_metadata=json.dumps({
                    "vendor": vendor,
                    "document_count": doc_count,
                    "amounts": amounts,
                    "types": types,
                })
            )
            insights.append(insight)

        # Save insights
        for insight in insights:
            db.add(insight)
        db.commit()

        return len(insights)

    finally:
        db.close()


def generate_spending_summaries():
    """
    Calculate spending summaries by vendor and time period.
    Insight type: 'summary'
    """
    db = SessionLocal()
    insights = []

    try:
        # Get all receipts/invoices with amounts from last 90 days
        ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)

        items_with_amounts = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                Item.created_at >= ninety_days_ago,
                AISummary.extracted_amount.isnot(None),
                AISummary.document_type.in_(["Receipt", "Invoice", "Bill"])
            )
            .all()
        )

        if len(items_with_amounts) < 5:
            return 0  # Not enough data

        # Check if summary already exists
        existing = db.query(Insight).filter(
            Insight.insight_type == "summary",
            Insight.status == "active",
            Insight.title.contains("Recent spending")
        ).first()

        if existing:
            return 0  # Skip if already exists

        # Group by vendor
        vendor_spending = defaultdict(list)
        for item, summary in items_with_amounts:
            if summary.extracted_vendor:
                vendor_spending[summary.extracted_vendor].append(summary.extracted_amount)

        # Find top vendors by document count
        top_vendors = sorted(
            vendor_spending.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:5]

        top_vendor_summary = ", ".join([f"{v} ({len(amounts)})" for v, amounts in top_vendors])

        insight = Insight(
            insight_type="summary",
            priority="low",
            title=f"Recent spending summary (last 90 days)",
            description=f"You have {len(items_with_amounts)} receipts/invoices. " +
                       f"Top vendors: {top_vendor_summary}",
            action="View all receipts and invoices",
            related_items=json.dumps([item.id for item, _ in items_with_amounts]),
            insight_metadata=json.dumps({
                "period_days": 90,
                "document_count": len(items_with_amounts),
                "top_vendors": dict(top_vendors),
            }),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)  # Refresh weekly
        )

        db.add(insight)
        db.commit()

        return 1

    finally:
        db.close()


def detect_upcoming_dates():
    """
    Find documents with future dates (potential renewals, expiries).
    Insight type: 'renewal'
    """
    db = SessionLocal()
    insights = []

    try:
        # Get items with extracted dates
        items_with_dates = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.extracted_date.isnot(None)
            )
            .all()
        )

        now = datetime.now(timezone.utc)
        ninety_days = now + timedelta(days=90)

        for item, summary in items_with_dates:
            # Try to parse the date (simple parsing for common formats)
            date_str = summary.extracted_date
            parsed_date = parse_date_string(date_str)

            if not parsed_date:
                continue

            # Check if date is in the future but within next 90 days
            if now < parsed_date < ninety_days:
                # Check if insight already exists for this item
                existing = db.query(Insight).filter(
                    Insight.insight_type == "renewal",
                    Insight.status == "active",
                    Insight.related_items.contains(item.id)
                ).first()

                if existing:
                    continue

                days_until = (parsed_date - now).days

                # Determine priority based on how soon
                if days_until <= 7:
                    priority = "high"
                elif days_until <= 30:
                    priority = "medium"
                else:
                    priority = "low"

                doc_type = summary.document_type or "Document"
                vendor = summary.extracted_vendor or "Unknown"

                insight = Insight(
                    insight_type="renewal",
                    priority=priority,
                    title=f"Upcoming date: {vendor} - {date_str}",
                    description=f"{doc_type} from {vendor} has a date of {date_str} ({days_until} days from now).",
                    action="Review document",
                    related_items=json.dumps([item.id]),
                    insight_metadata=json.dumps({
                        "vendor": vendor,
                        "date": date_str,
                        "parsed_date": parsed_date.isoformat(),
                        "days_until": days_until,
                    }),
                    expires_at=parsed_date  # Expires when date passes
                )
                insights.append(insight)

        # Save insights
        for insight in insights:
            db.add(insight)
        db.commit()

        return len(insights)

    finally:
        db.close()


def parse_date_string(date_str: str) -> Optional[datetime]:
    """
    Parse common date formats from AI-extracted dates.
    Returns datetime object in UTC or None if unparseable.
    """
    from dateutil import parser as date_parser

    try:
        # Try parsing with dateutil (handles most formats)
        parsed = date_parser.parse(date_str, fuzzy=True, dayfirst=True)
        # Convert to UTC aware datetime
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None


def generate_all_insights():
    """
    Generate all types of insights.
    Call this periodically (daily via cron).
    """
    print("Generating insights...")

    # Clear expired/old insights first
    clear_expired_insights()
    print("✓ Cleared expired insights")

    # Generate each type of insight
    vendor_count = generate_vendor_patterns()
    print(f"✓ Generated {vendor_count} vendor pattern insights")

    spending_count = generate_spending_summaries()
    print(f"✓ Generated {spending_count} spending summary insights")

    renewal_count = detect_upcoming_dates()
    print(f"✓ Generated {renewal_count} upcoming date insights")

    total = vendor_count + spending_count + renewal_count
    print(f"\nTotal: {total} new insights")
    return total


def get_active_insights() -> List[Dict[str, Any]]:
    """
    Get all active insights for display.
    Returns list of insight dicts ordered by priority and date.
    """
    db = SessionLocal()
    try:
        insights = (
            db.query(Insight)
            .filter(Insight.status == "active")
            .order_by(
                Insight.priority.desc(),  # high, medium, low
                Insight.generated_at.desc()
            )
            .all()
        )

        result = []
        for insight in insights:
            result.append({
                "id": insight.id,
                "type": insight.insight_type,
                "priority": insight.priority,
                "title": insight.title,
                "description": insight.description,
                "action": insight.action,
                "related_items": json.loads(insight.related_items) if insight.related_items else [],
                "metadata": json.loads(insight.insight_metadata) if insight.insight_metadata else {},
                "generated_at": insight.generated_at.isoformat(),
            })

        return result

    finally:
        db.close()


def dismiss_insight(insight_id: str) -> bool:
    """Mark an insight as dismissed."""
    db = SessionLocal()
    try:
        insight = db.query(Insight).filter(Insight.id == insight_id).first()
        if not insight:
            return False

        insight.status = "dismissed"
        insight.dismissed_at = datetime.now(timezone.utc)
        db.commit()
        return True

    finally:
        db.close()
