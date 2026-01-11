#!/usr/bin/env python3
"""
Test script for agent framework.

Verifies:
- Agent discovery works
- Registry can find agents
- Agent metadata is correct
- Agents can be instantiated
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents import get_registry, get_runner, Document


def test_agent_discovery():
    """Test that agents are discovered correctly."""
    print("=" * 60)
    print("Testing Agent Discovery")
    print("=" * 60)

    registry = get_registry()
    agents = registry.list_agents()

    print(f"\nFound {len(agents)} agent(s):\n")

    for agent_info in agents:
        print(f"📦 {agent_info['id']}")
        print(f"   Name: {agent_info['name']}")
        print(f"   Category: {agent_info['category']}")
        print(f"   Version: {agent_info['version']}")
        print(f"   Description: {agent_info['description']}")
        print(f"   License: {agent_info['license_type']}")
        print(f"   Min Documents: {agent_info['min_documents']}")
        print()

    return len(agents) > 0


def test_vehicle_agent():
    """Test VehicleAgent specifically."""
    print("=" * 60)
    print("Testing Vehicle Agent")
    print("=" * 60)

    registry = get_registry()

    try:
        agent = registry.get_agent("core.vehicle")
        print(f"\n✓ VehicleAgent loaded successfully")
        print(f"  Name: {agent.name}")
        print(f"  Category: {agent.category}")
        print(f"  Version: {agent.version}")
        print()

        # Test can_analyze
        test_docs = [
            Document(
                id="test1",
                filename="insurance.pdf",
                content_type="application/pdf",
                extracted_text="Vehicle insurance policy...",
                summary="Car insurance policy",
                vendor="AA Ireland",
                date="2025-03-15",
                amount="€450.00",
            ),
            Document(
                id="test2",
                filename="nct_cert.pdf",
                content_type="application/pdf",
                extracted_text="NCT certificate...",
                summary="NCT certificate",
                vendor="NCT",
                date="2025-06-01",
                amount=None,
            ),
        ]

        can_analyze = agent.can_analyze(test_docs)
        print(f"  Can analyze 2 test docs: {can_analyze}")

        # Test cost estimation
        estimated_cost = agent.estimate_cost(test_docs)
        print(f"  Estimated cost: ${estimated_cost:.4f}")
        print()

        return True

    except Exception as e:
        print(f"\n✗ Error loading VehicleAgent: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_runner():
    """Test agent runner."""
    print("=" * 60)
    print("Testing Agent Runner")
    print("=" * 60)

    runner = get_runner()
    print(f"\n✓ AgentRunner initialized")
    print(f"  Registry has {len(runner.registry.list_agents())} agent(s)")
    print()

    # Note: We won't actually run the agent here to avoid AI costs
    # Just verify the runner is set up correctly

    return True


if __name__ == "__main__":
    print("\n🧪 Agent Framework Test Suite\n")

    results = []

    # Run tests
    results.append(("Agent Discovery", test_agent_discovery()))
    results.append(("Vehicle Agent", test_vehicle_agent()))
    results.append(("Agent Runner", test_runner()))

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    print()

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
