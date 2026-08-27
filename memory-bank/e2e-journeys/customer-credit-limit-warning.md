# E2E Journey: Customer Credit Limit Warning

**Task**: customer-credit-limit-warning
**Feature**: customer-credit-limit-warning
**Primary Persona**: Sales rep / accountant (productBrief.md § Key Personas)
**Journey Type**: Synchronous, single-screen (no navigation required to reveal)

## Overview

A Sale Order form shows a computed, non-blocking banner immediately below the
status bar warning that a customer is approaching (yellow) or has exceeded
(red) their credit limit. The banner is driven by `credit_limit_warning_level`
(`'warning'` / `'danger'` / falsy) and the existing `partner_credit_warning`
text field on `sale.order`, both provided by the `sale_credit_limit_warning`
addon.

## Preconditions

- `res.company.account_use_credit_limit` is enabled (Settings > Invoicing >
  "Sales Credit Limit").
- At least one customer (`res.partner`) has `credit_limit` set to a non-zero
  value, with existing receivables (`credit` + `credit_to_invoice`) that can be
  pushed into the 80%-100% (warning) and >100% (danger) ranges by adding order
  lines.
- A second customer has `credit_limit` unset/0 (control case — no banner ever).

## Test Accounts Used

| Role | Email | Notes |
|------|-------|-------|
| sales_user | (resolve via `uat-config.md` persona map) | Member of Sales group only — NOT `account.group_account_invoice` / `account.group_account_readonly`. Used for AC-ERROR-1 (`.sudo()` access coverage). |
| accountant | (resolve via `uat-config.md` persona map) | Member of `account.group_account_invoice` or higher. Used for the primary happy-path walk. |

## Happy Path

### Step 1: Open a new Sale Order
**Actor**: accountant
- Navigate: Sales app → Quotations → New
- **Verify**: A new Sale Order form opens in `draft` state with no banner visible (no `partner_id` set yet)

### Step 2: Select a customer near their credit limit
**Actor**: accountant
- Set `partner_id` to the customer prepared to sit in the 80%-100% exposure range (before adding lines)
- Add order lines such that `outstanding + amount_total` lands between 80% (inclusive) and 100% (inclusive) of `credit_limit`
- **Verify**:
  - A yellow (`alert-warning`) banner appears directly below the status bar, with no extra click/navigation (AC-ENTRY-1, AC-HAPPY-1)
  - The message states the credit limit, current outstanding receivables, and this order's added amount
  - `credit_limit_warning_level == 'warning'`

### Step 3: Increase the order past the credit limit
**Actor**: accountant
- Add further order lines so `outstanding + amount_total` exceeds `credit_limit`
- **Verify**:
  - The banner switches to red (`alert-danger`) (AC-HAPPY-2)
  - The message still breaks out credit limit, outstanding receivables, and this order's contribution
  - `credit_limit_warning_level == 'danger'`

### Step 4: Switch to the customer with no credit limit set
**Actor**: accountant
- Change `partner_id` to the customer with `credit_limit` unset/0
- **Verify**: No banner is visible; `partner_credit_warning == ''` and `credit_limit_warning_level` is falsy (AC-HAPPY-3a)

**Cleanup**: Discard/delete the quotation created in this section (no persisted data expected — computed fields are `store=False`, so cleanup is optional but keep test data tidy).

## Negative / Access-Denied Paths

### N1: Sales-only user still sees the correct banner
**Actor**: sales_user (no `account.group_account_invoice` / `account.group_account_readonly`)
- Navigate: Sales app → Quotations → open the over-limit order from Step 3 (or recreate an equivalent order/customer pairing as this persona, if the prior order isn't accessible)
- **Verify**: The correct-tier banner (red, over limit) still renders — the warning must not be silently blank due to the viewing user's access rights on `credit` / `credit_to_invoice` / `credit_limit` (AC-ERROR-1)

**Cleanup**: None (read-only step).

## Error Scenarios

### E1: Confirmed order never shows the banner
**Actor**: accountant
- Take the over-limit order from Step 3 and confirm it (state → `sale`)
- **Verify**: The banner disappears once the order leaves `draft`/`sent` state, regardless of exposure (AC-HAPPY-3b, per the order-state gate)

### E2: Well-within-limit exposure shows no banner
**Actor**: accountant
- Create a new quotation for the near-limit customer (Step 2's customer) with order lines kept small enough that `outstanding + amount_total < 80% of credit_limit`
- **Verify**: No banner is visible (AC-HAPPY-3c)

**Cleanup**: Discard/delete quotations created in this section.

## Accessibility Notes

- Banner `<div>` carries `role="alert"` — screen readers should announce it when it becomes visible after a customer/line change.
- Banner text alone (not color) must convey severity — confirm the message's lead sentence ("approaching" vs. "has exceeded") is present and read by assistive tech, not just the yellow/red styling.

## Out of Scope for This Journey

- `res.config.settings` / `account_use_credit_limit` toggle UI — not modified by this feature.
- Customer invoice form banner (`account.move`) — untouched, out of scope per the task's Scope Boundaries.
- Multi-company credit exposure edge cases beyond core's existing `with_company` handling.
