# UAT Report: customer-credit-limit-warning

**Run ID**: 20260828-1424
**Task**: customer-credit-limit-warning
**Feature**: customer-credit-limit-warning
**Journey**: memory-bank/e2e-journeys/customer-credit-limit-warning.md
**Environment**: dev — http://localhost:8069 (db: `workshop`)
**Sections walked**: happy, mobile
**Plugin Version**: Banyan 2.2.1
**Timestamp**: 2026-08-28T14:24:00-04:00
**ux-patterns.md**: skipped (`--skip-ux-check`)

## Result: PASS_WITH_RECOMMENDATIONS

**Counts**: Required=0, Recommended=1, Optional=0
**Confidence**: high=1

## Pre-flight note

The `sale_credit_limit_warning` module was found **uninstalled** in the target
dev database at the start of this run (verified via
`ir_module_module.state = 'uninstalled'`), despite the task's Execution State
showing both build phases COMPLETE with all module-suite tests passing. It was
installed for this run via `odoo-bin -i sale_credit_limit_warning
--stop-after-init` (clean install, 0 errors). This is an environment-setup gap,
not a code defect — flagged here so the next `/bmb:build` or deploy step
doesn't assume the dev DB already reflects merged addons.

## Happy Path — accountant persona (walked as Administrator, superset access)

| Step | Verify | Result | Evidence |
|------|--------|--------|----------|
| 1. Open new Sale Order | No banner, `draft` state, no partner | PASS | screenshot (blank form, no `partner_credit_warning`) |
| 2. Customer near limit (Deco Addict, limit $1,000, outstanding $400) + order $510 | Yellow `alert-warning` banner; states limit/outstanding/order amount; `credit_limit_warning_level == 'warning'` | PASS | DOM: `div[role=alert].alert-warning`; banner text: "Deco Addict is approaching its credit limit of $1,000.00. Current outstanding receivables: $400.00. This order would add: $510.00." |
| 3. Push order to $680 (exposure $1,080 > $1,000) | Red `alert-danger` banner; same 3-part breakdown; `credit_limit_warning_level == 'danger'` | PASS | DOM: `div[role=alert].alert-danger`; banner text: "Deco Addict has exceeded its credit limit of $1,000.00. Current outstanding receivables: $400.00. This order would add: $680.00." |
| 4. Switch to Acme Corporation (explicit `credit_limit = 0` override) | No banner at all | PASS | `document.querySelectorAll('div[role="alert"]')` → `[]` |

**AC-ENTRY-1, AC-HAPPY-1, AC-HAPPY-2, AC-HAPPY-3a**: all confirmed.

**Cleanup**: Test quotation S00023 set to `Cancelled` state (soft-cancel; no persisted data was expected since these are `store=False` computed fields).

## Mobile — 375×667 viewport

Re-opened S00023 (Deco Addict, $680, danger tier) at 375×667. The red banner
renders full-width, wraps its text correctly with no horizontal overflow or
truncation, and remains directly below the status bar with no extra
navigation needed. PASS.

## Negative / Error scenarios

Not walked — `--sections` was not passed and no `default_sections` is
configured in `projectConfig.md`, so this run used the built-in fallback
(`happy,mobile`). N1 (sales-only user access), E1 (confirmed order hides
banner), and E2 (well-within-limit shows no banner) remain unverified by this
run. Recommend `/bmb:uat customer-credit-limit-warning --sections negatives,errors`
as a follow-up before considering the full journey covered.

## Findings

### R1 — Recommended (confidence: high)
**Category**: Journey Doc / Test Environment
**Summary**: The journey's "no credit limit set" precondition doesn't hold for any customer by default in this dev database — a global `ir.default` fallback sets `res.partner.credit_limit = 1.0` for every partner without an explicit per-record override (confirmed via `ir_default` table, `field_id` for `res.partner.credit_limit`, `json_value = 1.0`). A customer with no explicit override (e.g. "Azure Interior") still triggers a banner ("has exceeded its credit limit of $1.00...") because `1.0` is truthy, not falsy.
**Impact**: AC-HAPPY-3a ("no limit set / unset") cannot be exercised against an arbitrary customer — a tester must explicitly set `credit_limit = 0` on a specific partner (done here: Acme Corporation) to get a true control case. This is not a defect in `sale_credit_limit_warning`'s logic (`if not credit_limit` correctly treats an explicit `0` as falsy), but the journey doc's Preconditions section should say "explicitly set `credit_limit = 0`" rather than "unset/0", since "unset" resolves to `1.0` here.
**Evidence**: DB query (`ir_default` table) + browser observation (Azure Interior banner at $1.00 limit before the override).
**Recommendation**: Update `memory-bank/e2e-journeys/customer-credit-limit-warning.md` Preconditions to call out the `ir.default` fallback explicitly, and keep Acme Corporation (id 10) provisioned with `credit_limit = 0` as the durable control-case fixture for future UAT/E2E runs.

## Next Step

`/bmb:build customer-credit-limit-warning` to implement the E2E spec below.
