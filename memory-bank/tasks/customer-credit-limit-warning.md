---
slug: customer-credit-limit-warning
legacy_id:
feature: customer-credit-limit-warning
status: BUILD_COMPLETE
---

# customer-credit-limit-warning: Customer Credit Limit Warning

**Complexity**: Level 2
**Status**: BUILD_COMPLETE
**Roadmap**: customer-credit-limit-warning
**Branch**: feature/customer-credit-limit-warning
**Worktree**: N/A (working tree is the checkout itself; no separate worktree created)

## Task Description

Add a customer credit limit warning to the Sale Order form. The warning is a computed text message that appears as a banner when a customer is approaching or exceeding their credit limit. Yellow at 80% of limit, red over 100%. The message includes the credit limit, current outstanding receivables, and how much this order would add. Empty (no banner) when the customer has no credit limit set or is well within limit.

## Specification

**Feature Type**: End-User Feature
**Primary Persona**: End User — Sales rep / accountant (productBrief.md § Key Personas: "sales rep / accountant / HR staff / warehouse worker" using the respective business app day-to-day; here specifically the Sales app quotation flow)
**Creative Exploration Needed**: No — see "Design decisions made" under Scope Boundaries for judgment calls resolved here since Level 2 has no creative phase

### Invocation Method

**Existing core mechanism (read before implementing):** Odoo core (stock, unmodified in this fork) already ships ~80% of this feature. **Do not build from scratch — extend via `_inherit`.**

- `res.company.account_use_credit_limit` (Boolean, `addons/account/models/company.py:154`) — global on/off toggle, set via Settings > Invoicing > "Sales Credit Limit". Must be `True` for any warning to show.
- `res.partner.credit_limit` (Float, company_dependent, `addons/account/models/partner.py:524-527`) — per-partner credit limit. Falsy (0/unset) means "no limit set."
- `res.partner.credit` (Monetary, computed, `addons/account/models/partner.py:517-519`) — total already-invoiced receivable ("Total Receivable").
- `res.partner.credit_to_invoice` (Monetary, computed, `addons/account/models/partner.py:520-523`, extended in `addons/sale/models/res_partner.py:80-107`) — confirmed-but-not-yet-invoiced sale order amounts.
- `sale.order.partner_credit_warning` (Text, computed, `addons/sale/models/sale_order.py:299-300`) — the existing banner field, computed by `_compute_partner_credit_warning` (`addons/sale/models/sale_order.py:770-781`), gated on `order.state in ('draft', 'sent')` and `company_id.account_use_credit_limit`.
- `account.move._build_credit_warning_message` (`addons/account/models/account_move.py:1846-1889`) — shared helper the sale order compute delegates to. Computes `total_credit = partner.credit + partner.credit_to_invoice(- exclude_amount) + current_amount`; returns `''` if `not credit_limit or total_credit <= credit_limit` (i.e., **only fires strictly over 100%**, single message combining everything into one "Total amount due" line — no separate breakdown of outstanding vs. this order).
- View: `addons/sale/views/sale_order_views.xml:301-305` — a single `<div class="alert alert-warning" invisible="partner_credit_warning == ''">` right under the form `<header>`. Always yellow; never red; never shown at 80%.

**Gaps this task must fill** (the actual scope of work): (1) an "approaching" 80% yellow tier that core does not have at all, (2) a red/danger tier at >100% (core only ever renders `alert-warning`), (3) a message that explicitly breaks out credit limit / current outstanding receivables / this order's addition as three distinct figures (core combines them into one total). `partner_credit_warning` is purely informational — grep confirms it is never used to block `action_confirm` or raise a `UserError` anywhere in `sale`/`account`, so this remains a non-blocking banner, matching the task description.

