# Vault UI Evolution

## Initial Design (Layer 1 - Minimalist)

**Date:** 2026-01-04

**Approach:** Ultra-minimal, single-column list
- No sidebar
- No filters
- No tabs
- Search bar at top
- Simple chronological list
- Separate upload page

**Philosophy:**
- Reduce cognitive load
- Hide all complexity
- Make it "boring and calm"
- Scannable within seconds

---

## Design Pivot: Single-Screen System

**Date:** 2026-01-04

**Decision:** Move to a more complete single-screen interface with navigation, filtering, and richer layout.

### Reasons for Change

1. **Practical usability over theoretical minimalism**
   - A document vault with hundreds or thousands of items needs filtering
   - Constantly navigating between pages creates friction
   - Search alone is not enough - users need to browse by type, date, source
   - Real-world use reveals that "just scroll" doesn't scale

2. **One-screen efficiency**
   - All controls visible at once
   - No context switching between upload/search/browse modes
   - Faster decision-making when everything is accessible
   - Reduces mental model complexity (one view, multiple tools)

3. **Information density without clutter**
   - More can fit on screen if layout is structured (table vs list)
   - Users can scan multiple attributes at once (name, date, type, source)
   - Visual hierarchy through layout, not through hiding information

4. **Family member usability**
   - Non-technical users benefit from visible options (not hidden behind pages)
   - Clear visual structure (sidebar + main area) is familiar
   - Filters prevent overwhelming "scroll through everything" experience
   - Icons and visual cues aid recognition

5. **Long-term viability**
   - System needs to work with 5 years of documents, not just 50 items
   - Filtering by date ranges, document types, sources is essential
   - Quick access to common actions (upload, search, filter) needed
   - Single screen reduces "where did I put that feature?" confusion

### What This Means

**We keep:**
- Zero decision-making at intake
- Documents as source of truth
- No AI features at this layer
- Calm, trustworthy visual design
- UK English, plain language
- No tags, categories, or manual filing

**We add:**
- Left sidebar for navigation
- Filter options (by source type, date range)
- Table layout with multiple columns
- File type icons for quick recognition
- All controls on one screen
- Upload integrated into main view

**We reject:**
- Status badges (Active, Critical, etc.) - not relevant to document vault
- User avatars - single-user/family system
- Configuration screens - keep it simple
- Dashboards and analytics - future layer

### Core Principle Update

The system remains **boring, durable, and understandable**.

But "minimal" does not mean "featureless" - it means:
- Every feature earns its place through utility
- Visual design stays calm and neutral
- No cognitive overhead during capture
- Efficient access to stored documents

**One screen > multiple simple screens**

This is still Layer 1 (pre-AI). It's just a more complete Layer 1.

---

## Next Steps

Build single-screen Vault UI with:
1. Left sidebar (navigation + quick upload)
2. Top bar (search + breadcrumb/title)
3. Main area: table layout with columns
4. Filter controls (source type, date range)
5. File type icons (PDF, image, email, etc.)
6. Clean, spacious design inspired by reference image
