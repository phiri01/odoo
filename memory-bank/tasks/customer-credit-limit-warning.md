---
slug: customer-credit-limit-warning
legacy_id:
feature: customer-credit-limit-warning
status: INITIALIZED
---

# customer-credit-limit-warning: Customer Credit Limit Warning

**Complexity**: Level 2
**Status**: INITIALIZED
**Roadmap**: customer-credit-limit-warning
**Branch**: feature/customer-credit-limit-warning
**Worktree**: N/A

## Task Description

Add a customer credit limit warning to the Sale Order form. The warning is a computed text message that appears as a banner when a customer is approaching or exceeding their credit limit. Yellow at 80% of limit, red over 100%. The message includes the credit limit, current outstanding receivables, and how much this order would add. Empty (no banner) when the customer has no credit limit set or is well within limit.

## User Journey Definition

**Feature Type**: [End-User Feature | NFR/Infrastructure]
**Creative Phase Required**: [Yes - Type | No]

### Invocation Method (End-User Features)
- **Location**: [exact page/screen/component]
- **Element**: [exact button/link/command]
- **Visibility**: [always visible | conditional]
- **Navigation**: [steps from entry to feature]

### Success Criteria (End-User Features)
- **User sees**: [exact message/screen/feedback]
- **User can verify at**: [exact location]
- **Data persisted**: [what and where]
- **Observable within**: [timeframe]

### NFR Verification (Infrastructure Features)
- **Test method**: [exact command/tool]
- **Success metrics**: [specific thresholds]
- **Observable at**: [dashboard/log location]

### Acceptance Criteria
- AC-ENTRY-1: [user can find the feature]
- AC-HAPPY-1: [user completes primary journey]
- AC-ERROR-1: [error handling]

## Test Strategy

### Approach
- **Emphasis**: [unit | integration | E2E | balanced — override systemPatterns.md default if needed]
- **Target test count**: [N total across all phases — justify if >20]

### File Organization
- **New test files**: [list files to create and what they cover]
- **Extend existing**: [list existing test files to add tests to, rather than creating new ones]

### What NOT to Test
- [Thing] — [reason: covered by type system / existing tests / framework / out of scope]

### Per-Phase Test Guidance
- Phase 1: [N tests — what behaviors to verify]
- Phase 2: [N tests — what behaviors to verify]

## Implementation Roadmap

### New Source Files (pin path + extension)
<!--
  Pin EVERY new source file (incl. hooks/utils/types — not just components) with
  its explicit path AND extension, resolved from systemPatterns.md → Code
  Organization Patterns / techContext.md → Source extensions. This removes the
  extension from being an ad-hoc build-time guess. Use "extend" for files modified.
-->
- [ ] [e.g., `frontend/src/hooks/useFeedbackSubmitMutation.ts` — submit mutation hook]
- [ ] [e.g., `frontend/src/components/FeedbackWidget.tsx` — widget]

### Phases
- [ ] Phase 1: [phase name]
- [ ] Phase 2: [phase name]

## Creative Phases

- [ ] [Architecture | User Journey | UI/UX | Algorithm] design → pending

---

## Execution State

**Build Status**: IDLE
**Last Completed**: N/A
**Can Resume**: NO

### Active Sub-Agents
(none)

### Completed Steps
(none)
