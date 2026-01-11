# Agent Development Guide

## Purpose

This guide shows you how to build intelligence agents for your personal system. Each agent you build serves your needs first, but is structured for potential business extraction later.

---

## Why Build Agents?

**Personal Value:**
- Solve specific problems you have
- Automate intelligence gathering
- Get actionable recommendations
- Build expertise in domains

**Portfolio Value:**
- Each agent is documented expertise
- Reusable, modular code
- Potential consulting asset
- Career safety net

**Business Value (Future):**
- Can be sold as premium features
- Consulting deliverables
- Training examples
- Product components

---

## Agent Development Workflow

### 1. Identify Personal Need

**Start with a real problem:**
- "I keep missing insurance renewal dates"
- "I don't know if I'm overpaying for utilities"
- "Tax season is chaos every year"
- "I forget medical appointments"

**Questions to ask:**
- What documents do I have related to this?
- What insights would help me?
- What actions should I take?
- How often do I need this intelligence?

### 2. Design the Agent

**Define scope:**
```python
Agent Name: Vehicle Insurance Intelligence
Category: vehicle
Purpose: Track insurance policies, renewal dates, coverage gaps

Expected Documents:
- Insurance policies
- Renewal notices
- Coverage letters
- Claims history

Expected Insights:
- "Insurance renews in 30 days - compare quotes"
- "Coverage gap: no windscreen protection"
- "Premium increased 15% - review policy"
- "3 years claim-free - request discount"

Minimum Documents: 1 policy
Analysis Frequency: Monthly
```

### 3. Implement the Agent

**Use the template:**
```python
# app/agents_library/core/vehicle_insurance.py
from app.agents import IntelligenceAgent, Document, Insight
from typing import List

class VehicleInsuranceAgent(IntelligenceAgent):
    # Metadata
    name = "Vehicle Insurance Intelligence"
    version = "1.0.0"
    category = "vehicle"
    description = "Insurance policy tracking, renewal reminders, coverage analysis"
    author = "your_name"

    # Configuration
    min_documents = 1
    max_documents = 20
    license_type = "personal"

    def analyze(self, documents: List[Document]) -> List[Insight]:
        """Analyze insurance documents for renewal and coverage intelligence"""
        insights = []

        # Extract policies
        policies = [doc for doc in documents if "insurance" in doc.filename.lower()]

        # Find renewal dates
        for policy in policies:
            renewal_date = self._extract_renewal_date(policy)
            if renewal_date and self._is_upcoming(renewal_date, days=60):
                insights.append(
                    Insight(
                        title=f"Insurance Renewal Approaching",
                        description=f"Your {policy.vendor} policy renews on {renewal_date}",
                        recommendation="Compare quotes from 3 providers and review coverage",
                        priority="high" if self._is_upcoming(renewal_date, 30) else "medium",
                        category=self.category,
                        metadata={"policy_file": policy.filename, "renewal_date": renewal_date},
                        confidence=0.9,
                    )
                )

        # Check for coverage gaps
        # Check for premium changes
        # Check for claim history patterns

        return insights

    def _extract_renewal_date(self, document: Document) -> str:
        """Extract renewal date from document text"""
        # Your extraction logic here
        pass

    def _is_upcoming(self, date_str: str, days: int) -> bool:
        """Check if date is within X days"""
        # Your date logic here
        pass
```

### 4. Test the Agent

**Manual testing:**
```python
from app.agents import get_registry, get_runner, Document

# Create test documents
test_docs = [
    Document(
        id="test1",
        filename="car_insurance_2024.pdf",
        content_type="application/pdf",
        extracted_text="Policy renewal date: 15 March 2026...",
        vendor="Campions Insurance",
    )
]

# Run agent
runner = get_runner()
result = runner.run_agent("core.vehicle_insurance", test_docs)

# Check results
print(f"Success: {result.success}")
print(f"Insights: {len(result.insights)}")
for insight in result.insights:
    print(f"  - {insight.title}")
    print(f"    {insight.description}")
```

### 5. Document the Agent

