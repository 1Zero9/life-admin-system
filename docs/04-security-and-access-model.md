# Life Admin System – Security and Access Model

This system contains sensitive personal and family information.

Security must be strong, but must never prevent legitimate access by the family.

## Core security principles

- Protect against unauthorised access
- Avoid single points of failure
- Prefer clarity over obscurity
- Security must not rely on one person’s memory

---

## Access roles

### Owner
- Full access to all data
- Can grant and revoke access
- Responsible for system stewardship

### Co-owner
- Full access to life admin items
- Can add, view, and understand everything
- Cannot accidentally destroy the system

### Viewer
- Read-only access to selected items
- Intended for children or trusted family members

### Emergency / Executor access
- Access intended for serious illness, death, or incapacity
- Clearly documented and deliberate
- Must not require technical knowledge to use

---

## Authentication principles

- Multi-factor authentication required
- No shared passwords
- Access tied to people, not devices
- Recovery mechanisms must exist

---

## Data protection principles

- Data encrypted at rest
- Data encrypted in transit
- No passwords stored inside documents
- Credentials referenced externally where required

---

## Failure scenarios considered

This model must still work if:
- The primary owner is unavailable
- A cloud provider disappears
- A device is lost
- A password is forgotten

Security must degrade safely, not lock people out forever.
