"""
Base Agent Class - Intelligence Agent Framework

Each agent is a self-contained intelligence module that:
1. Analyzes documents in a specific domain
2. Generates actionable insights
3. Learns from user corrections
4. Estimates costs transparently

Design principles:
- Self-contained (minimal dependencies)
- Reusable (can work standalone or in system)
- Testable (clear inputs/outputs)
- Extractable (can become a product if needed)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Document:
    """Document input for analysis"""
    id: str
    filename: str
    content_type: str
    extracted_text: str
    summary: Optional[str] = None
    vendor: Optional[str] = None
    date: Optional[str] = None
    amount: Optional[str] = None
    created_at: Optional[datetime] = None
    # Entity association (who/what this document is about)
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    entity_type: Optional[str] = None


@dataclass
class Insight:
    """Intelligence output from agent"""
    title: str
    description: str
    recommendation: str
    priority: str  # high, medium, low
    category: str
    metadata: Dict[str, Any]
    confidence: float = 1.0  # 0-1 score
    estimated_value: Optional[str] = None  # e.g., "€200 savings"


@dataclass
class Correction:
    """User correction for learning"""
    original_category: str
    corrected_category: str
    document_context: Dict[str, Any]
    timestamp: datetime


class IntelligenceAgent(ABC):
    """
    Base class for all intelligence agents.

    Each agent is an expert in one domain (vehicle, medical, financial, etc.)
    and provides specialized analysis and recommendations.
    """

    # Metadata (override in subclass)
    name: str = "Base Agent"
    version: str = "1.0.0"
    category: str = "general"
    description: str = "Base intelligence agent"
    author: str = "core"

    # Configuration
    min_documents: int = 1  # Minimum docs needed for analysis
    max_documents: int = 100  # Max docs to analyze (performance)

    # Licensing (for future business use)
    license_type: str = "personal"  # personal, free, premium, enterprise
    price_monthly: float = 0.0  # Monthly cost (0 for personal/free)

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize agent with optional configuration"""
        self.config = config or {}
        self._setup()

    def _setup(self):
        """Optional setup hook for subclasses"""
        pass

    @abstractmethod
    def analyze(self, documents: List[Document]) -> List[Insight]:
        """
        Main intelligence generation method.

        Args:
            documents: List of documents to analyze

        Returns:
            List of insights generated from analysis

        Raises:
            ValueError: If documents don't meet requirements
        """
        pass

    def can_analyze(self, documents: List[Document]) -> bool:
        """
        Check if agent can analyze these documents.

        Args:
            documents: Documents to check

        Returns:
            True if agent can analyze, False otherwise
        """
        if len(documents) < self.min_documents:
            return False

        if len(documents) > self.max_documents:
            return False

        return True

    def learn(self, corrections: List[Correction]) -> None:
        """
        Optional: Update agent based on user corrections.

        Default implementation does nothing. Override if agent supports learning.

        Args:
            corrections: User corrections to learn from
        """
        pass

    def estimate_cost(self, documents: List[Document]) -> float:
        """
        Estimate AI operation cost for analysis.

        Default: Assumes Claude Sonnet 4 pricing.
        Override if agent uses different model or has custom pricing.

        Args:
            documents: Documents to analyze

        Returns:
            Estimated cost in USD
        """
        # Rough estimate: $3 per million tokens
        # Average document: ~1000 tokens
        # Analysis prompt: ~500 tokens
        total_tokens = len(documents) * 1500
        cost_per_token = 3.0 / 1_000_000
        return total_tokens * cost_per_token

    def get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata for registry"""
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "description": self.description,
            "author": self.author,
            "min_documents": self.min_documents,
            "max_documents": self.max_documents,
            "license_type": self.license_type,
            "price_monthly": self.price_monthly,
        }

    def validate_insights(self, insights: List[Insight]) -> List[Insight]:
        """
        Validate and filter insights.

        Default implementation removes duplicates and low-confidence insights.
        Override for custom validation logic.

        Args:
            insights: Insights to validate

        Returns:
            Validated insights
        """
        # Remove duplicates (same title)
        seen_titles = set()
        validated = []

        for insight in insights:
            if insight.title not in seen_titles:
                # Only include high-confidence insights
                if insight.confidence >= 0.7:
                    validated.append(insight)
                    seen_titles.add(insight.title)

        return validated

    def __repr__(self) -> str:
        return f"<{self.name} v{self.version} ({self.category})>"
