# E2E Spec: customer-credit-limit-warning

**Source UAT run**: 20260828-1424 (PASS_WITH_RECOMMENDATIONS)
**Target framework**: Odoo `TransactionCase` / `HttpCase` (Python) — this
codebase has no JS tour or Playwright/Cypress harness (`techContext.md`:
"No pytest setup; standard Odoo `TransactionCase`/`HttpCase` tests are
discovered via each module's `tests/` package"). The confirmed selectors
below are still recorded for a future browser-driven harness if one is added.

Extend the existing suite at
`addons/sale_credit_limit_warning/tests/test_sale_order_credit_warning.py`
rather than creating a new file — it already covers the compute logic this
spec exercises end-to-end through the UI.

## Fixtures Confirmed During Walk

- Customer with a real, non-trivial limit: **Deco Addict** (`res.partner`
  `credit_limit = 1000` for company 1, pre-existing demo data).
- Control-case customer with an **explicit zero** limit: **Acme Corporation**
  (`res.partner` id 10) — had to be provisioned during this run because no
  demo partner has a truly falsy `credit_limit` (see UAT report Finding R1:
  a global `ir.default` fallback of `1.0` applies to every partner without
  an explicit override). Any E2E test for the "no banner" case MUST use a
  partner with an explicit `credit_limit = 0.0` write, not an unset one.
- Product used to control order totals precisely: `[FURN_1118] Corner Desk
  Left Sit`, unit price $85.00 (quantity is the only lever needed).

## Confirmed Selectors / DOM Contract

- Banner container: `div[role="alert"]` — exactly one or zero present at a
  time (the view's xpath makes the two tiers mutually exclusive).
- Tier via class: `alert-warning` (yellow / approaching) vs `alert-danger`
  (red / exceeded). Assert on this class, not on text color.
- No separate "hidden" banner element to check — when `credit_limit_warning_level`
  is falsy, `document.querySelectorAll('div[role="alert"]')` returns `[]`.
  Do not assert on `display: none`; the divs are removed from the DOM
  (Odoo `invisible` on an owl template), not merely hidden.
- Banner appears immediately on setting `partner_id` / order line changes —
  no save/reload required (client-side onchange recompute). No explicit wait
  condition beyond Odoo's normal form re-render was needed during the walk.

## Test Cases to Implement (Python `TransactionCase`, mirrors the UI walk)

1. **test_e2e_warning_tier_via_ui_equivalent_values** — partner with
   `credit_limit=1000`, `credit=400` (pre-existing outstanding), new order
   with lines totaling `510` → assert `partner_credit_warning` contains the
   limit ($1,000.00), outstanding ($400.00), and order-add ($510.00) figures,
   and `credit_limit_warning_level == 'warning'`.
2. **test_e2e_danger_tier_via_ui_equivalent_values** — same partner, order
   total `680` (exposure `1080 > 1000`) → `credit_limit_warning_level ==
   'danger'`, message still breaks out all three figures.
3. **test_e2e_no_banner_explicit_zero_limit** — partner with an **explicit**
   `credit_limit = 0.0` (not merely unset — see Fixtures note above), any
   order amount → `partner_credit_warning == ''`, `credit_limit_warning_level`
   falsy. This is the case the manual UI walk needed a new fixture for; codify
   that fixture in the test (`self.env['res.partner'].create({...,
   'credit_limit': 0.0})` or an explicit write on an existing demo partner).
4. **test_e2e_mobile_viewport_no_regression** — out of scope for a Python
   `TransactionCase` (no viewport concept server-side). If a JS/tour harness
   is ever added, port this as: load the form at 375×667, assert the same
   `div[role="alert"]` class contract and that the container's rendered width
   does not exceed the viewport (no horizontal scroll introduced).

## Explicitly Not Covered by This Spec

Per the UAT report, `negatives` (N1 — sales-only user access) and `errors`
(E1 — confirmed order hides banner, E2 — well-within-limit shows no banner)
were not walked in this run. Phase 1/2's existing test suite already covers
E1/E2/N1 at the compute-logic level (see task file Test Strategy: tests for
order-state gate and non-accounting-user access already exist and pass). No
new test cases are proposed here for those paths; re-run `/bmb:uat
customer-credit-limit-warning --sections negatives,errors` to get UI-level
confirmation if desired.
