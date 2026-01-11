"""
Category Intelligence Engine - Provides smart insights by analyzing documents within each category.

For each category, this engine understands:
- What documents should exist (completeness)
- What patterns indicate good organization
- What gaps or risks exist
- What actions should be taken

This goes beyond simple counting to provide intelligent, actionable analysis.
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

from app.db import SessionLocal
from app.models import Item, AISummary, Insight
from sqlalchemy import func, case

# Check if AI is enabled
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
AI_ENABLED = bool(ANTHROPIC_API_KEY)

if AI_ENABLED:
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    MODEL = "claude-sonnet-4-20250514"


def extract_json_from_text(text: str):
    """
    Extract JSON from text that might be wrapped in markdown code fences.
    Handles cases like:
    - Plain JSON: {...}
    - Markdown: ```json\n{...}\n```
    - Markdown: ```\n{...}\n```
    """
    text = text.strip()

    # Try to parse as-is first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract from markdown code fence
    import re

    # Match ```json ... ``` or ``` ... ```
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # If all else fails, raise the original error
    raise json.JSONDecodeError("Could not extract valid JSON from text", text, 0)


def analyze_vehicle_category():
    """
    Analyze vehicle documents for completeness and upcoming needs.

    Expected docs: insurance, NCT cert, service records, tax disc, registration
    Insights: missing docs, upcoming renewals, service due, unusual costs
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        # Get all vehicle documents
        vehicle_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "vehicle"
            )
            .order_by(Item.created_at.desc())
            .all()
        )

        if len(vehicle_docs) < 2:
            return []  # Not enough data for analysis

        # Prepare document summaries for Claude
        doc_summaries = []
        for item, summary in vehicle_docs:
            doc_summaries.append({
                "filename": item.original_filename,
                "type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "date": summary.extracted_date,
                "amount": summary.extracted_amount,
                "summary": summary.summary_text,
                "uploaded": item.created_at.strftime("%Y-%m-%d")
            })

        prompt = f"""Analyze these vehicle-related documents and provide intelligent insights:

{json.dumps(doc_summaries, indent=2)}

As a vehicle document analyst, evaluate:
1. **Completeness**: Are key documents missing? (insurance, NCT, tax, service records, registration)
2. **Renewals**: Any upcoming expiry dates or renewals needed?
3. **Maintenance**: Is the vehicle being properly maintained? Service intervals appropriate?
4. **Costs**: Any unusual costs or patterns worth noting?
5. **Compliance**: All legal requirements met? (insurance, tax, NCT)

For each significant finding, provide:
{{
    "title": "Clear, actionable title",
    "description": "Detailed explanation of the issue/observation",
    "recommendation": "Specific action to take",
    "priority": "high|medium|low",
    "urgency_days": "how many days until action needed (if applicable)"
}}

Only report significant findings. If everything looks good, return [].
Respond with a JSON array of insights.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                # Check if similar insight exists
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == finding["title"]
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "medium"), "medium")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"🚗 Vehicle: {finding['title']}",
                    description=finding["description"],
                    action=finding["recommendation"],
                    related_items=json.dumps([item.id for item, _ in vehicle_docs[:10]]),
                    insight_metadata=json.dumps({
                        "category": "vehicle",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(vehicle_docs),
                        "urgency_days": finding.get("urgency_days")
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing vehicle category: {e}")
            return []

        return insights

    finally:
        db.close()


def analyze_medical_category():
    """
    Analyze medical documents for patterns and gaps.

    Expected: hospital records, prescriptions, test results, insurance claims
    Insights: missing follow-ups, prescription refills, recurring appointments
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        medical_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "medical"
            )
            .order_by(Item.created_at.desc())
            .limit(30)
            .all()
        )

        if len(medical_docs) < 2:
            return []

        doc_summaries = []
        for item, summary in medical_docs:
            doc_summaries.append({
                "filename": item.original_filename,
                "type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "date": summary.extracted_date,
                "amount": summary.extracted_amount,
                "summary": summary.summary_text
            })

        prompt = f"""Analyze these medical documents:

{json.dumps(doc_summaries, indent=2)}

Identify:
1. Recurring conditions or treatments
2. Missing follow-ups or appointments
3. Prescription patterns (refills needed?)
4. Unusual costs or billing issues
5. Care coordination gaps

Provide insights as JSON array with: title, description, recommendation, priority.
Only significant findings. Return [] if nothing notable.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == f"🏥 Medical: {finding['title']}"
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "medium"), "medium")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"🏥 Medical: {finding['title']}",
                    description=finding["description"],
                    action=finding.get("recommendation", "Review medical records"),
                    related_items=json.dumps([item.id for item, _ in medical_docs[:10]]),
                    insight_metadata=json.dumps({
                        "category": "medical",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(medical_docs)
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing medical category: {e}")
            return []

        return insights

    finally:
        db.close()


def analyze_utilities_category():
    """
    Analyze utility bills for patterns and optimization.

    Expected: electricity, gas, water, broadband, phone bills
    Insights: cost trends, usage patterns, tariff optimization, contract renewals
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        utility_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "utilities"
            )
            .order_by(Item.created_at.desc())
            .all()
        )

        if len(utility_docs) < 3:
            return []

        doc_summaries = []
        for item, summary in utility_docs:
            doc_summaries.append({
                "vendor": summary.extracted_vendor,
                "type": summary.document_type,
                "date": summary.extracted_date,
                "amount": summary.extracted_amount,
                "summary": summary.summary_text
            })

        prompt = f"""Analyze these utility bills:

{json.dumps(doc_summaries, indent=2)}

Evaluate:
1. Cost trends (increasing, seasonal patterns)
2. Usage anomalies
3. Contract renewal opportunities
4. Tariff optimization potential
5. Duplicate or overlapping services

Provide insights as JSON array with: title, description, recommendation, priority, potential_savings.
Only significant findings. Return [] if nothing notable.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == f"⚡ Utilities: {finding['title']}"
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "medium"), "medium")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"⚡ Utilities: {finding['title']}",
                    description=finding["description"],
                    action=finding.get("recommendation", "Review utility bills"),
                    related_items=json.dumps([item.id for item, _ in utility_docs[:10]]),
                    insight_metadata=json.dumps({
                        "category": "utilities",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(utility_docs),
                        "potential_savings": finding.get("potential_savings")
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing utilities category: {e}")
            return []

        return insights

    finally:
        db.close()


def analyze_tax_category():
    """
    Analyze tax documents for compliance and preparation.

    Expected: P60, tax certs, returns, revenue correspondence
    Insights: missing documents, filing deadlines, tax efficiency
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        tax_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "tax"
            )
            .order_by(Item.created_at.desc())
            .all()
        )

        if len(tax_docs) < 1:
            return []

        doc_summaries = []
        for item, summary in tax_docs:
            doc_summaries.append({
                "filename": item.original_filename,
                "type": summary.document_type,
                "date": summary.extracted_date,
                "summary": summary.summary_text,
                "uploaded": item.created_at.strftime("%Y-%m-%d")
            })

        prompt = f"""Analyze these tax documents:

{json.dumps(doc_summaries, indent=2)}

Assess:
1. Tax compliance status (missing forms, certs, returns)
2. Upcoming deadlines
3. Document organization for tax prep
4. Any red flags or issues
5. Tax efficiency opportunities

Provide insights as JSON array with: title, description, recommendation, priority, deadline.
Only significant findings. Return [] if nothing notable.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == f"📋 Tax: {finding['title']}"
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "high"), "high")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"📋 Tax: {finding['title']}",
                    description=finding["description"],
                    action=finding.get("recommendation", "Review tax documents"),
                    related_items=json.dumps([item.id for item, _ in tax_docs]),
                    insight_metadata=json.dumps({
                        "category": "tax",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(tax_docs),
                        "deadline": finding.get("deadline")
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=90)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing tax category: {e}")
            return []

        return insights

    finally:
        db.close()


def analyze_financial_category():
    """
    Analyze financial documents for money management and optimization.

    Expected: bank statements, loan docs, credit cards, savings, pensions
    Insights: unusual transactions, subscription waste, savings opportunities, loan optimization
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        financial_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "financial"
            )
            .order_by(Item.created_at.desc())
            .limit(50)
            .all()
        )

        if len(financial_docs) < 2:
            return []

        doc_summaries = []
        for item, summary in financial_docs:
            doc_summaries.append({
                "filename": item.original_filename,
                "type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "date": summary.extracted_date,
                "amount": summary.extracted_amount,
                "summary": summary.summary_text
            })

        prompt = f"""Analyze these financial documents:

{json.dumps(doc_summaries, indent=2)}

Evaluate:
1. Recurring subscriptions or payments (any waste?)
2. Unusual transactions or amounts
3. Savings opportunities or optimization potential
4. Loan/credit card payment patterns
5. Account management issues

Provide insights as JSON array with: title, description, recommendation, priority, potential_savings.
Only significant findings. Return [] if nothing notable.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == f"💰 Financial: {finding['title']}"
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "medium"), "medium")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"💰 Financial: {finding['title']}",
                    description=finding["description"],
                    action=finding.get("recommendation", "Review financial documents"),
                    related_items=json.dumps([item.id for item, _ in financial_docs[:10]]),
                    insight_metadata=json.dumps({
                        "category": "financial",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(financial_docs),
                        "potential_savings": finding.get("potential_savings")
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing financial category: {e}")
            return []

        return insights

    finally:
        db.close()


def analyze_insurance_category():
    """
    Analyze insurance documents for coverage and renewals.

    Expected: various insurance policies (not car/home - those are separate)
    Insights: renewal dates, coverage gaps, premium changes, policy optimization
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        insurance_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "insurance"
            )
            .order_by(Item.created_at.desc())
            .all()
        )

        if len(insurance_docs) < 1:
            return []

        doc_summaries = []
        for item, summary in insurance_docs:
            doc_summaries.append({
                "filename": item.original_filename,
                "type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "date": summary.extracted_date,
                "amount": summary.extracted_amount,
                "summary": summary.summary_text
            })

        prompt = f"""Analyze these insurance documents:

{json.dumps(doc_summaries, indent=2)}

Assess:
1. Upcoming renewal dates
2. Coverage gaps or overlaps
3. Premium changes or trends
4. Policy optimization opportunities
5. Missing insurance types

Provide insights as JSON array with: title, description, recommendation, priority, renewal_date.
Only significant findings. Return [] if nothing notable.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == f"🛡️ Insurance: {finding['title']}"
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "medium"), "medium")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"🛡️ Insurance: {finding['title']}",
                    description=finding["description"],
                    action=finding.get("recommendation", "Review insurance policies"),
                    related_items=json.dumps([item.id for item, _ in insurance_docs]),
                    insight_metadata=json.dumps({
                        "category": "insurance",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(insurance_docs),
                        "renewal_date": finding.get("renewal_date")
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing insurance category: {e}")
            return []

        return insights

    finally:
        db.close()


def analyze_employment_category():
    """
    Analyze employment documents for payroll consistency and benefits.

    Expected: payslips, contracts, P60, employment letters
    Insights: payslip consistency, tax deductions, contract changes, benefits tracking
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        employment_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "employment"
            )
            .order_by(Item.created_at.desc())
            .limit(30)
            .all()
        )

        if len(employment_docs) < 2:
            return []

        doc_summaries = []
        for item, summary in employment_docs:
            doc_summaries.append({
                "filename": item.original_filename,
                "type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "date": summary.extracted_date,
                "amount": summary.extracted_amount,
                "summary": summary.summary_text
            })

        prompt = f"""Analyze these employment documents:

{json.dumps(doc_summaries, indent=2)}

Review:
1. Payslip consistency (amounts, deductions, patterns)
2. Tax deduction correctness
3. Contract terms and changes
4. Benefits tracking and utilization
5. Missing employment documents (P60, contracts, etc.)

Provide insights as JSON array with: title, description, recommendation, priority.
Only significant findings. Return [] if nothing notable.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == f"💼 Employment: {finding['title']}"
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "medium"), "medium")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"💼 Employment: {finding['title']}",
                    description=finding["description"],
                    action=finding.get("recommendation", "Review employment documents"),
                    related_items=json.dumps([item.id for item, _ in employment_docs]),
                    insight_metadata=json.dumps({
                        "category": "employment",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(employment_docs)
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing employment category: {e}")
            return []

        return insights

    finally:
        db.close()


def analyze_home_category():
    """
    Analyze home/property documents for maintenance and compliance.

    Expected: mortgage, rent, property tax, maintenance, solicitor docs
    Insights: property tax deadlines, maintenance schedules, mortgage milestones, compliance
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        home_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "home"
            )
            .order_by(Item.created_at.desc())
            .all()
        )

        if len(home_docs) < 1:
            return []

        doc_summaries = []
        for item, summary in home_docs:
            doc_summaries.append({
                "filename": item.original_filename,
                "type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "date": summary.extracted_date,
                "amount": summary.extracted_amount,
                "summary": summary.summary_text
            })

        prompt = f"""Analyze these home/property documents:

{json.dumps(doc_summaries, indent=2)}

Evaluate:
1. Property tax deadlines and payment status
2. Maintenance schedules and recurring work
3. Mortgage payment patterns or milestones
4. Rental agreement terms and renewals
5. Property compliance (certificates, inspections)

Provide insights as JSON array with: title, description, recommendation, priority, deadline.
Only significant findings. Return [] if nothing notable.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == f"🏠 Home: {finding['title']}"
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "medium"), "medium")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"🏠 Home: {finding['title']}",
                    description=finding["description"],
                    action=finding.get("recommendation", "Review property documents"),
                    related_items=json.dumps([item.id for item, _ in home_docs]),
                    insight_metadata=json.dumps({
                        "category": "home",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(home_docs),
                        "deadline": finding.get("deadline")
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing home category: {e}")
            return []

        return insights

    finally:
        db.close()


def analyze_legal_category():
    """
    Analyze legal documents for compliance and expiries.

    Expected: contracts, legal letters, court documents
    Insights: contract expiries, compliance requirements, legal deadlines, missing documents
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        legal_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "legal"
            )
            .order_by(Item.created_at.desc())
            .all()
        )

        if len(legal_docs) < 1:
            return []

        doc_summaries = []
        for item, summary in legal_docs:
            doc_summaries.append({
                "filename": item.original_filename,
                "type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "date": summary.extracted_date,
                "summary": summary.summary_text
            })

        prompt = f"""Analyze these legal documents:

{json.dumps(doc_summaries, indent=2)}

Assess:
1. Contract expiry dates and renewals
2. Legal compliance requirements
3. Upcoming deadlines or actions
4. Missing legal documents
5. Document completeness for legal matters

Provide insights as JSON array with: title, description, recommendation, priority, deadline.
Only significant findings. Return [] if nothing notable.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == f"⚖️ Legal: {finding['title']}"
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "high"), "high")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"⚖️ Legal: {finding['title']}",
                    description=finding["description"],
                    action=finding.get("recommendation", "Review legal documents"),
                    related_items=json.dumps([item.id for item, _ in legal_docs]),
                    insight_metadata=json.dumps({
                        "category": "legal",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(legal_docs),
                        "deadline": finding.get("deadline")
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=90)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing legal category: {e}")
            return []

        return insights

    finally:
        db.close()


def analyze_education_category():
    """
    Analyze education documents for deadlines and requirements.

    Expected: school fees, college docs, course materials, certificates
    Insights: fee deadlines, application windows, certification renewals, course completion
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        education_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "education"
            )
            .order_by(Item.created_at.desc())
            .all()
        )

        if len(education_docs) < 1:
            return []

        doc_summaries = []
        for item, summary in education_docs:
            doc_summaries.append({
                "filename": item.original_filename,
                "type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "date": summary.extracted_date,
                "amount": summary.extracted_amount,
                "summary": summary.summary_text
            })

        prompt = f"""Analyze these education documents:

{json.dumps(doc_summaries, indent=2)}

Review:
1. Fee payment deadlines
2. Application or enrollment windows
3. Certification expirations or renewals
4. Course completion requirements
5. Document organization for education records

Provide insights as JSON array with: title, description, recommendation, priority, deadline.
Only significant findings. Return [] if nothing notable.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == f"🎓 Education: {finding['title']}"
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "medium"), "medium")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"🎓 Education: {finding['title']}",
                    description=finding["description"],
                    action=finding.get("recommendation", "Review education documents"),
                    related_items=json.dumps([item.id for item, _ in education_docs]),
                    insight_metadata=json.dumps({
                        "category": "education",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(education_docs),
                        "deadline": finding.get("deadline")
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing education category: {e}")
            return []

        return insights

    finally:
        db.close()


def analyze_travel_category():
    """
    Analyze travel documents for bookings and compliance.

    Expected: flight/hotel bookings, tickets, visas, travel insurance
    Insights: upcoming trips, visa expiries, insurance coverage, booking patterns
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        travel_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "travel"
            )
            .order_by(Item.created_at.desc())
            .all()
        )

        if len(travel_docs) < 1:
            return []

        doc_summaries = []
        for item, summary in travel_docs:
            doc_summaries.append({
                "filename": item.original_filename,
                "type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "date": summary.extracted_date,
                "amount": summary.extracted_amount,
                "summary": summary.summary_text
            })

        prompt = f"""Analyze these travel documents:

{json.dumps(doc_summaries, indent=2)}

Evaluate:
1. Upcoming travel dates and bookings
2. Visa expiration dates
3. Travel insurance coverage gaps
4. Booking patterns and optimization
5. Missing travel documents (confirmations, insurance, visas)

Provide insights as JSON array with: title, description, recommendation, priority, travel_date.
Only significant findings. Return [] if nothing notable.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == f"✈️ Travel: {finding['title']}"
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "medium"), "medium")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"✈️ Travel: {finding['title']}",
                    description=finding["description"],
                    action=finding.get("recommendation", "Review travel documents"),
                    related_items=json.dumps([item.id for item, _ in travel_docs]),
                    insight_metadata=json.dumps({
                        "category": "travel",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(travel_docs),
                        "travel_date": finding.get("travel_date")
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing travel category: {e}")
            return []

        return insights

    finally:
        db.close()


def analyze_shopping_category():
    """
    Analyze shopping documents for warranties and returns.

    Expected: receipts, order confirmations, warranties
    Insights: warranty tracking, return windows, spending patterns, subscription waste
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        shopping_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "shopping"
            )
            .order_by(Item.created_at.desc())
            .limit(50)
            .all()
        )

        if len(shopping_docs) < 3:
            return []

        doc_summaries = []
        for item, summary in shopping_docs:
            doc_summaries.append({
                "filename": item.original_filename,
                "type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "date": summary.extracted_date,
                "amount": summary.extracted_amount,
                "summary": summary.summary_text
            })

        prompt = f"""Analyze these shopping documents:

{json.dumps(doc_summaries, indent=2)}

Identify:
1. Active warranties and expiration dates
2. Open return windows (items recently purchased)
3. Spending patterns or trends
4. Recurring purchases (subscriptions or regular buys)
5. High-value purchases needing warranty tracking

Provide insights as JSON array with: title, description, recommendation, priority, expiry_date.
Only significant findings. Return [] if nothing notable.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == f"🛒 Shopping: {finding['title']}"
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "low"), "low")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"🛒 Shopping: {finding['title']}",
                    description=finding["description"],
                    action=finding.get("recommendation", "Review shopping documents"),
                    related_items=json.dumps([item.id for item, _ in shopping_docs[:10]]),
                    insight_metadata=json.dumps({
                        "category": "shopping",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(shopping_docs),
                        "expiry_date": finding.get("expiry_date")
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing shopping category: {e}")
            return []

        return insights

    finally:
        db.close()


def analyze_government_category():
    """
    Analyze government documents for compliance and renewals.

    Expected: licenses, permits, official forms, government correspondence
    Insights: license renewals, permit expiries, compliance deadlines, missing documents
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        government_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "government"
            )
            .order_by(Item.created_at.desc())
            .all()
        )

        if len(government_docs) < 1:
            return []

        doc_summaries = []
        for item, summary in government_docs:
            doc_summaries.append({
                "filename": item.original_filename,
                "type": summary.document_type,
                "vendor": summary.extracted_vendor,
                "date": summary.extracted_date,
                "summary": summary.summary_text
            })

        prompt = f"""Analyze these government documents:

{json.dumps(doc_summaries, indent=2)}

Review:
1. License and permit renewal dates
2. Government compliance requirements
3. Application deadlines
4. Missing required documents
5. Response deadlines for official correspondence

Provide insights as JSON array with: title, description, recommendation, priority, deadline.
Only significant findings. Return [] if nothing notable.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == f"🏛️ Government: {finding['title']}"
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "high"), "high")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"🏛️ Government: {finding['title']}",
                    description=finding["description"],
                    action=finding.get("recommendation", "Review government documents"),
                    related_items=json.dumps([item.id for item, _ in government_docs]),
                    insight_metadata=json.dumps({
                        "category": "government",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(government_docs),
                        "deadline": finding.get("deadline")
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing government category: {e}")
            return []

        return insights

    finally:
        db.close()


def analyze_personal_category():
    """
    Analyze personal documents for organization and completeness.

    Expected: personal letters, certificates, personal records
    Insights: document organization, important dates, missing documents
    """
    if not AI_ENABLED:
        return []

    db = SessionLocal()
    insights = []

    try:
        personal_docs = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == "personal"
            )
            .order_by(Item.created_at.desc())
            .all()
        )

        if len(personal_docs) < 2:
            return []

        doc_summaries = []
        for item, summary in personal_docs:
            doc_summaries.append({
                "filename": item.original_filename,
                "type": summary.document_type,
                "date": summary.extracted_date,
                "summary": summary.summary_text
            })

        prompt = f"""Analyze these personal documents:

