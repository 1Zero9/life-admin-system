# Intelligence Agent Framework

## Overview

This framework provides a modular, extensible system for building domain-specific AI intelligence agents. Each agent is an expert in one domain (vehicle, medical, financial, etc.) and generates actionable insights from documents.

## Philosophy

**Personal First, Product Second**

This framework is designed for personal use first, with business extraction as a byproduct:

- **Personal**: Each agent solves a real problem you have
- **Portfolio**: Each agent is clean, reusable IP
- **Fallback**: Agents can be extracted as products/services if needed
- **Quality**: Build it right once, use it forever

**Key Principles:**

1. **Self-Contained**: Each agent works standalone
2. **Reusable**: Minimal dependencies, clean interfaces
3. **Testable**: Clear inputs → outputs
4. **Extractable**: Can become a product without rewrite
5. **Valuable**: Captures real expertise and intelligence

## Architecture

```
┌─────────────────────────────────────────────┐
│           Intelligence Agent                │
├─────────────────────────────────────────────┤
│  Metadata:                                  │
│  - name, version, category                  │
│  - description, author                      │
│  - license, pricing                         │
├─────────────────────────────────────────────┤
│  Methods:                                   │
│  - analyze(documents) → insights            │
│  - can_analyze(documents) → bool            │
│  - learn(corrections) → void                │
│  - estimate_cost(documents) → float         │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│           Agent Registry                    │
│  Discovers and manages all agents           │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│           Agent Runner                      │
│  Executes agents, tracks metrics            │
└─────────────────────────────────────────────┘
```

## Directory Structure

```
app/agents/                    # Framework core
├── base.py                    # Base agent class
├── registry.py                # Agent discovery
├── runner.py                  # Agent execution
└── README.md                  # This file

app/agents_library/            # Your agent implementations
├── core/                      # Production agents
│   ├── vehicle.py            # Vehicle intelligence
│   ├── medical.py            # Medical intelligence
│   ├── financial.py          # Financial intelligence
│   └── ...                   # 14 total core agents
│
└── experimental/              # Agents in development
    ├── investment_analyzer.py
    └── contract_intelligence.py
```

## Creating an Agent

### 1. Basic Agent Template

```python
from app.agents import IntelligenceAgent, Document, Insight

class MyAgent(IntelligenceAgent):
    # Metadata
    name = "My Intelligence Agent"
    version = "1.0.0"
    category = "my_category"
    description = "What this agent does"
    author = "your_name"

    # Configuration
    min_documents = 2
    license_type = "personal"  # or "free", "premium"

    def analyze(self, documents: List[Document]) -> List[Insight]:
        """Generate insights from documents"""
        insights = []

        # Your intelligence logic here
        # Analyze documents, extract patterns, generate recommendations

        return insights
```

### 2. Advanced Agent with Learning

```python
class SmartAgent(IntelligenceAgent):
    def __init__(self, config=None):
        super().__init__(config)
        self.patterns = []  # Store learned patterns

    def analyze(self, documents: List[Document]) -> List[Insight]:
        # Use learned patterns in analysis
        pass

    def learn(self, corrections: List[Correction]) -> None:
        """Learn from user corrections"""
        for correction in corrections:
            # Update internal patterns
            self.patterns.append(correction)
```

## Using Agents

### Personal Use (Current System)

```python
from app.agents import get_registry, get_runner

# Discover agents
registry = get_registry()
agents = registry.list_agents()
print(f"Found {len(agents)} agents")

# Run an agent
runner = get_runner()
result = runner.run_agent("core.vehicle", documents)

print(f"Generated {len(result.insights)} insights")
print(f"Cost: ${result.estimated_cost:.4f}")
print(f"Time: {result.execution_time:.2f}s")
```

### Business Extraction (Future)

Each agent can become:

1. **SaaS Feature**: Run as API endpoint
2. **Premium Add-on**: Charge for specialized agents
3. **Consulting Asset**: Deploy for clients
4. **Training Material**: Teach the pattern

## Agent Portfolio (Your IP)

Each agent you build is:

- **Working Code**: Solves real problems
- **Documented Expertise**: Your knowledge captured
- **Reusable Module**: Can be deployed anywhere
- **Potential Product**: Extractable if needed
- **Career Safety Net**: Fallback option

**Current Portfolio:**
- 14 Core Agents (personal life admin)
- ? Experimental Agents (in development)

## Business Framework (Byproduct)

### Agent as Product

```python
class PremiumFinancialAgent(IntelligenceAgent):
    name = "Advanced Financial Optimizer"
    license_type = "premium"
    price_monthly = 29.99  # Future: actual pricing

    def analyze(self, documents: List[Document]) -> List[Insight]:
        # Deep financial analysis
        # Multi-year projections
        # Tax optimization strategies
        # Investment recommendations
        pass
```

### Agent Marketplace Model

```yaml
# Future: Agent catalog for marketplace
agent_id: premium.financial_optimizer
name: Advanced Financial Optimizer
author: your_company
category: financial
price: $29.99/month
features:
  - Multi-year analysis
  - Tax optimization
  - Investment recommendations
  - Spending patterns
rating: 4.8/5.0
users: 1,247
```

## Cost Transparency

Each agent tracks:
- Estimated AI cost per run
- Execution time
- Number of insights generated
- Success/failure rate

**Example Output:**
```
Vehicle Intelligence Agent
- Analyzed: 12 documents
- Generated: 3 insights
- Cost: $0.045
- Time: 4.2s
- Success: True
```

## Testing Agents

```python
# Test agent with sample documents
test_docs = [
    Document(id="1", filename="insurance.pdf", ...),
    Document(id="2", filename="nct_cert.pdf", ...),
]

result = runner.run_agent("core.vehicle", test_docs)

assert result.success
assert len(result.insights) > 0
assert result.estimated_cost < 0.10  # Cost guard
```

## Migration Path

### Current System → Agent Framework

Your existing `category_intelligence.py` analyzers can be migrated:

```python
# Before (category_intelligence.py)
def analyze_vehicle_category():
    # 100 lines of code
    pass

# After (agents_library/core/vehicle.py)
class VehicleAgent(IntelligenceAgent):
    def analyze(self, documents):
        # Same logic, cleaner structure
        pass
```

**Benefits:**
- Cleaner code organization
- Reusable modules
- Testable units
- Extractable IP

## Next Steps

1. **Migrate Existing Analyzers**: Convert 14 category analyzers to agents
2. **Build New Agents**: Create specialized intelligence modules
3. **Document Each Agent**: Capture your expertise
4. **Test and Refine**: Make agents production-ready
5. **Build Portfolio**: Each agent is an asset

## Future Possibilities

### Agent Marketplace
- Developers build agents
- Users subscribe to agents
- Platform takes revenue share
- Network effects

### Vertical Products
- Financial Intelligence Platform (financial agents)
- Business Intelligence Platform (business agents)
- Legal Intelligence Platform (legal agents)

### Enterprise Services
- Custom agent development
- Agent consulting
- Training workshops
- Implementation services

## Philosophy Summary

**You're not building a business.**
**You're building options.**

Each agent you create:
- Solves a personal problem (value now)
- Builds your expertise portfolio (value later)
- Creates extraction opportunities (value if needed)

**Personal first. Business second. Always.**

---

*Built for personal use. Ready for business extraction. Designed for longevity.*
