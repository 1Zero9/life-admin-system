"""
Agent Registry - Discovers and manages intelligence agents

This registry:
1. Discovers all available agents
2. Loads agents on demand
3. Tracks agent metadata
4. Manages agent lifecycle
5. Provides agent catalog for UI/API

Design: Agents are discovered dynamically, making it easy to add new ones.
"""

import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Type
from app.agents.base import IntelligenceAgent


class AgentRegistry:
    """
    Central registry for all intelligence agents.

    Discovers agents from agents_library/ directories and provides
    access to agent metadata and instances.
    """

    def __init__(self):
        self._agents: Dict[str, Type[IntelligenceAgent]] = {}
        self._instances: Dict[str, IntelligenceAgent] = {}
        self._discover_agents()

    def _discover_agents(self):
        """Discover all agent classes in agents_library/"""
        # Get the agents_library directory
        agents_dir = Path(__file__).parent.parent / "agents_library"

        if not agents_dir.exists():
            return

        # Discover in core/ and experimental/
        for subdir in ["core", "experimental"]:
            subdir_path = agents_dir / subdir
            if not subdir_path.exists():
                continue

            # Find all .py files
            for py_file in subdir_path.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue

                # Import the module
                module_name = f"app.agents_library.{subdir}.{py_file.stem}"
                try:
                    module = importlib.import_module(module_name)

                    # Find IntelligenceAgent subclasses
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (
                            issubclass(obj, IntelligenceAgent)
                            and obj is not IntelligenceAgent
                        ):
                            agent_id = f"{subdir}.{py_file.stem}"
                            self._agents[agent_id] = obj

                except Exception as e:
                    print(f"Warning: Failed to load agent from {module_name}: {e}")

    def get_agent(self, agent_id: str, config: Optional[Dict] = None) -> IntelligenceAgent:
        """
        Get an agent instance by ID.

        Args:
            agent_id: Agent identifier (e.g., "core.vehicle")
            config: Optional configuration for agent

        Returns:
            Agent instance

        Raises:
            KeyError: If agent not found
        """
        if agent_id not in self._agents:
            raise KeyError(f"Agent not found: {agent_id}")

        # Create new instance if not cached or config provided
        if agent_id not in self._instances or config is not None:
            agent_class = self._agents[agent_id]
            self._instances[agent_id] = agent_class(config)

        return self._instances[agent_id]

    def list_agents(self) -> List[Dict[str, any]]:
        """
        List all available agents with metadata.

        Returns:
            List of agent metadata dictionaries
        """
        agents = []
        for agent_id, agent_class in self._agents.items():
            # Create temporary instance to get metadata
            instance = agent_class()
            metadata = instance.get_metadata()
            metadata["id"] = agent_id
            agents.append(metadata)

        return agents

    def get_agents_by_category(self, category: str) -> List[str]:
        """
        Get all agent IDs for a category.

        Args:
            category: Category name (e.g., "vehicle", "medical")

        Returns:
            List of agent IDs
        """
        return [
            agent_id
            for agent_id, agent_class in self._agents.items()
            if agent_class().category == category
        ]

    def reload(self):
        """Reload all agents (useful during development)"""
        self._agents.clear()
        self._instances.clear()
        self._discover_agents()


# Global registry instance
_registry = None


def get_registry() -> AgentRegistry:
    """Get the global agent registry"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
