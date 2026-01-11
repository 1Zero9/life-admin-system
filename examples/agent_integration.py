#!/usr/bin/env python3
"""
Agent Integration Example

Demonstrates how to use the agent framework to analyze documents
from your personal vault.

This shows the migration path from category_intelligence.py to agents.
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents import get_registry, get_runner, Document
from app.db import SessionLocal
from app.models import Item, AISummary


def load_documents_by_category(category: str):
    """
    Load documents from database for a specific category.

    This is how you bridge from the existing database to the agent framework.
    """
    db = SessionLocal()
    try:
        # Get all documents for this category
        items = (
            db.query(Item, AISummary)
            .join(AISummary, Item.id == AISummary.item_id)
            .filter(
                Item.deleted_at.is_(None),
                AISummary.category == category
            )
            .order_by(Item.created_at.desc())
            .all()
        )

        # Convert to agent Document format
        documents = []
        for item, summary in items:
            doc = Document(
                id=item.id,
                filename=item.original_filename,
                content_type=item.content_type,
                extracted_text=item.extracted_text or "",
                summary=summary.summary_text,
                vendor=summary.extracted_vendor,
                date=summary.extracted_date,
                amount=summary.extracted_amount,
            )
            documents.append(doc)

        return documents

    finally:
        db.close()


def run_vehicle_agent_example():
    """
    Example: Run the Vehicle Intelligence Agent on your actual documents.
    """
    print("=" * 60)
    print("Vehicle Agent Integration Example")
    print("=" * 60)
    print()

    # Load your actual vehicle documents
    print("Loading vehicle documents from vault...")
    documents = load_documents_by_category("vehicle")
    print(f"Found {len(documents)} vehicle document(s)")
    print()

    if len(documents) < 2:
        print("⚠️  Need at least 2 vehicle documents for analysis")
        print("   Upload some vehicle docs (insurance, NCT, service records)")
        return

    # Get the agent runner
    runner = get_runner()

    # Run the vehicle agent
    print("Running Vehicle Intelligence Agent...")
    print()

    result = runner.run_agent("core.vehicle", documents)

    # Display results
    print("-" * 60)
    print("Analysis Results")
    print("-" * 60)
    print()
    print(f"✓ Success: {result.success}")
    print(f"  Documents analyzed: {result.document_count}")
    print(f"  Execution time: {result.execution_time:.2f}s")
    print(f"  Estimated cost: ${result.estimated_cost:.4f}")
    print(f"  Insights generated: {len(result.insights)}")
    print()

    if result.insights:
        print("📋 Insights:")
        print()
        for i, insight in enumerate(result.insights, 1):
            print(f"{i}. {insight.title}")
            print(f"   Priority: {insight.priority.upper()}")
            print(f"   {insight.description}")
            print(f"   → {insight.recommendation}")
            if insight.estimated_value:
                print(f"   💰 Value: {insight.estimated_value}")
            print()

    if result.error:
        print(f"❌ Error: {result.error}")


def compare_old_vs_new_approach():
    """
    Show the difference between old category_intelligence.py and new agents.
    """
    print("=" * 60)
    print("Old vs New Approach Comparison")
    print("=" * 60)
    print()

    print("OLD APPROACH (category_intelligence.py):")
    print("  - Monolithic functions")
    print("  - Tightly coupled to database")
    print("  - Hard to test")
    print("  - Hard to extract for business use")
    print("  - No cost transparency")
    print("  - All 14 analyzers in one file")
    print()

    print("NEW APPROACH (agent framework):")
    print("  - Modular classes")
    print("  - Clean interface (Document → Insight)")
    print("  - Easy to test")
    print("  - Each agent is extractable product")
    print("  - Cost estimation built-in")
    print("  - Each agent in separate file")
    print("  - Auto-discovery (just add file)")
    print("  - Can run standalone or integrated")
    print()

    print("MIGRATION PATH:")
    print("  1. Keep category_intelligence.py working (Mode 1 never breaks)")
    print("  2. Create new agent (copy logic, clean interface)")
    print("  3. Test agent independently")
    print("  4. Once working, optionally switch to agent")
    print("  5. Repeat for other 13 categories")
    print()

    print("BUSINESS VALUE:")
    print("  - Each agent = potential product")
    print("  - Vehicle agent → fleet management tool")
    print("  - Medical agent → health tracking tool")
    print("  - Financial agent → expense analyzer")
    print("  - Agents can be sold individually or as suite")
    print()


def show_agent_portfolio():
    """
    Display the agent portfolio.
    """
    print("=" * 60)
    print("Your Agent Portfolio")
    print("=" * 60)
    print()

    registry = get_registry()
    agents = registry.list_agents()

    print(f"Total Agents: {len(agents)}")
    print()

    # Group by license type
    by_license = {}
    for agent in agents:
        license_type = agent['license_type']
        by_license.setdefault(license_type, []).append(agent)

    for license_type, agent_list in by_license.items():
        print(f"{license_type.upper()} ({len(agent_list)}):")
        for agent in agent_list:
            print(f"  ✓ {agent['name']} v{agent['version']}")
            print(f"    {agent['description']}")
        print()

    print("PORTFOLIO GROWTH PLAN:")
    print("  Phase 1: Migrate 14 category analyzers (1-2 months)")
    print("  Phase 2: Build 3-5 specialized agents (3-6 months)")
    print("  Phase 3: Document and polish (ongoing)")
    print("  Phase 4: Assess extraction options (12+ months)")
    print()


if __name__ == "__main__":
    print("\n🚀 Agent Framework Integration Examples\n")

    # Run examples
    compare_old_vs_new_approach()
    show_agent_portfolio()

    # Uncomment to run actual agent (costs ~$0.01):
    # run_vehicle_agent_example()

    print("\n💡 To run the vehicle agent on your actual documents:")
    print("   Uncomment the last line in this file and run again")
    print()