**Create agent documentation:**
```markdown
# Vehicle Insurance Intelligence Agent

## Purpose
Tracks insurance policies, renewal dates, and coverage to prevent lapses and overpayment.

## What It Analyzes
- Insurance policy documents
- Renewal notices
- Coverage letters
- Claims history

## Insights Generated
1. Renewal reminders (30-60 days advance)
2. Coverage gap identification
3. Premium change detection
4. Claim pattern analysis

## Personal Value
- Never miss renewal deadlines
- Identify coverage gaps before incidents
- Track premium changes over time
- Optimize insurance costs

## Business Potential
- Insurance brokers could use for client management
- Could be sold as $19/month add-on
- Consulting deliverable for insurance practice
```

### 6. Iterate and Improve

**Based on real use:**
- Did it catch your renewal? ✓ Works
- Did it find coverage gaps? ✗ Improve detection
- Was the recommendation helpful? ✓ Keep format
- Too many false positives? ✗ Tune confidence threshold

---

## Agent Templates

### Simple Pattern Detection Agent

```python
class PatternDetectionAgent(IntelligenceAgent):
    """Detects patterns in recurring documents"""

    def analyze(self, documents: List[Document]) -> List[Insight]:
        insights = []

        # Group by vendor
        by_vendor = {}
        for doc in documents:
            vendor = doc.vendor or "unknown"
            by_vendor.setdefault(vendor, []).append(doc)

        # Find vendors with 3+ documents
        for vendor, vendor_docs in by_vendor.items():
            if len(vendor_docs) >= 3:
                insights.append(
                    Insight(
                        title=f"Recurring Vendor: {vendor}",
                        description=f"You have {len(vendor_docs)} documents from {vendor}",
                        recommendation="Review relationship and ensure getting best value",
                        priority="low",
                        category=self.category,
                        metadata={"vendor": vendor, "document_count": len(vendor_docs)},
                    )
                )

        return insights
```

### Date-Based Alert Agent

```python
class DateAlertAgent(IntelligenceAgent):
    """Alerts on upcoming dates"""

    def analyze(self, documents: List[Document]) -> List[Insight]:
        insights = []
        today = datetime.now()

        for doc in documents:
            if not doc.date:
                continue

            doc_date = self._parse_date(doc.date)
            if not doc_date:
                continue

            days_until = (doc_date - today).days

            if 0 < days_until <= 90:
                priority = "high" if days_until <= 7 else "medium" if days_until <= 30 else "low"

                insights.append(
                    Insight(
                        title=f"Upcoming Date: {doc.filename}",
                        description=f"Date in {days_until} days ({doc.date})",
                        recommendation="Review and take action if needed",
                        priority=priority,
                        category=self.category,
                        metadata={"days_until": days_until, "date": doc.date},
                    )
                )

        return insights
```

### Cost Analysis Agent

```python
class CostAnalysisAgent(IntelligenceAgent):
    """Analyzes spending patterns"""

    def analyze(self, documents: List[Document]) -> List[Insight]:
        insights = []

        # Extract amounts
        amounts = []
        for doc in documents:
            if doc.amount:
                amount_value = self._parse_amount(doc.amount)
                if amount_value:
                    amounts.append((doc, amount_value))

        if not amounts:
            return insights

        # Calculate statistics
        total = sum(amount for _, amount in amounts)
        avg = total / len(amounts)
        high = max(amount for _, amount in amounts)

        # Find outliers (> 2x average)
        for doc, amount in amounts:
            if amount > avg * 2:
                insights.append(
                    Insight(
                        title=f"High Cost Alert: {doc.vendor}",
                        description=f"{doc.amount} is {amount/avg:.1f}x average spending",
                        recommendation="Review if this expense was expected",
                        priority="medium",
                        category=self.category,
                        metadata={"amount": amount, "average": avg},
                    )
                )

        return insights
```

---

## Agent Ideas (Personal Needs → Portfolio)

### Financial Domain

1. **Subscription Tracker** - Find recurring charges, identify unused subscriptions
2. **Budget Variance** - Compare spending to patterns, flag anomalies
3. **Investment Rebalancer** - Track portfolio drift, suggest rebalancing
4. **Tax Deduction Finder** - Identify deductible expenses

