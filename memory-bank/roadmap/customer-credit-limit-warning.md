---
version: next
status: planned
priority: medium
complexity: 2
linked_tasks: [customer-credit-limit-warning]
created: 2026-08-26
---

# Customer Credit Limit Warning

Add a customer credit limit warning to the Sale Order form. The warning is a computed text message that appears as a banner when a customer is approaching or exceeding their credit limit. Yellow at 80% of limit, red over 100%. The message includes the credit limit, current outstanding receivables, and how much this order would add. Empty (no banner) when the customer has no credit limit set or is well within limit.

**Complexity rationale**: Enhancement scoped to a single component (Sale Order model + form view) with clear, fully-specified thresholds and message content. Requires a computed field/banner widget with conditional styling but no cross-component design exploration — Level 2.
