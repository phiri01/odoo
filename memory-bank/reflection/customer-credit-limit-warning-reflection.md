# Reflection: customer-credit-limit-warning - Customer Credit Limit Warning

**Date**: 2026-08-28
**Task Complexity**: Level 2
**Total Phases**: 3 (2 planned + 1 post-UAT E2E-spec phase)
**Duration**: 2026-08-28 (roadmap → plan → build x3 → UAT → build → reflect, same day)

## Executive Summary

The task added a two-tier (yellow/red) credit-limit banner to the Sale Order form by extending Odoo core's existing `sale.order._compute_partner_credit_warning` rather than building parallel logic — a deliberately conservative, well-evidenced architectural choice (core already ships ~80% of the feature; the new addon fills the gap: an 80% "approaching" tier, a red >100% tier, and a three-part message breakdown). All four MUST-priority acceptance criteria (AC-ENTRY-1, AC-HAPPY-1/2/3, AC-ERROR-1) were verified either by `TransactionCase` tests or by a live browser UAT walk, and the implementation landed with 13/13 module tests passing and zero blocking code-review findings across all three phases.

The build was not frictionless, but every friction point had a clean, well-documented recovery: a genuine correctness bug (reading credit fields off `order.partner_id` instead of the rolled-up `order.partner_id.commercial_partner_id`) was caught by code review before merge, not by a customer; a stale Docker test image was worked around by testing against the live-synced container instead of burning time on a slow rebuild; and a UAT-environment surprise (a global `ir.default` fallback silently sets `credit_limit=1.0` for every partner) was diagnosed and turned into a durable fixture (Acme Corporation, id 10) rather than a blocked UAT run. The one real process failure — a `gh` credential only having read access to the target GitHub remote — was outside the agent's control and was correctly escalated to the human rather than worked around silently.

