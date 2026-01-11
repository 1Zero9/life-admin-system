"""
AI-Powered Insights Engine - Uses Claude to analyze documents intelligently.

This module goes beyond simple database queries to provide real GenAI-powered analysis:
- Anomaly detection (unusual bills, duplicate charges)
- Trend analysis (spending patterns, cost changes over time)
- Cross-document intelligence (finding relationships between documents)
- Proactive recommendations (actionable advice based on content)
- Financial intelligence (detailed spending analysis)
"""

import json
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

from app.db import SessionLocal
from app.models import Item, AISummary, Insight

# Check if AI is enabled
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
AI_ENABLED = bool(ANTHROPIC_API_KEY)

if AI_ENABLED:
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    MODEL = "claude-sonnet-4-20250514"


def call_claude(prompt: str, max_tokens: int = 2000) -> str:
    """Call Claude API with a prompt."""
    if not AI_ENABLED:
        return ""

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Error calling Claude: {e}")
        return ""


def detect_bill_anomalies():
    """
    Detect unusual patterns in bills - price spikes, duplicate charges, etc.
    Uses Claude to analyze bill content and spot issues.
    """
    if not AI_ENABLED:
        return 0

    db = SessionLocal()
    insights = []

    try:
        # Get all bills/invoices from last 6 months
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)

        bills = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                Item.created_at >= six_months_ago,
                AISummary.document_type.in_(["Bill", "Invoice", "Receipt"]),
                AISummary.extracted_vendor.isnot(None),
                AISummary.extracted_amount.isnot(None)
            )
            .order_by(AISummary.extracted_vendor, Item.created_at)
            .all()
        )

        # Group by vendor
        vendor_bills = defaultdict(list)
        for item, summary in bills:
            vendor_bills[summary.extracted_vendor].append({
                "item_id": item.id,
                "filename": item.original_filename,
                "date": item.created_at,
                "amount": summary.extracted_amount,
                "text_preview": item.extracted_text[:1000] if item.extracted_text else ""
            })

        # Analyze each vendor's bills for anomalies
        for vendor, vendor_bill_list in vendor_bills.items():
            if len(vendor_bill_list) < 3:
                continue  # Need at least 3 bills to detect patterns

            # Check if insight already exists for this vendor
            existing = db.query(Insight).filter(
                Insight.insight_type == "anomaly",
                Insight.status == "active",
                Insight.insight_metadata.contains(f'"vendor": "{vendor}"')
            ).first()

            if existing:
                continue

            # Prepare data for Claude
            bill_summary = []
            for i, bill in enumerate(vendor_bill_list[-6:]):  # Last 6 bills
                bill_summary.append(f"Bill {i+1}: {bill['date'].strftime('%Y-%m-%d')} - {bill['amount']}")
                if bill['text_preview']:
                    bill_summary.append(f"  Preview: {bill['text_preview'][:200]}...")

            prompt = f"""Analyze these recent bills from {vendor} for anomalies or issues:

{chr(10).join(bill_summary)}

Look for:
1. Unusual price spikes or drops
2. Duplicate charges
3. Billing errors
4. Changed billing patterns
5. Any red flags in the text

If you find a significant anomaly, respond with JSON:
{{
    "anomaly_found": true,
    "severity": "high|medium|low",
    "title": "Brief title of the issue",
    "description": "Detailed explanation of what's wrong",
    "recommendation": "What action should be taken"
}}

If no significant anomalies, respond with:
{{"anomaly_found": false}}
"""

            response = call_claude(prompt, max_tokens=500)

            try:
                result = json.loads(response)

                if result.get("anomaly_found"):
                    # Map severity to priority
                    priority_map = {"high": "high", "medium": "medium", "low": "low"}
                    priority = priority_map.get(result.get("severity", "medium"), "medium")

                    insight = Insight(
                        insight_type="anomaly",
                        priority=priority,
                        title=result["title"],
                        description=result["description"],
                        action=result.get("recommendation", "Review these bills"),
                        related_items=json.dumps([b["item_id"] for b in vendor_bill_list[-6:]]),
                        insight_metadata=json.dumps({
                            "vendor": vendor,
                            "bill_count": len(vendor_bill_list),
                            "analysis_date": datetime.now(timezone.utc).isoformat(),
                            "severity": result.get("severity", "medium")
                        }),
                        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
                    )
                    insights.append(insight)
            except json.JSONDecodeError:
                # Claude didn't return valid JSON, skip
                continue

        # Save insights
        for insight in insights:
            db.add(insight)
        db.commit()

        return len(insights)

    finally:
        db.close()


