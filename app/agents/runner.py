"""
Agent Runner - Executes intelligence agents and manages workflow

This runner:
1. Executes agents on documents
2. Tracks execution metrics (time, cost)
3. Handles errors gracefully
4. Provides execution reports
5. Manages agent lifecycle

Design: Separates execution from agent logic, making it easy to add
features like retry logic, caching, or distributed execution later.
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.agents.base import IntelligenceAgent, Document, Insight
from app.agents.registry import get_registry


class AgentExecutionResult:
    """Result of agent execution with metrics"""

    def __init__(
        self,
        agent_id: str,
        insights: List[Insight],
        execution_time: float,
        estimated_cost: float,
        document_count: int,
        success: bool = True,
        error: Optional[str] = None,
    ):
        self.agent_id = agent_id
        self.insights = insights
        self.execution_time = execution_time
        self.estimated_cost = estimated_cost
        self.document_count = document_count
        self.success = success
        self.error = error
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage"""
        return {
            "agent_id": self.agent_id,
            "insights_generated": len(self.insights),
            "execution_time_seconds": round(self.execution_time, 2),
            "estimated_cost_usd": round(self.estimated_cost, 4),
            "documents_analyzed": self.document_count,
            "success": self.success,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class AgentRunner:
    """
    Executes intelligence agents and manages execution workflow.

    Handles:
    - Agent loading and validation
    - Document preparation
    - Execution timing and cost tracking
    - Error handling and reporting
    - Execution logging
    """

    def __init__(self):
        self.registry = get_registry()
        self.execution_history: List[AgentExecutionResult] = []

    def run_agent(
        self,
        agent_id: str,
        documents: List[Document],
        config: Optional[Dict[str, Any]] = None,
    ) -> AgentExecutionResult:
        """
        Run a specific agent on documents.

        Args:
            agent_id: Agent identifier (e.g., "core.vehicle")
            documents: Documents to analyze
            config: Optional agent configuration

        Returns:
            Execution result with insights and metrics
        """
        start_time = time.time()

        try:
            # Load agent
            agent = self.registry.get_agent(agent_id, config)

            # Validate documents
            if not agent.can_analyze(documents):
                return AgentExecutionResult(
                    agent_id=agent_id,
                    insights=[],
                    execution_time=time.time() - start_time,
                    estimated_cost=0.0,
                    document_count=len(documents),
                    success=False,
                    error=f"Agent cannot analyze {len(documents)} documents (requires {agent.min_documents}-{agent.max_documents})",
                )

            # Estimate cost
            estimated_cost = agent.estimate_cost(documents)

            # Run analysis
            insights = agent.analyze(documents)

            # Validate insights
            validated_insights = agent.validate_insights(insights)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Create result
            result = AgentExecutionResult(
                agent_id=agent_id,
                insights=validated_insights,
                execution_time=execution_time,
                estimated_cost=estimated_cost,
                document_count=len(documents),
                success=True,
            )

            # Track execution
            self.execution_history.append(result)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            result = AgentExecutionResult(
                agent_id=agent_id,
                insights=[],
                execution_time=execution_time,
                estimated_cost=0.0,
                document_count=len(documents),
                success=False,
                error=str(e),
            )
            self.execution_history.append(result)
            return result

    def run_all_agents(
        self, documents_by_category: Dict[str, List[Document]]
    ) -> List[AgentExecutionResult]:
        """
        Run all applicable agents on categorized documents.

        Args:
            documents_by_category: Dict mapping category -> documents

        Returns:
            List of execution results
        """
        results = []

        for category, documents in documents_by_category.items():
            # Get agents for this category
            agent_ids = self.registry.get_agents_by_category(category)

            for agent_id in agent_ids:
                result = self.run_agent(agent_id, documents)
                results.append(result)

        return results

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get aggregate execution statistics.

        Returns:
            Dictionary with execution metrics
        """
        if not self.execution_history:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_insights": 0,
                "total_cost_usd": 0.0,
                "avg_execution_time": 0.0,
            }

        successful = [r for r in self.execution_history if r.success]
        failed = [r for r in self.execution_history if not r.success]

        return {
            "total_executions": len(self.execution_history),
            "successful_executions": len(successful),
            "failed_executions": len(failed),
            "total_insights": sum(len(r.insights) for r in successful),
            "total_cost_usd": sum(r.estimated_cost for r in successful),
            "avg_execution_time": (
                sum(r.execution_time for r in successful) / len(successful)
                if successful
                else 0.0
            ),
            "last_execution": (
                self.execution_history[-1].timestamp.isoformat()
                if self.execution_history
                else None
            ),
        }

    def clear_history(self):
        """Clear execution history"""
        self.execution_history.clear()


# Global runner instance
_runner = None


def get_runner() -> AgentRunner:
    """Get the global agent runner"""
    global _runner
    if _runner is None:
        _runner = AgentRunner()
    return _runner