Overall this is a strong Level 2 execution: right-sized architecture (extend, don't duplicate), rigorous TDD with real RED→GREEN verification (not simulated), and UAT that actually changed the test suite for the better (Phase 3 exists only because UAT surfaced a gap). The main ecosystem-level gap is observability into the build itself — no task-scoped session logs existed to analyze, which is a real cost when trying to reflect on *how* the sub-agents worked, not just what they produced.

---

## What Went Well

1. **"Extend, don't modify" architecture paid off exactly as designed.** The new addon depends on `sale`/`account` and overrides `_compute_partner_credit_warning` via `super()` rather than monkey-patching or duplicating core's `_build_credit_warning_message` logic. This kept the diff small (one model file, one view xpath, tests) and meant the only real complexity was the three-tier threshold math and the view's two-div xpath replacement — not re-deriving `credit`/`credit_to_invoice` rollups core already computes correctly.
2. **Code review caught a real correctness bug before it shipped.** Phase 1's review flagged that credit fields were read from `order.partner_id` instead of `order.partner_id.commercial_partner_id`, which would have silently under-reported exposure for any order placed under a child contact (a common B2B pattern — invoicing address vs. commercial entity). This is exactly the kind of bug that is easy to write and easy to miss in manual testing (most demo/test partners *are* their own commercial partner), and the review process caught it on the first pass.
3. **Real RED→GREEN verification, not simulated.** The Phase 1 fix-and-reverify cycle ran an actual failing test against the live `odoo-odoo-1` container before the fix, then a real passing run after — not just "trust the diff." This matters in a project (Odoo core) where field access rights and `sudo()` boundaries are easy to get subtly wrong.
4. **UAT produced a concrete, correctly-scoped test-writing follow-up.** Phase 3 exists because UAT's "Next Step" and the E2E spec explicitly identified 3 server-testable cases and 1 out-of-scope case (mobile viewport) — the TDD agent implemented exactly the 3 and correctly declined the 4th rather than forcing a browser-tour harness that doesn't exist in this repo.
5. **The `ir.default` UAT gotcha was diagnosed and fixed at the fixture level, not papered over.** Discovering that no demo partner actually has `credit_limit` unset (a global `ir.default` sets 1.0) could have produced a false "no banner" pass on the wrong partner. Instead the UAT walker traced the root cause and provisioned a durable, explicit fixture (Acme Corporation, credit_limit=0.0) for the control case — this is exactly the kind of finding a browser-based UAT catches that pure unit tests would not.
5. **Escalation discipline on the push failure.** When `gh`'s active account turned out to be read-only on the intended remote, the agent did not attempt a workaround that could mask a credentials/environment problem (e.g., silently trying other remotes) — it escalated to the human, who made the call to push to a fork remote instead.

## Challenges Encountered

1. **`order.partner_id` vs. `order.partner_id.commercial_partner_id` (Phase 1)** — Resolved via code review + TDD fix-and-reverify cycle, with a new regression test (`test_commercial_partner_credit_limit_warning`) added specifically to lock in the fix.
2. **Stale Docker image breaking the build-verifier's `docker compose run` (Phase 1)** — The verifier's image predated the new module and reported "invalid module names, ignored." Resolved by running tests directly against the already-running, live-synced `odoo-odoo-1` container instead of rebuilding a slow, sandbox-constrained image. This is a workaround, not a fix — the underlying image-staleness problem was not addressed and will recur on the next task unless the image build/sync mechanism itself is fixed.
3. **`ir.default` fallback masking the "no credit limit set" control case in the dev DB (UAT)** — No demo partner had a truly unset `credit_limit`; a global default silently applies 1.0 to everyone. Resolved by provisioning an explicit fixture (Acme Corporation, id 10, `credit_limit=0.0`) and updating the journey doc's precondition language — but this is an environment characteristic that will bite the *next* task's UAT run too if it assumes "unset" fields behave as unset in this dev DB.
4. **Module found uninstalled in the dev DB despite `BUILD_COMPLETE` status (UAT pre-flight)** — Build completing does not imply the dev DB has the module installed; UAT had to `-i sale_credit_limit_warning` before it could walk anything. Resolved this run, but indicates install-state and build-status can silently drift.
5. **Lint FAIL on Phase 3 (9 new E501 violations)** — Mechanical, fixed by rewrapping lines; root cause was simply not checking `setup.cfg`'s 79-char limit before writing test code, not a memory-bank guidance gap.
6. **`gh` push 403 on the intended remote (Phase 3 archive step)** — Environment/credentials issue (active `gh` account has read-only access to `DaKaZ/odoo`), unrelated to code quality. Escalated to the human, who redirected the push to `phiri01-fork`.

## Lessons Learned

- A correctness bug tied to Odoo's `commercial_partner_id` pattern is not obvious from surface-level testing because most seeded/demo data collapses the distinction (partner == its own commercial partner). Any feature reading partner-level financial fields (`credit`, `credit_limit`, `credit_to_invoice`, similar) needs an explicit child-contact test case as a matter of course, not as a review afterthought.
- This dev database's `ir.default` on `res.partner.credit_limit` (defaulting to 1.0) means "unset" is not actually achievable by omission — any future feature or UAT journey that needs a true zero/unset credit limit must provision it explicitly and durably (as Acme Corporation, id 10, now is) rather than relying on any existing demo partner.
- Build-verifier infra (the Docker image backing `docker compose run`) can silently drift out of sync with a live-synced dev container; when the verifier reports "invalid module names, ignored" for a module that clearly exists on disk, that is a strong signal to check image freshness before assuming the module itself is broken.

## Action Items

- [ ] Consider fixing (or automating a rebuild-check for) the `odoo-odoo` Docker image used by `bmb:build-verifier-agent` so it doesn't silently run stale — this will recur on every future task until addressed.
- [ ] Consider documenting the `ir.default credit_limit=1.0` dev-DB quirk (and the Acme Corporation id-10 fixture) somewhere more durable than this reflection — e.g., `techContext.md` or a UAT fixtures note — so the next feature touching partner credit fields doesn't rediscover it from scratch.
- [ ] Verify/resolve the `gh` account's access scope on `DaKaZ/odoo` before the next task needs to push there, to avoid repeating the escalation.
- [ ] Apply the non-blocking Phase 2 hardening suggestion (anchor the view xpath on the child `<field>` element rather than the exact `invisible=` string) opportunistically next time this view file is touched — low cost, meaningfully more resilient to cosmetic core changes.

---

## Claude Code Ecosystem Observations

### What Worked Well

- **Command sequencing matched complexity.** Level 2's `roadmap → plan → build(x3) → uat → build → reflect` flow worked exactly as designed for a task whose scope grew mid-stream (UAT surfacing a legitimate need for a 3rd build phase). The workflow absorbed that without requiring a re-plan or re-classification.
- **Code review as a real gate, not a rubber stamp.** Across 3 phases, review caught one genuine blocking bug (Phase 1) and offered two reasonable, correctly-deferred non-blocking suggestions (Phases 2 and 3) — signal that the reviewer is discriminating between "must fix" and "nice to have" rather than treating everything as blocking or nothing as blocking.
- **UAT-to-build handoff via generated E2E spec worked as intended.** The `/bmb:uat` PASS output (`memory-bank/uat/spec-customer-credit-limit-warning-e2e.md`) gave Phase 3's TDD agent a concrete, scoped list of cases to implement, including one explicitly-out-of-scope case it correctly did not force into the wrong test framework.
- **Recovery Ladder correctly not invoked for non-artifact-loss issues.** Both the Phase 1 code-review fix and the Phase 3 lint fix were routed through a standard fix-and-reverify cycle rather than escalating to a heavier recovery mechanism — the Guard & Recovery Log's own judgment that these weren't "artifact-loss" cases appears sound in hindsight.

### Friction Points

1. **No task-scoped session logs (`.agent-logs/claude/by-task/customer-credit-limit-warning/` absent).** This materially degraded this reflection's Build Session Analysis — tool-utilization counts, sub-agent invocation counts, and error-recovery timing had to be reconstructed from the task file's narrative Execution State and git log rather than measured from logs. The date-based fallback directory didn't even align with when most of the work happened (Phase 3/UAT landed 2026-08-28; the fallback directory was dated 2026-08-27). This is exactly the gap the task-file note "Session logs not task-indexed. Run /bmb:init to upgrade." anticipates — this project should run that upgrade.
2. **Stale Docker image is a recurring, unaddressed infra tax.** The Phase 1 workaround (test against the live container instead of rebuilding) was reasonable in the moment but doesn't fix the underlying problem — the same staleness will very likely reoccur on the next task that touches a new/changed module, each time costing the same diagnosis effort.
3. **Build-status vs. install-status drift.** `BUILD_COMPLETE` did not imply the module was actually installed in the dev DB that UAT walks against. UAT's pre-flight check caught this, but it's a gap in the "definition of complete" between `/bmb:build` and `/bmb:uat` that could silently produce a false UAT PASS if the pre-flight check were ever skipped or weaker.
4. **Environment/credentials issue surfaced only at the very last step.** The `gh` read-only-access problem on the push target wasn't discoverable until Phase 3's completion tried to push — a cheap `gh auth status` / remote-permission check earlier in the workflow (e.g., at `/bmb:plan` or first `/bmb:build`) could have surfaced this hours earlier instead of at the finish line.

### Suggestions for Improvement

**High Priority**:
1. Populate/enable by-task session-log indexing for this project (run whatever `/bmb:init` upgrade step establishes `.agent-logs/claude/by-task/<slug>/`) — build-session analysis is currently unusable for reflections on tasks predating that indexing, which undermines exactly the ecosystem-effectiveness half of this document's mandate.
2. Add a lightweight preflight (at `/bmb:build` Phase 1 start, or `/bmb:doctor`) that checks the target push remote's write access via `gh api repos/<owner>/<repo> --jq .permissions` (or equivalent), surfacing a credentials problem before the final phase instead of after 3 phases of work are done.

**Medium Priority**:
1. Investigate whether `bmb:build-verifier-agent`'s `docker compose run` path can auto-detect staleness (e.g., compare image build timestamp against `git log -1 --format=%cI` for the addon under test) and either auto-rebuild or fall back to the live container automatically instead of failing with a confusing "invalid module names, ignored" message that requires manual root-causing each time.
2. Have `/bmb:uat`'s pre-flight check (or `/bmb:build`'s Step 11 completion) explicitly verify module install-state in the target dev DB matches `BUILD_COMPLETE`, rather than relying on UAT to discover the mismatch reactively.