### Medical Domain

5. **Medication Reminder** - Track prescriptions, refill dates
6. **Appointment Follow-up** - Detect missed follow-ups
7. **Health Trend Analyzer** - Track vitals over time
8. **Insurance Claim Tracker** - Monitor claim status

### Business Domain

9. **Contract Renewal Manager** - Track all contracts, renewal dates
10. **Invoice Payment Tracker** - Find overdue invoices
11. **Client Health Score** - Analyze client engagement
12. **Compliance Checker** - Ensure regulatory requirements met

### Home Domain

13. **Maintenance Scheduler** - Track home maintenance by last service date
14. **Warranty Tracker** - Track appliance warranties
15. **Energy Usage Analyzer** - Compare utility bills over time
16. **Property Tax Optimizer** - Track assessments, flag increases

---

## Building Your Portfolio

### Current Portfolio (Example)

```
Agent Portfolio - 18 Total

Core Agents (14): Production, personal use
1. ✅ Vehicle Intelligence
2. ✅ Medical Intelligence
3. ✅ Financial Intelligence
... (11 more)

Experimental Agents (4): In development
15. 🔨 Investment Analyzer (80% complete)
16. 🔨 Subscription Tracker (testing)
17. 💡 Contract Intelligence (design phase)
18. 💡 Energy Optimizer (idea)

Legend:
✅ = Production (working, tested)
🔨 = In Development (building)
💡 = Planned (idea stage)
```

### Portfolio Growth Strategy

**Month 1-2: Migrate Existing**
- Convert 14 category analyzers to agent framework
- Document each agent
- Test in personal system

**Month 3-4: Fill Personal Gaps**
- Build 2-3 agents for problems you actually have
- Test, iterate, refine
- Document lessons learned

**Month 5-6: Experiment & Learn**
- Try different agent patterns
- Test AI models (Haiku vs Sonnet)
- Optimize costs and accuracy

**Month 7-12: Build Depth**
- Pick 2-3 domains to specialize in
- Build advanced versions
- Create agent families (basic → advanced)

**Year 2: Assess & Extract**
- Review what works
- Identify most valuable agents
- Decide if/what to extract

---

## Agent Quality Checklist

Before marking an agent "production ready":

**Functionality:**
- [ ] Solves real personal problem
- [ ] Tested with actual documents
- [ ] Generates useful insights
- [ ] Handles edge cases gracefully
- [ ] Cost estimates are accurate

**Code Quality:**
- [ ] Clean, readable code
- [ ] Proper error handling
- [ ] Documented functions
- [ ] Type hints used
- [ ] No hardcoded values

**Documentation:**
- [ ] Purpose clearly stated
- [ ] Input/output documented
- [ ] Examples provided
- [ ] Limitations noted
- [ ] Business potential assessed

**Extractability:**
- [ ] Self-contained (minimal dependencies)
- [ ] Configurable (no personal data hardcoded)
- [ ] Testable (can run standalone)
- [ ] Reusable (works in different contexts)

---

## Next Actions

**This Week:**
1. Pick one personal problem to solve
2. Design the agent (use template above)
3. Implement basic version
4. Test with your documents

**This Month:**
5. Migrate 2-3 existing category analyzers
6. Build 1 new experimental agent
7. Document lessons learned

**This Quarter:**
8. Convert all 14 core agents
9. Build 3-5 new specialized agents
10. Create agent showcase/catalog

**This Year:**
11. Build portfolio of 20+ agents
12. Document expertise in each domain
13. Assess business extraction options

---

## Remember

**Personal First:**
- Build for problems you actually have
- Test with your real documents
- Keep what works, discard what doesn't

**Quality Over Quantity:**
- One excellent agent > Five mediocre ones
- Solve problems completely
- Build for longevity

**Document Everything:**
- Your future self will thank you
- Others can learn from it
- Business value is in the documentation

**Create Options, Not Obligations:**
- Each agent is an asset
- No pressure to monetize
- Safety net if needed

---

*Build for yourself. Document for future. Extract if needed.*
