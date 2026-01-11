"""
Natural Language Search - Uses Claude to understand user queries and find relevant documents.

Examples:
- "Show me everything related to my car"
- "Find my car insurance documents"
- "What electricity bills do I have from 2025?"
- "Show me medical documents from The Plaza Clinic"
"""

import os
import json
from typing import List, Dict, Any, Optional
from sqlalchemy import or_, and_, func

from app.db import SessionLocal
from app.models import Item, AISummary

# Check if AI is enabled
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
AI_ENABLED = bool(ANTHROPIC_API_KEY)

if AI_ENABLED:
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    MODEL = "claude-sonnet-4-20250514"


def extract_json_from_text(text: str):
    """Extract JSON from text that might be wrapped in markdown code fences."""
    text = text.strip()

    # Try to parse as-is first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract from markdown code fence
    import re
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # If all else fails, raise the original error
    raise json.JSONDecodeError("Could not extract valid JSON from text", text, 0)


def natural_language_search(query: str, limit: int = 50) -> Dict[str, Any]:
    """
    Search documents using natural language query.

    Args:
        query: Natural language search query (e.g., "show me car insurance documents")
        limit: Maximum number of results to return

    Returns:
        Dictionary with search results, explanation, and metadata
    """
    if not AI_ENABLED:
        return {
            "ok": False,
            "error": "AI features not enabled. Set ANTHROPIC_API_KEY in .env"
        }

    db = SessionLocal()

    try:
        # Step 1: Ask Claude to analyze the query and determine search strategy
        analysis_prompt = f"""Analyze this natural language search query and determine the best search strategy.

User query: "{query}"

Based on the query, provide a search strategy including:
1. **keywords**: Important keywords to search for in document text (list of strings)
2. **categories**: Relevant document categories to filter by (list from: vehicle, medical, home, utilities, financial, insurance, employment, tax, legal, education, travel, shopping, government, personal, other)
3. **document_types**: Specific document types if mentioned (e.g., "bill", "invoice", "receipt", "policy", "certificate")
4. **vendors**: Specific vendor/company names if mentioned
5. **date_range**: If a time period is mentioned (e.g., "2025", "last year", "recent")
6. **explanation**: A brief explanation of what you're searching for (1-2 sentences)

Respond with JSON:
{{
  "keywords": ["keyword1", "keyword2"],
  "categories": ["category1", "category2"],
  "document_types": ["type1", "type2"],
  "vendors": ["vendor1"],
  "date_range": {{"year": 2025, "month": null}},
  "explanation": "Searching for..."
}}

If no specific filter is needed, use null or empty array. Be generous with keywords to catch variations.
"""

        message = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": analysis_prompt}]
        )

        search_strategy = extract_json_from_text(message.content[0].text)

        # Step 2: Build database query based on strategy
        query_obj = db.query(Item, AISummary).outerjoin(AISummary, Item.id == AISummary.item_id).filter(
            Item.deleted_at.is_(None)
        )

        # Apply category filters
        if search_strategy.get("categories"):
            query_obj = query_obj.filter(AISummary.category.in_(search_strategy["categories"]))

        # Apply document type filters
        if search_strategy.get("document_types"):
            type_conditions = [AISummary.document_type.ilike(f"%{dt}%") for dt in search_strategy["document_types"]]
            query_obj = query_obj.filter(or_(*type_conditions))

        # Apply vendor filters
        if search_strategy.get("vendors"):
            vendor_conditions = [AISummary.extracted_vendor.ilike(f"%{v}%") for v in search_strategy["vendors"]]
            query_obj = query_obj.filter(or_(*vendor_conditions))

        # Apply date range filters
        if search_strategy.get("date_range"):
            date_range = search_strategy["date_range"]
            if date_range.get("year"):
                year = date_range["year"]
                if date_range.get("month"):
                    # Specific month
                    month = date_range["month"]
                    query_obj = query_obj.filter(
                        func.strftime('%Y', Item.created_at) == str(year),
                        func.strftime('%m', Item.created_at) == str(month).zfill(2)
                    )
                else:
                    # Entire year
                    query_obj = query_obj.filter(
                        func.strftime('%Y', Item.created_at) == str(year)
                    )

        # Apply keyword filters (search in text, filename, summary)
        if search_strategy.get("keywords"):
            keyword_conditions = []
            for keyword in search_strategy["keywords"]:
                keyword_like = f"%{keyword}%"
                keyword_conditions.append(or_(
                    Item.original_filename.ilike(keyword_like),
                    Item.extracted_text.ilike(keyword_like),
                    AISummary.summary_text.ilike(keyword_like),
                    AISummary.extracted_vendor.ilike(keyword_like)
                ))
            query_obj = query_obj.filter(or_(*keyword_conditions))

        # Execute query
        results = query_obj.order_by(Item.created_at.desc()).limit(limit).all()

        # Format results
        documents = []
        for item, summary in results:
            doc = {
                "id": item.id,
                "filename": item.original_filename,
                "created_at": item.created_at.isoformat(),
                "source_type": item.source_type,
                "content_type": item.content_type,
                "has_text": bool(item.extracted_text),
                "summary": None
            }

            if summary:
                doc["summary"] = {
                    "type": summary.document_type,
                    "category": summary.category,
                    "vendor": summary.extracted_vendor,
                    "amount": summary.extracted_amount,
                    "date": summary.extracted_date,
                    "summary_text": summary.summary_text
                }

            documents.append(doc)

        return {
            "ok": True,
            "query": query,
            "explanation": search_strategy.get("explanation", ""),
            "search_strategy": search_strategy,
            "total_results": len(documents),
            "documents": documents
        }

    except Exception as e:
        print(f"Natural language search error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "ok": False,
            "error": str(e)
        }

    finally:
        db.close()
