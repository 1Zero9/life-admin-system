"""
Intelligence Agent Framework

This framework provides a modular system for building domain-specific
intelligence agents that analyze documents and generate actionable insights.

Key components:
- IntelligenceAgent: Base class for all agents
- AgentRegistry: Discovers and manages agents
- AgentRunner: Executes agents and tracks metrics

Usage:
    from app.agents import get_registry, get_runner

    # List available agents
    registry = get_registry()
    agents = registry.list_agents()

    # Run an agent
    runner = get_runner()
    result = runner.run_agent("core.vehicle", documents)
"""

from app.agents.base import IntelligenceAgent, Document, Insight, Correction
from app.agents.registry import AgentRegistry, get_registry
from app.agents.runner import AgentRunner, AgentExecutionResult, get_runner

__all__ = [
    "IntelligenceAgent",
    "Document",
    "Insight",
    "Correction",
    "AgentRegistry",
    "get_registry",
    "AgentRunner",
    "AgentExecutionResult",
    "get_runner",
]