{json.dumps(doc_summaries, indent=2)}

Assess:
1. Document organization and completeness
2. Important dates or anniversaries
3. Personal records that need attention
4. Document preservation needs
5. General personal admin suggestions

Provide insights as JSON array with: title, description, recommendation, priority.
Only significant findings. Return [] if nothing notable.
"""

        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = extract_json_from_text(message.content[0].text)

            for finding in analysis:
                existing = db.query(Insight).filter(
                    Insight.insight_type == "category_intelligence",
                    Insight.status == "active",
                    Insight.title == f"📝 Personal: {finding['title']}"
                ).first()

                if existing:
                    continue

                priority_map = {"high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(finding.get("priority", "low"), "low")

                insight = Insight(
                    insight_type="category_intelligence",
                    priority=priority,
                    title=f"📝 Personal: {finding['title']}",
                    description=finding["description"],
                    action=finding.get("recommendation", "Review personal documents"),
                    related_items=json.dumps([item.id for item, _ in personal_docs]),
                    insight_metadata=json.dumps({
                        "category": "personal",
                        "analysis_date": datetime.now(timezone.utc).isoformat(),
                        "document_count": len(personal_docs)
                    }),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=60)
                )
                insights.append(insight)

        except Exception as e:
            print(f"Error analyzing personal category: {e}")
            return []

        return insights

    finally:
        db.close()


def generate_category_overview():
    """
    Generate comprehensive category overview for dashboard.

    Returns detailed stats for each category including:
    - Document count and percentage
    - Active insights count and priorities
    - Status (good/warning/urgent based on insights)
    - Potential savings (aggregated from insights)
    - Upcoming deadlines
    """
    db = SessionLocal()

    try:
        from sqlalchemy import func

        # All categories with metadata
        CATEGORY_INFO = {
            "vehicle": {"name": "Vehicle", "icon": "🚗", "description": "Car insurance, NCT, service, tax"},
            "medical": {"name": "Medical", "icon": "🏥", "description": "Health records, prescriptions, appointments"},
            "utilities": {"name": "Utilities", "icon": "⚡", "description": "Electricity, gas, water, broadband"},
            "tax": {"name": "Tax", "icon": "📋", "description": "Tax returns, certs, revenue letters"},
            "financial": {"name": "Financial", "icon": "💰", "description": "Bank statements, loans, investments"},
            "insurance": {"name": "Insurance", "icon": "🛡️", "description": "General insurance policies"},
            "employment": {"name": "Employment", "icon": "💼", "description": "Payslips, contracts, P60"},
            "home": {"name": "Home", "icon": "🏠", "description": "Mortgage, property tax, maintenance"},
            "legal": {"name": "Legal", "icon": "⚖️", "description": "Contracts, legal letters, court docs"},
            "education": {"name": "Education", "icon": "🎓", "description": "Fees, courses, certificates"},
            "travel": {"name": "Travel", "icon": "✈️", "description": "Bookings, tickets, visas"},
            "shopping": {"name": "Shopping", "icon": "🛒", "description": "Receipts, orders, warranties"},
            "government": {"name": "Government", "icon": "🏛️", "description": "Licenses, permits, forms"},
            "personal": {"name": "Personal", "icon": "📝", "description": "Personal letters, records"},
            "other": {"name": "Other", "icon": "📄", "description": "Uncategorized documents"}
        }

        # Get document counts per category
        category_doc_counts = (
            db.query(AISummary.category, func.count(Item.id))
            .join(Item, AISummary.item_id == Item.id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category.isnot(None)
            )
            .group_by(AISummary.category)
            .all()
        )

        # Get insights per category
        category_insights = (
            db.query(
                func.json_extract(Insight.insight_metadata, '$.category').label('category'),
                func.count(Insight.id).label('insight_count'),
                func.sum(case((Insight.priority == 'high', 1), else_=0)).label('high_priority'),
                func.sum(case((Insight.priority == 'medium', 1), else_=0)).label('medium_priority'),
                func.sum(case((Insight.priority == 'low', 1), else_=0)).label('low_priority')
            )
            .filter(
                Insight.insight_type == 'category_intelligence',
                Insight.status == 'active'
            )
            .group_by('category')
            .all()
        )

        # Total documents
        total = db.query(func.count(Item.id)).filter(Item.deleted_at.is_(None)).scalar() or 0
        categorized = sum(count for _, count in category_doc_counts)
        uncategorized = total - categorized

        # Build category details
        categories = {}
        for category, info in CATEGORY_INFO.items():
            if category == "other":
                continue  # Skip "other" in main overview

            # Document count
            doc_count = next((count for cat, count in category_doc_counts if cat == category), 0)
            percentage = round((doc_count / total) * 100, 1) if total > 0 else 0

            # Insight stats
            insight_data = next((ins for ins in category_insights if ins[0] == category), None)
            insight_count = insight_data[1] if insight_data else 0
            high_priority = insight_data[2] if insight_data else 0
            medium_priority = insight_data[3] if insight_data else 0
            low_priority = insight_data[4] if insight_data else 0

            # Calculate status
            if high_priority > 0:
                status = "urgent"
                status_label = "⚠️ Action Needed"
            elif medium_priority > 0:
                status = "warning"
                status_label = "⚡ Review Soon"
            elif doc_count == 0:
                status = "empty"
                status_label = "📭 No Documents"
            elif insight_count > 0:
                status = "info"
                status_label = "ℹ️ Has Insights"
            else:
                status = "good"
                status_label = "✓ Looking Good"

            categories[category] = {
                "name": info["name"],
                "icon": info["icon"],
                "description": info["description"],
                "doc_count": doc_count,
                "percentage": percentage,
                "insight_count": insight_count,
                "high_priority": high_priority,
                "medium_priority": medium_priority,
                "low_priority": low_priority,
                "status": status,
                "status_label": status_label
            }

        # Overall statistics
        total_insights = sum(cat["insight_count"] for cat in categories.values())
        total_high_priority = sum(cat["high_priority"] for cat in categories.values())
        total_medium_priority = sum(cat["medium_priority"] for cat in categories.values())

        categories_with_docs = sum(1 for cat in categories.values() if cat["doc_count"] > 0)
        categories_needing_attention = sum(1 for cat in categories.values() if cat["status"] in ["urgent", "warning"])

        overview = {
            "total_documents": total,
            "categorized": categorized,
            "uncategorized": uncategorized,
            "categories_with_docs": categories_with_docs,
            "total_categories": len(categories),
            "total_insights": total_insights,
            "total_high_priority": total_high_priority,
            "total_medium_priority": total_medium_priority,
            "categories_needing_attention": categories_needing_attention,
            "categories": categories
        }

        return overview

    finally:
        db.close()


def generate_all_category_intelligence():
    """
    Generate intelligent insights for all categories.
    Call this periodically or on-demand.
    """
    if not AI_ENABLED:
        print("AI features disabled")
        return 0

    print("Generating category intelligence...")
    print("Analyzing all 14 document categories...\n")

    db = SessionLocal()
    all_insights = []

    # Analyze each category
    all_insights.extend(analyze_vehicle_category())
    print(f"  ✓ Vehicle documents analyzed")

    all_insights.extend(analyze_medical_category())
    print(f"  ✓ Medical documents analyzed")

    all_insights.extend(analyze_utilities_category())
    print(f"  ✓ Utilities documents analyzed")

    all_insights.extend(analyze_tax_category())
    print(f"  ✓ Tax documents analyzed")

    all_insights.extend(analyze_financial_category())
    print(f"  ✓ Financial documents analyzed")

    all_insights.extend(analyze_insurance_category())
    print(f"  ✓ Insurance documents analyzed")

    all_insights.extend(analyze_employment_category())
    print(f"  ✓ Employment documents analyzed")

    all_insights.extend(analyze_home_category())
    print(f"  ✓ Home/property documents analyzed")

    all_insights.extend(analyze_legal_category())
    print(f"  ✓ Legal documents analyzed")

    all_insights.extend(analyze_education_category())
    print(f"  ✓ Education documents analyzed")

    all_insights.extend(analyze_travel_category())
    print(f"  ✓ Travel documents analyzed")

    all_insights.extend(analyze_shopping_category())
    print(f"  ✓ Shopping documents analyzed")

    all_insights.extend(analyze_government_category())
    print(f"  ✓ Government documents analyzed")

    all_insights.extend(analyze_personal_category())
    print(f"  ✓ Personal documents analyzed")

    # Save all insights
    try:
        for insight in all_insights:
            db.add(insight)
        db.commit()

        print(f"\n✅ Complete! Generated {len(all_insights)} category intelligence insights")
        return len(all_insights)
    finally:
        db.close()
