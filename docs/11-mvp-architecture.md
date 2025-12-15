# Life Admin System – MVP Architecture

The MVP architecture is designed to support daily use while remaining portable and replaceable.

## Architectural layers

1. Intake
2. Archive
3. Understanding
4. Insight

Each layer must be independently replaceable.

## MVP includes

- Intake layer
- Archive layer
- Basic understanding layer

## MVP excludes

- Automation that acts without review
- Complex insights
- Tight coupling between layers
- Vendor-specific data formats

## Direction of flow

Data flows one way only:
Intake → Archive → Understanding → Insight

Breaking this rule breaks the system.