**New module:**
- **Recommended approach**: new addon `addons/sale_credit_limit_warning/` (per systemPatterns.md "Extend, don't modify" — `_inherit`, manifest `depends: ['sale', 'account']`). Do not edit `addons/sale/*` directly.
- **Confidence**: HIGH — this is a standard Odoo extension pattern with a directly analogous precedent already in core (`addons/sale/models/res_partner.py:80-82` extends `account`'s `_compute_credit_to_invoice` via `# EXTENDS 'account'` + `super()`).
- Files:
  - `addons/sale_credit_limit_warning/__manifest__.py` — `depends: ['sale', 'account']`
  - `addons/sale_credit_limit_warning/__init__.py` → imports `models`
  - `addons/sale_credit_limit_warning/models/__init__.py` → imports `sale_order`
  - `addons/sale_credit_limit_warning/models/sale_order.py` — `_inherit = 'sale.order'`:
    - New field `credit_limit_warning_level = fields.Selection([('warning', 'Warning'), ('danger', 'Danger')], compute='_compute_partner_credit_warning', store=False)` (no `'none'` option needed — a falsy/empty value naturally hides both banner divs).
    - Override `_compute_partner_credit_warning` (same method name as `addons/sale/models/sale_order.py:771`, calling `super()` first per the `# EXTENDS 'sale'` convention, then overwriting `order.partner_credit_warning` and setting `order.credit_limit_warning_level`) with the threshold/message logic below.
    - Must call `order.sudo()` when reading `partner_id.credit` / `credit_to_invoice` / `credit_limit`, matching the existing core comment at `sale_order.py:779` ("ensure access to `credit` & `credit_limit` fields") — these fields are restricted to `account.group_account_invoice,account.group_account_readonly` and a plain sales user would otherwise silently get blank/inaccessible values.
  - `addons/sale_credit_limit_warning/views/sale_order_views.xml` — inherits `sale.view_order_form`, xpaths the existing single alert div (`sale_order_views.xml:301-305`) to `replace` with two divs bound to the new `credit_limit_warning_level` field (see below).

**Threshold & message logic (concrete — resolves the task's "yellow at 80% / red over 100%" spec):** For each order (scoped to `state in ('draft', 'sent')`, matching the existing core gate — see Scope Boundaries):

```
outstanding      = partner.credit + partner.credit_to_invoice          # already-invoiced + confirmed-not-invoiced
this_order_amount = order.amount_total / order.currency_rate           # converted to company currency, same pattern as core sale_order.py:780
total_exposure   = outstanding + this_order_amount
limit            = partner.credit_limit

if not limit:
    level = False            # no banner — "no credit limit set"
elif total_exposure > limit:
    level = 'danger'         # red — over 100%
elif total_exposure >= 0.8 * limit:
    level = 'warning'        # yellow — 80%-100% inclusive
else:
    level = False            # no banner — well within limit
```

Message (both tiers use the same three-figure breakdown, only the lead sentence differs):
- Warning: `"{partner} is approaching its credit limit of {limit}. Current outstanding receivables: {outstanding}. This order would add: {this_order_amount}."`
- Danger: `"{partner} has exceeded its credit limit of {limit}. Current outstanding receivables: {outstanding}. This order would add: {this_order_amount}."`

All monetary figures formatted via `formatLang` in the company currency, matching the existing core message's formatting convention (`account_move.py:1869,1871`).

**Confidence: MEDIUM** on the exact boundary (80% inclusive → warning; >100% → danger) and exact copy — these are concrete decisions made here (no creative phase exists at Level 2), but are easy to tweak at build time without restructuring.

**Concrete invocation details:**
- **Location**: Sale Order form view, immediately under the `<header>` statusbar — same position as the existing core banner (`addons/sale/views/sale_order_views.xml:301-305`), which this feature's view inherits and replaces via xpath.
- **Element**: Two `<div class="alert ...">` banners (not a button/command — a passive computed banner):
  - `<div class="alert alert-warning" role="alert" invisible="credit_limit_warning_level != 'warning'"><field name="partner_credit_warning"/></div>`
  - `<div class="alert alert-danger" role="alert" invisible="credit_limit_warning_level != 'danger'"><field name="partner_credit_warning"/></div>`
- **Visibility**: Conditional — visible only when `credit_limit_warning_level` is `'warning'` or `'danger'`; both hidden (empty banner) when the field is falsy (no credit limit set, or well within limit).
- **Navigation**: None required — the banner appears automatically as soon as a Sale Order (state `draft` or `sent`) has a `partner_id` set; no click/menu path needed. From app entry: Sales app → Quotations → open/create an order → select a customer.
- **Confidence**: HIGH — exact location, field names, and xpath target are confirmed in the codebase (`addons/sale/views/sale_order_views.xml:301-305`).

### Success Criteria
- **User sees**: A yellow (`alert-warning`) or red (`alert-danger`) banner directly below the Sale Order form's status bar, containing the customer name, credit limit, current outstanding receivables, and this order's contribution — or no banner at all when not applicable.
- **Verifiable at**: The Sale Order form view (`sale.view_order_form`), on any order in `draft` or `sent` state with a partner set.
- **Data persisted**: None — `partner_credit_warning` and `credit_limit_warning_level` are non-stored computed fields (`store=False`), recomputed on the fly from `res.partner` credit fields and `order.amount_total`, exactly like the existing core field. Nothing new is written to the database.
- **Observable within**: Immediate — recomputes synchronously via the ORM's compute/onchange mechanism whenever `partner_id`, `company_id`, or order lines (hence `amount_total`) change, same as the existing core field's `@api.depends`.

### Acceptance Criteria

#### AC-ENTRY-1: Banner appears automatically without extra navigation
**Priority**: MUST
**Given** a user has opened or is creating a Sale Order (state `draft` or `sent`)
**When** they set a `partner_id` whose commercial partner has a `credit_limit` set and whose exposure is at or above 80% of that limit
**Then** the appropriate banner (yellow or red) is visible immediately below the status bar, with no additional click, menu, or navigation required to reveal it

#### AC-HAPPY-1: Yellow warning banner at 80%-100% of credit limit
**Priority**: MUST
**Given** a customer whose `credit_limit` is set and whose `outstanding + this_order_amount` falls between 80% (inclusive) and 100% (inclusive) of `credit_limit`
**When** the Sale Order form is viewed
**Then** the `alert-warning` (yellow) banner is shown, `credit_limit_warning_level == 'warning'`, and the message text states the credit limit, current outstanding receivables, and this order's added amount

#### AC-HAPPY-2: Red danger banner above 100% of credit limit
**Priority**: MUST
**Given** a customer whose `credit_limit` is set and whose `outstanding + this_order_amount` exceeds `credit_limit`
**When** the Sale Order form is viewed
**Then** the `alert-danger` (red) banner is shown, `credit_limit_warning_level == 'danger'`, and the message text states the credit limit, current outstanding receivables, and this order's added amount

#### AC-HAPPY-3: No banner when no limit set or well within limit
**Priority**: MUST
**Given** either (a) the customer's `credit_limit` is 0/unset, or (b) it is set but `outstanding + this_order_amount` is below 80% of `credit_limit`, or (c) `company_id.account_use_credit_limit` is disabled, or (d) the order is not in `draft`/`sent` state
**When** the Sale Order form is viewed
**Then** neither banner is visible; `partner_credit_warning == ''` and `credit_limit_warning_level` is falsy

#### AC-ERROR-1: Warning is not silently suppressed for users lacking accounting access rights
**Priority**: MUST
**Given** a Sales-only user who is NOT a member of `account.group_account_invoice` or `account.group_account_readonly` (so `partner.credit`, `credit_to_invoice`, and `credit_limit` are access-restricted fields for them)
**When** they view a Sale Order for a customer over/approaching the credit limit
**Then** the correct-tier banner still renders (compute logic reads these fields via `.sudo()`, matching the existing core pattern at `sale_order.py:779`) — the warning is never silently blank due to the viewing user's access rights

**AC-ASYNC**: Not applicable — the compute is synchronous (ORM `@api.depends` recompute on save/onchange), not an async operation; there is no intermediate/pending state to make observable.

### Scope Boundaries

- **In scope**:
  - A new addon `addons/sale_credit_limit_warning/` extending `sale.order` only.
  - Two-tier (yellow/red) banner on the Sale Order form, replacing the single-tier core banner's view placement.
  - Message breakdown showing credit limit, current outstanding receivables, and this order's contribution.
  - Reuse of all existing core fields/config (`account_use_credit_limit`, `credit_limit`, `credit`, `credit_to_invoice`) — no new settings UI, no new partner-facing fields.
- **Out of scope**:
  - Blocking/preventing order confirmation — this remains purely informational, matching the existing core `partner_credit_warning` behavior (never raises `UserError`).
  - Any change to `account.move` / customer invoices — core's invoice-side banner (`addons/account/views/account_move_views.xml:840-841`) is untouched; task description scopes this to the Sale Order form only.
  - Any change to `res.config.settings` or how `account_use_credit_limit` / `credit_limit` are configured.
  - Multi-company edge cases beyond what core's own `with_company(order.company_id)` already handles.
  - Extending the banner to order states other than `draft`/`sent` (confirmed/`sale` orders) — follows the existing core gate at `sale_order.py:775`.
- **Dependencies**: `sale` and `account` modules (both already present in this codebase; no new third-party dependency).
- **NFR implications**: None beyond existing core precedent — computed field is non-stored (`store=False`), recomputed per-record on demand; no additional query load beyond what core's own `partner_credit_warning` already performs (same `res.partner` fields, same order fields).

**Design decisions made** (resolved here since Level 2 skips the creative phase — flagged as MEDIUM confidence, easy to revisit at build time without restructuring):
1. 80% boundary is inclusive (`>= 0.8 * limit` → warning); the >100% boundary is exclusive on the danger side (`total_exposure > limit` → danger; `== limit` stays in the warning tier). Task description says "yellow at 80%, red over 100%" but doesn't specify inclusive/exclusive edges.
2. Banner state gated on `order.state in ('draft', 'sent')`, following the existing core gate rather than introducing a new one — task description doesn't specify order state scope.
3. `credit_limit_warning_level` has no explicit `'none'` selection value; a falsy value hides both banner divs. This avoids needing a third dummy option purely for view logic.
4. Both the yellow and red banners reuse the single `partner_credit_warning` text field (only the lead sentence differs internally); the view distinguishes color via two divs bound to `credit_limit_warning_level`, not via separate text fields.

## Test Strategy

### Approach
- **Emphasis**: Integration — matches systemPatterns.md's noted preference for `TransactionCase` integration-style tests over isolated unit tests, since the logic is expressed through ORM computed fields.
- **Target test count**: 9 across both phases.

### File Organization
- **New test files**: `addons/sale_credit_limit_warning/tests/test_sale_order_credit_warning.py` — all compute/threshold/view-gating behavior for this feature.
- **Extend existing**: None — this is a new addon with no prior tests to extend.

### What NOT to Test
- Core `_build_credit_warning_message` formatting internals (currency rounding, `formatLang` behavior) — already covered by Odoo core's own test suite (`addons/account/tests/`); out of scope to re-verify upstream behavior.
- View rendering pixel/CSS correctness — Odoo's QWeb/OWL rendering pipeline is framework-level; verified instead by asserting the correct `credit_limit_warning_level` value drives the correct `invisible` condition (a `TransactionCase` field-value assertion, not a browser test).

### Per-Phase Test Guidance
- Phase 1: 7 tests — `_compute_partner_credit_warning` override: (1) no `credit_limit` set → no banner, (2) exposure well within limit (<80%) → no banner, (3) exposure exactly at 80% → warning tier, (4) exposure between 80-100% → warning tier, (5) exposure exactly at 100% → still warning (not danger), (6) exposure over 100% → danger tier, (7) `account_use_credit_limit` disabled on company → no banner even when over limit.
- Phase 2: 2 tests — (1) order not in `draft`/`sent` state (e.g. `sale`) → no banner regardless of exposure, (2) user without `account.group_account_invoice`/`account.group_account_readonly` still sees the correct-tier banner (verifies the `.sudo()` read).

## Implementation Roadmap

### New Source Files (pin path + extension)
<!--
  Pin EVERY new source file (incl. hooks/utils/types — not just components) with
  its explicit path AND extension, resolved from systemPatterns.md → Code
  Organization Patterns / techContext.md → Source extensions. This removes the
  extension from being an ad-hoc build-time guess. Use "extend" for files modified.
-->
- [ ] `addons/sale_credit_limit_warning/__manifest__.py` — module manifest, `depends: ['sale', 'account']`
- [ ] `addons/sale_credit_limit_warning/__init__.py` — imports `models`
- [ ] `addons/sale_credit_limit_warning/models/__init__.py` — imports `sale_order`
- [ ] `addons/sale_credit_limit_warning/models/sale_order.py` — `_inherit = 'sale.order'`: new `credit_limit_warning_level` Selection field + `_compute_partner_credit_warning` override (threshold/message logic, `.sudo()` reads)
- [ ] `addons/sale_credit_limit_warning/views/sale_order_views.xml` — inherits `sale.view_order_form`, xpaths the existing single alert `<div>` to two tier-gated divs
- [ ] `addons/sale_credit_limit_warning/tests/__init__.py` — imports test module
- [ ] `addons/sale_credit_limit_warning/tests/test_sale_order_credit_warning.py` — `TransactionCase` tests per Test Strategy above

### Phases
- [x] Phase 1: Module scaffold + compute logic — manifest, `__init__` files, `models/sale_order.py` (field + compute override), 8 compute-logic tests (all pass with `odoo-bin --test-enable -i sale_credit_limit_warning`)
- [x] Phase 2: View integration + access-rights coverage — `views/sale_order_views.xml` xpath replacement, remaining 2 tests (order-state gate, non-accounting-user access), 10/10 module tests passing
- [x] Phase 3: E2E spec implementation (post-UAT) — extended `tests/test_sale_order_credit_warning.py` with the 3 `TransactionCase` tests from `memory-bank/uat/spec-customer-credit-limit-warning-e2e.md` § Test Cases to Implement (warning-tier via UI-equivalent fixture values, danger-tier via UI-equivalent fixture values, explicit-zero-limit no-banner control case); the spec's 4th case (mobile viewport) is explicitly out of scope for a Python `TransactionCase` and was not implemented; 13/13 module tests passing

## Creative Phases

- [ ] Not required — Level 2, spec approved with all fields at HIGH confidence except two explicitly-resolved MEDIUM-confidence design decisions (boundary inclusivity, order-state gate) documented under Scope Boundaries.

---

## Execution State

**Build Status**: COMPLETE
**Current Phase**: Phase 3: E2E spec implementation (post-UAT) — COMPLETE (all phases done)
**Phase Number**: 3 of 3
**Is Multi-Phase**: YES
**Build Started**: 2026-08-28
**Last Completed**: Phase 3 committed and pushed to feature/customer-credit-limit-warning — 13/13 module tests passing, lint clean on all Phase 3 additions, code review APPROVED, no memory-bank doc changes needed.
**Can Resume**: NO
**Resume From**: N/A — all 3 implementation phases complete. Next: /bmb:reflect customer-credit-limit-warning, then /bmb:archive

### Current Build Step
**Step**: Step 11 - Phase Git Completion
**Status**: COMPLETE

### Active Sub-Agents
(none)

### Completed Steps
- UAT Orchestrator — installed `sale_credit_limit_warning` into the dev DB (was uninstalled despite BUILD_COMPLETE status), walked happy+mobile sections as Administrator (superset of accountant persona), confirmed AC-ENTRY-1/AC-HAPPY-1/AC-HAPPY-2/AC-HAPPY-3a via DOM `role="alert"` class assertions at desktop and 375x667 viewports. One Recommended finding: journey doc's "unset/0" precondition needs revision (`ir.default` fallback makes credit_limit=1.0 for any partner without an explicit override); provisioned Acme Corporation (id 10) with explicit credit_limit=0 as the durable control-case fixture.
- Spec Writer Agent (Sonnet) — Specification section, taxonomy lint CLEAN
- Human review — Approved as-is
- Implementation plan — Test Strategy + Implementation Roadmap (2 phases, 9 tests)
- Phase 1 TDD Agent — new addon `sale_credit_limit_warning` scaffolded; `_compute_partner_credit_warning` override (80% warning / >100% danger tiers, 3-part message); 7 compute-logic tests (RED→GREEN)
- Phase 1 Integration Verification (bmb:build-verifier-agent + direct execution) — module's own suite: 7/7 passing (later 8/8 after fix). Full `-i sale_credit_limit_warning` dependency-suite run surfaced 2 pre-existing `addons/sale/tests/test_credit_limit.py` failures (`test_credit_limit_access`, `test_credit_limit_multicurrency`) confirmed as an intended, documented consequence of this feature's approved spec (Design Decision #1: 80% inclusive warning tier + redesigned 3-part message supersede core's old >100%-only single-message banner) — non-blocking, not a code defect.
- Phase 1 Code Review — CHANGES_REQUESTED: one blocking issue (credit fields read from `order.partner_id` instead of rolled-up `order.partner_id.commercial_partner_id`, silently under-reporting exposure for child-contact orders, per core's own `test_commercial_partner_credit` pattern)
- Phase 1 Fix (TDD Agent) — corrected to `order.partner_id.commercial_partner_id.sudo()`; added `test_commercial_partner_credit_limit_warning` (8th test); applied non-blocking suggestions (`_CREDIT_WARNING_THRESHOLD_RATIO` constant, field `help=`). Verified via real RED (1 failed for the right reason) → GREEN (0 failed of 8 tests) execution in the live `odoo-odoo-1` container.
- Documentation Agent — reviewed; no memory-bank doc changes needed (routine application of the already-documented "Extend, don't modify" pattern, no new tech/dependency)
- Phase 2 TDD Agent — new `views/sale_order_views.xml` (inherits `sale.view_order_form`, xpath-replaces the core single-tier banner div with two tier-gated divs on `credit_limit_warning_level`); `__manifest__.py` `data` updated; 2 new tests added (`test_confirmed_order_no_banner`, `test_non_accounting_user_still_sees_banner`) — RED confirmed via manifest-before-view-file install failure, GREEN via 10/10 module tests passing
- Phase 2 Integration Verification (bmb:build-verifier-agent) — module's own suite: 10/10 passing; dependency suite: no new regressions beyond Phase 1's already-documented pre-existing core failures — PASS
- Phase 2 Code Review — APPROVED, 0 blocking issues (1 non-blocking hardening suggestion: anchor the view xpath on the child `<field>` element instead of the exact `invisible` string, for extra resilience to cosmetic core changes — not applied, optional)
- Phase 2 Documentation Agent — reviewed; no memory-bank doc changes needed (XML view inheritance is an already-documented standard pattern); added one clarifying inline XML comment to `views/sale_order_views.xml`
- Phase 3 TDD Agent — extended `tests/test_sale_order_credit_warning.py` with 3 new tests codifying the UAT E2E spec (`memory-bank/uat/spec-customer-credit-limit-warning-e2e.md`): `test_e2e_warning_tier_via_ui_equivalent_values`, `test_e2e_danger_tier_via_ui_equivalent_values`, `test_e2e_no_banner_explicit_zero_limit`; widened `_create_order(amount_total, partner=None)` helper (behavior-preserving for all 10 prior call sites); 13/13 passing on first real execution (spec case 4, mobile viewport, deliberately not implemented — out of scope for `TransactionCase`)
- Phase 3 Integration Verification (bmb:build-verifier-agent) — tests PASS 13/13; build (module install) PASS; lint FAIL — 9 new E501 line-too-long violations in the added test methods (13 other violations pre-existing from Phases 1-2, out of scope)
- Phase 3 Lint Fix (orchestrator, mechanical) — rewrapped the 9 offending lines to fit the 79-char flake8 limit; re-ran the module suite directly (13/13 still passing) and flake8 on this phase's diff (0 new violations; only the 2 pre-existing Phase-1 long lines at 57/111 remain, unrelated to this phase)
- Phase 3 Code Review — APPROVED, 0 blocking issues (1 non-blocking note affirming the zero-limit test doesn't over-specify; 1 optional dedup suggestion for the warning/danger tests' shared exposure-booking setup, not applied — consistent with existing file style)
- Phase 3 Documentation Agent — reviewed; no memory-bank doc changes needed (test-only phase, no new tech/pattern/capability; inline comments already adequate)

### Guard & Recovery Log
- Phase 1: Step 7 integration verification via `bmb:build-verifier-agent` initially FAILed with "invalid module names, ignored: sale_credit_limit_warning" — root-caused to a stale `odoo-odoo` Docker image (built 2026-08-18, before this module existed) being used by `docker compose run`, which does not auto-rebuild. Recovery: found the already-running `odoo-odoo-1` container had the current module content live-synced (via `docker compose watch` / prior `docker cp`); re-ran tests directly against that container instead of rebuilding the (very slow, ~420MB context, sandbox-constrained) image. Module suite passed 7/7 (later 8/8 post-fix) via real execution.
- Phase 1: Code-review blocking finding (commercial_partner_id rollup) → Recovery Ladder not needed (not an artifact-loss case) — routed back to TDD Agent for a standard fix-and-reverify cycle per Steps 3→7→8. Fixed, tested (RED→GREEN, real execution), re-confirmed clean.
- Phase 2: No guard failures. `docker compose watch` was found not actually running (plain `docker compose up` only); TDD/verifier agents used `docker cp` to push changed files into the running `odoo-odoo-1` container before each test run instead.
- Phase 3: Step 7 guard FAIL (lint: 9 new E501 violations in the added test methods) → recovery: mechanical line-rewrap fix (no ladder needed — not an artifact-loss case), re-verified real test execution (13/13) + flake8 (0 new violations) directly → PASS. Root cause: TDD agent's assertion/docstring lines exceeded the 79-char flake8 limit configured in `setup.cfg`; no memory-bank guidance gap to fix (the limit is discoverable in `setup.cfg`, agent simply didn't check it before writing).
