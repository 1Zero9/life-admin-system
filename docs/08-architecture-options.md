# Life Admin System – Architecture Options

This system must support daily use today and graceful survival decades into the future.

Architecture choices must serve the principles, not constrain them.

---

## Architectural constraints

Any implementation must:

- Honour zero-friction intake
- Keep documents as source of truth
- Support full data export
- Avoid single-vendor lock-in
- Be understandable by non-technical users
- Degrade gracefully if parts fail

---

## Acceptable architectural shapes

### Web-first system
- Browser-based interface
- Centralised document store
- Cloud-backed storage
- Suitable for daily family use

---

### Hybrid system
- Web interface for daily use
- Periodic offline archive generation
- Self-contained export for long-term survival

---

### Archive-first system
- Data stored as a structured archive
- Lightweight UI layered on top
- Prioritises longevity over convenience

---

## Storage principles

- Documents stored in standard formats
- Metadata stored separately and exportable
- Storage provider replaceable without data loss
- Offline copy always possible

---

## What this avoids

- Tight coupling between UI and data
- App-only data models
- Vendor-specific logic embedded in data
- Irreversible architectural decisions early on

Architecture must remain adaptable as technology evolves.