**Low Priority / Nice to Have**:
1. Surface known dev-DB data quirks (like the `ir.default credit_limit=1.0` global default) in a durable, discoverable location (e.g., a "UAT Fixtures & Gotchas" subsection of `uat-config.md`) so future tasks touching the same fields don't re-derive the same discovery from scratch.

**Note**: These are suggestions only. Not implemented as part of this reflection.

---

## Extractable Learnings

1. **testing-patterns** (`res.partner` financial/credit fields, `sale.order`, `account.move`): When a feature reads partner-level financial fields (`credit`, `credit_limit`, `credit_to_invoice`), always roll up through `commercial_partner_id` and add an explicit child-contact test case — most seeded/demo data collapses partner and commercial-partner, hiding this bug class from casual testing.
2. **uat-fixtures** (`memory-bank/uat/`, journey docs referencing "unset"/"0" field preconditions): Before writing a UAT journey precondition that assumes a field is unset/zero by default, verify no `ir.default` (or equivalent project-level default) overrides it in the target dev DB — provision an explicit, durable fixture record instead of relying on any existing demo data to be truly unset.

---

## Conclusion

This was a well-executed Level 2 task: the architectural decision to extend rather than duplicate Odoo core's existing credit-warning machinery was sound and kept the implementation tightly scoped, the TDD/code-review loop caught a real bug before merge, and UAT did what UAT is supposed to do — surface an environment gotcha and generate a concrete, correctly-scoped follow-up test phase rather than a vague "looks fine." The friction that did occur (stale Docker image, `ir.default` surprise, uninstalled module, read-only `gh` remote) was all handled competently in the moment, but three of the four are recurring infra/environment issues rather than one-off task quirks, and are worth fixing at the ecosystem level rather than re-diagnosing on every future task. The missing task-scoped session logs are a genuine gap in this reflection's evidence base and should be closed before the next reflection is written.

**Overall Task Success**: ✅ Success

**Overall Workflow Effectiveness**: ⚠️ Moderately Effective (solid command/agent workflow; recurring infra friction — Docker image staleness, session-log indexing gap, no push-permission preflight — kept it from "Highly Effective")

**Recommendation**: Ready to archive.