def analyze_spending_trends():
    """
    Analyze spending trends over time using Claude to provide intelligent commentary.
    Goes beyond simple totals to understand WHY spending changed.
    """
    if not AI_ENABLED:
        return 0

    db = SessionLocal()

    try:
        # Check if insight already exists
        existing = db.query(Insight).filter(
            Insight.insight_type == "trend",
            Insight.status == "active",
            Insight.title.contains("Spending trends")
        ).first()

        if existing:
            return 0

        # Get spending data for last 6 months
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)

        bills = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                Item.created_at >= six_months_ago,
                AISummary.document_type.in_(["Bill", "Invoice", "Receipt"]),
                AISummary.extracted_amount.isnot(None)
            )
            .order_by(Item.created_at)
            .all()
        )

        if len(bills) < 10:
            return 0  # Not enough data

        # Group by month and vendor
        monthly_data = defaultdict(lambda: {"total": 0, "vendors": defaultdict(list)})

        for item, summary in bills:
            month_key = item.created_at.strftime("%Y-%m")
            # Extract numeric amount
            amount_str = summary.extracted_amount
            try:
                # Remove currency symbols and parse
                import re
                amount_match = re.search(r'[\d,]+\.?\d*', amount_str.replace(',', ''))
                if amount_match:
                    amount = float(amount_match.group())
                    monthly_data[month_key]["total"] += amount
                    monthly_data[month_key]["vendors"][summary.extracted_vendor or "Unknown"].append(amount)
            except:
                continue

        # Prepare summary for Claude
        month_summary = []
        for month, data in sorted(monthly_data.items()):
            vendor_summary = []
            for vendor, amounts in sorted(data["vendors"].items(), key=lambda x: sum(x[1]), reverse=True)[:5]:
                vendor_summary.append(f"{vendor}: €{sum(amounts):.2f} ({len(amounts)} bills)")

            month_summary.append(f"{month}: €{data['total']:.2f}")
            month_summary.append(f"  Top vendors: {', '.join(vendor_summary)}")

        prompt = f"""Analyze these spending trends over the last 6 months:

{chr(10).join(month_summary)}

Provide intelligent analysis:
1. What are the major trends? (increasing, decreasing, seasonal patterns)
2. Which vendors are driving changes?
3. Are there any concerns or opportunities?
4. What recommendations would you make?

Respond with JSON:
{{
    "title": "Brief title summarizing the trend",
    "analysis": "Detailed analysis (2-3 paragraphs)",
    "key_findings": ["Finding 1", "Finding 2", "Finding 3"],
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "priority": "high|medium|low"
}}
"""

        response = call_claude(prompt, max_tokens=1000)

        try:
            result = json.loads(response)

            # Build description
            description = result["analysis"]
            if result.get("key_findings"):
                description += "\n\nKey Findings:\n" + "\n".join([f"• {f}" for f in result["key_findings"]])

            # Build action
            action = "Review spending trends"
            if result.get("recommendations"):
                action = result["recommendations"][0]  # Use first recommendation as action

            priority_map = {"high": "high", "medium": "medium", "low": "low"}
            priority = priority_map.get(result.get("priority", "low"), "low")

            insight = Insight(
                insight_type="trend",
                priority=priority,
                title=result["title"],
                description=description,
                action=action,
                related_items=json.dumps([item.id for item, _ in bills]),
                insight_metadata=json.dumps({
                    "analysis_period": "6 months",
                    "document_count": len(bills),
                    "key_findings": result.get("key_findings", []),
                    "recommendations": result.get("recommendations", []),
                    "analysis_date": datetime.now(timezone.utc).isoformat()
                }),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30)
            )

            db.add(insight)
            db.commit()

            return 1
        except json.JSONDecodeError:
            return 0

    finally:
        db.close()


