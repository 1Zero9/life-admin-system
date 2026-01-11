"""
Vehicle Intelligence Agent

Analyzes vehicle-related documents to provide insights on:
- Document completeness (insurance, NCT, tax, service records)
- Upcoming renewals and expiry dates
- Maintenance patterns and service intervals
- Cost analysis and unusual expenses
- Legal compliance (insurance, tax, NCT)

Personal Value: Never miss NCT renewal, track maintenance, optimize costs
Business Value: Could be sold as fleet management add-on or insurance tool
"""

import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any

from app.agents import IntelligenceAgent, Document, Insight

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


class VehicleAgent(IntelligenceAgent):
    """
    Vehicle Intelligence Agent

    Analyzes vehicle documents for completeness, renewals, maintenance, and compliance.
    """

    # Metadata
    name = "Vehicle Intelligence"
    version = "1.0.0"
    category = "vehicle"
    description = "Track insurance, NCT, tax, service records. Get renewal reminders and maintenance insights."
    author = "core"

    # Configuration
    min_documents = 2  # Need at least 2 docs for pattern analysis
    max_documents = 100
    license_type = "personal"  # Future: Could be "premium" for advanced features

    def analyze(self, documents: List[Document]) -> List[Insight]:
        """
        Analyze vehicle documents and generate intelligence.

        Entity-aware: Groups documents by vehicle and analyzes each separately.

        Args:
            documents: List of vehicle-related documents

        Returns:
            List of actionable insights
        """
        if not AI_ENABLED:
            return []

        if len(documents) < self.min_documents:
            return []

        # Group documents by entity (each vehicle separately)
        by_entity = {}
        for doc in documents:
            entity_id = getattr(doc, 'entity_id', None) or 'unknown'
            entity_name = getattr(doc, 'entity_name', None)
            by_entity.setdefault(entity_id, {'name': entity_name, 'docs': []})['docs'].append(doc)

        all_insights = []

        # Analyze each vehicle separately
        for entity_id, entity_data in by_entity.items():
            vehicle_docs = entity_data['docs']
            vehicle_name = entity_data['name'] or 'Unknown Vehicle'

            # Need at least min_documents for this specific vehicle
            if len(vehicle_docs) < self.min_documents:
                continue

            # Prepare document summaries for this vehicle
            doc_summaries = []
            for doc in vehicle_docs:
                doc_summaries.append({
                    "filename": doc.filename,
                    "vendor": doc.vendor,
                    "date": doc.date,
                    "amount": doc.amount,
                    "summary": doc.summary,
                })

            # Analyze this specific vehicle
            prompt = f"""Analyze these vehicle-related documents for {vehicle_name} and provide intelligent insights:

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
    "urgency_days": "how many days until action needed (if applicable)",
    "estimated_value": "potential savings or cost if applicable (e.g., '€50 savings')"
}}

Only report significant findings. If everything looks good, return [].
Respond with a JSON array of insights."""

            try:
                message = client.messages.create(
                    model=MODEL,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )

                analysis = extract_json_from_text(message.content[0].text)

                for finding in analysis:
                    priority_map = {"high": "high", "medium": "medium", "low": "low"}
                    priority = priority_map.get(finding.get("priority", "medium"), "medium")

                    # Tag insight with vehicle entity
                    insight = Insight(
                        title=f"[{vehicle_name}] {finding['title']}",
                        description=finding["description"],
                        recommendation=finding["recommendation"],
                        priority=priority,
                        category=self.category,
                        metadata={
                            "analysis_date": datetime.now(timezone.utc).isoformat(),
                            "document_count": len(vehicle_docs),
                            "urgency_days": finding.get("urgency_days"),
                            "agent": self.name,
                            "agent_version": self.version,
                            "entity_id": entity_id if entity_id != 'unknown' else None,
                            "entity_name": vehicle_name,
                        },
                        confidence=0.9,  # High confidence for Claude Sonnet 4
                        estimated_value=finding.get("estimated_value"),
                    )
                    all_insights.append(insight)

            except Exception as e:
                print(f"Error analyzing {vehicle_name}: {e}")
                continue

        return all_insights

    def can_analyze(self, documents: List[Document]) -> bool:
        """Check if we have enough documents to analyze."""
        return AI_ENABLED and len(documents) >= self.min_documents

    def estimate_cost(self, documents: List[Document]) -> float:
        """
        Estimate AI operation cost for analysis.

        Claude Sonnet 4 pricing (approx):
        - Input: ~$3 per million tokens
        - Output: ~$15 per million tokens

        Typical run:
        - Input: ~1000 tokens (doc summaries + prompt)
        - Output: ~500 tokens (insights)
        - Cost: (1000 * 0.000003) + (500 * 0.000015) = $0.0105
        """
        if not AI_ENABLED or len(documents) < self.min_documents:
            return 0.0

        # Estimate tokens based on document count
        estimated_input_tokens = 500 + (len(documents) * 100)  # Base + per doc
        estimated_output_tokens = 500  # Typical insights response

        # Claude Sonnet 4 pricing (per million tokens)
        input_cost_per_million = 3.0
        output_cost_per_million = 15.0

        input_cost = (estimated_input_tokens / 1_000_000) * input_cost_per_million
        output_cost = (estimated_output_tokens / 1_000_000) * output_cost_per_million

        return input_cost + output_cost