def find_document_relationships():
    """
    Use Claude to find relationships between documents that aren't obvious from metadata alone.
    E.g., multiple documents related to same event, cross-references, missing documents.
    """
    if not AI_ENABLED:
        return 0

    db = SessionLocal()
    insights = []

    try:
        # Get all recent documents with summaries
        recent = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                Item.extracted_text.isnot(None)
            )
            .order_by(Item.created_at.desc())
            .limit(50)  # Last 50 documents
            .all()
        )

        if len(recent) < 10:
            return 0

        # Prepare document summaries for Claude
        doc_summaries = []
        for item, summary in recent:
            doc_summaries.append({
                "id": item.id,
                "filename": item.original_filename,
                "date": item.created_at.strftime("%Y-%m-%d"),
                "type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "summary": summary.summary_text,
                "text_preview": item.extracted_text[:300] if item.extracted_text else ""
            })

        # Ask Claude to find relationships
        prompt = f"""Analyze these documents and find meaningful relationships between them:

{json.dumps(doc_summaries, indent=2)}

Look for:
1. Documents that are part of the same transaction/event (e.g., quote → invoice → receipt)
2. Documents that reference each other
3. Missing documents in a sequence
4. Related but separate matters (e.g., multiple bills for same service)
5. Unusual patterns or connections

For each significant relationship found, respond with an item in this JSON array:
[
    {{
        "title": "Brief description of relationship",
        "description": "Detailed explanation of how these documents are related and why it matters",
        "document_ids": ["id1", "id2", "id3"],
        "relationship_type": "sequence|cross-reference|missing|pattern",
        "priority": "high|medium|low",
        "recommendation": "What action to take"
    }}
]

If no significant relationships found, return: []
"""

        response = call_claude(prompt, max_tokens=1500)

        try:
            relationships = json.loads(response)

            for rel in relationships:
                # Check if similar insight already exists
                existing = db.query(Insight).filter(
                    Insight.insight_type == "relationship",
                    Insight.status == "active",
                    Insight.title == rel["title"]
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(rel.get("priority", "low"), "low")

                insight = Insight(
                    insight_type="relationship",
                    priority=priority,
                    title=rel["title"],
                    description=rel["description"],
                    action=rel.get("recommendation", "Review related documents"),
                    related_items=json.dumps(rel["document_ids"]),
                    insight_metadata=json.dumps({
                        "relationship_type": rel.get("relationship_type", "pattern"),
                        "analysis_date": datetime.now(timezone.utc).isoformat()
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60)
                )
                insights.append(insight)
        except json.JSONDecodeError:
            return 0

        # Save insights
        for insight in insights:
            db.add(insight)
        db.commit()

        return len(insights)

    finally:
        db.close()


def generate_proactive_recommendations():
    """
    Analyze documents to find actionable recommendations.
    E.g., tax issues, missing renewals, optimization opportunities.
    """
    if not AI_ENABLED:
        return 0

    db = SessionLocal()
    insights = []

    try:
        # Get recent documents with full text
        recent = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                Item.extracted_text.isnot(None)
            )
            .order_by(Item.created_at.desc())
            .limit(30)
            .all()
        )

        if len(recent) < 5:
            return 0

        # Prepare document summaries
        doc_summaries = []
        for item, summary in recent:
            doc_summaries.append({
                "id": item.id,
                "filename": item.original_filename,
                "date": item.created_at.strftime("%Y-%m-%d"),
                "type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "amount": summary.extracted_amount,
                "summary": summary.summary_text,
                "key_content": item.extracted_text[:500] if item.extracted_text else ""
            })

        prompt = f"""Review these documents and provide proactive recommendations for action:

{json.dumps(doc_summaries, indent=2)}

Look for:
1. Issues requiring urgent attention (tax problems, overdue bills, etc.)
2. Optimization opportunities (could save money, consolidate services, etc.)
3. Missing or incomplete information
4. Upcoming deadlines or renewals
5. Risks or concerns that should be addressed

For each actionable recommendation, respond with an item in this JSON array:
[
    {{
        "title": "Clear, action-oriented title",
        "issue": "What's the problem or opportunity?",
        "impact": "Why does this matter?",
        "recommendation": "Specific action to take",
        "related_document_ids": ["id1", "id2"],
        "priority": "high|medium|low",
        "urgency": "How urgent is this?"
    }}
]

Only include genuinely important recommendations. Return [] if nothing significant found.
"""

        response = call_claude(prompt, max_tokens=1500)

        try:
            recommendations = json.loads(response)

            for rec in recommendations:
                # Check if similar insight exists
                existing = db.query(Insight).filter(
                    Insight.insight_type == "recommendation",
                    Insight.status == "active",
                    Insight.title == rec["title"]
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(rec.get("priority", "medium"), "medium")

                description = f"{rec['issue']}\n\n{rec['impact']}"
                if rec.get('urgency'):
                    description += f"\n\nUrgency: {rec['urgency']}"

                insight = Insight(
                    insight_type="recommendation",
                    priority=priority,
                    title=rec["title"],
                    description=description,
                    action=rec["recommendation"],
                    related_items=json.dumps(rec.get("related_document_ids", [])),
                    insight_metadata=json.dumps({
                        "urgency": rec.get("urgency", ""),
                        "analysis_date": datetime.now(timezone.utc).isoformat()
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=30)
                )
                insights.append(insight)
        except json.JSONDecodeError:
            return 0

        # Save insights
        for insight in insights:
            db.add(insight)
        db.commit()

        return len(insights)

    finally:
        db.close()


def generate_all_ai_insights():
    """
    Generate all AI-powered insights.
    This should be run periodically (e.g., daily) or on-demand.
    """
    if not AI_ENABLED:
        print("AI features disabled - set ANTHROPIC_API_KEY to enable")
        return 0

    print("Generating AI-powered insights...")

    # Run each insight generator
    anomaly_count = detect_bill_anomalies()
    print(f"✓ Detected {anomaly_count} bill anomalies")

    trend_count = analyze_spending_trends()
    print(f"✓ Generated {trend_count} spending trend insights")

    relationship_count = find_document_relationships()
    print(f"✓ Found {relationship_count} document relationships")

    recommendation_count = generate_proactive_recommendations()
    print(f"✓ Generated {recommendation_count} proactive recommendations")

    total = anomaly_count + trend_count + relationship_count + recommendation_count
    print(f"\nTotal: {total} new AI-powered insights")

    return total
