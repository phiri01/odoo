# UAT Configuration

This file is created and maintained by `/bmb:uat-init`. It carries project-specific UAT infrastructure (base URLs, persona credentials, auth strategy, viewport presets, isolation strategy).

**Companion file**: `memory-bank/projectConfig.md` `## UAT` section carries project-wide *ergonomic* defaults (default sections, artifact git policy). Keep secrets/infra here; keep ergonomics there.

---

**Status**: Configured
**Last Updated**: 2026-08-27

## Environments

| Name | Base URL              | Default |
|------|-----------------------|---------|
| dev  | http://localhost:8069 | yes     |

> `/bmb:uat` refuses to run against environments where `name == "prod"`. There is no override flag — production UAT must be intentionally invoked via a separate (future) command.

## Auth

- **Strategy**: token+fallback
  - `token` — inject localStorage/cookies from `.auth/<persona>.json`, hard-reload. Fastest.
  - `login` — drive the IDP UI. Slower but resilient to expired tokens.
  - `token+fallback` (default) — try token first; on auth failure or 401, fall back to `login` and cache fresh tokens back to `.auth/<persona>.json`.
- **Credential vault**: `.auth/` (must be in `.gitignore`)
- **Token file pattern**: `.auth/<persona>.json`
- **Login selectors** (only when strategy includes `login`):
  - username: `input[name="login"]`
  - password: `input[name="password"]`
  - submit:   `button[type="submit"]`
  - post-login wait: url matches `/odoo`

## Persona Map

Each row maps a persona role discovered in `productBrief.md` → a test account → an auth reference (token path or env var name for password).

| Role          | Test Account                | Auth Reference    |
|---------------|------------------------------|--------------------|
| sales_user    | rphilyaw@banyansoftware.com | $TEST_SALES_PW     |
| accountant    | rphilyaw@banyansoftware.com | $TEST_ACCOUNTANT_PW |
| administrator | rphilyaw@banyansoftware.com | $TEST_ADMIN_PW     |

## Viewports

| Name    | Width | Height | Default For      |
|---------|-------|--------|-------------------|
| desktop | 1280  | 720    | all non-mobile    |
| mobile  | 375   | 667    | mobile section    |

## Execution

- **max_parallel_tabs**: 4
- **isolation_strategy**: auto          # auto | same-persona-only | incognito
  - `auto` (default) — probes incognito support at run start; falls back to `same-persona-only` if unavailable. Today this always falls back; the Claude-in-Chrome MCP does not yet expose incognito tab creation.
  - `same-persona-only` — explicit conservative. Walkers with the same resolved persona run in parallel; walkers with different personas serialize.
  - `incognito` — reserved for a future Claude-in-Chrome release. Selecting today errors at the phase gate.
- **auth_cookies_to_clear**:            # cookie names to scrub between persona groups
    # (none configured — relies on localStorage.clear() + logout_url navigation)
- **logout_url**: /web/session/logout
- **screenshot_retention**: keep only findings-related (drop screenshots not referenced in findings)
- **default_timeout_ms**: 15000
- **ux_pattern_check**: enabled

## Notes

- The credential vault directory MUST be added to `.gitignore`. UAT artifacts may include screenshots that contain test-account PII; configure `artifact_git_policy` in `projectConfig.md` accordingly.
- `--persona-override` flags warn when the supplied address does not match the project's documented test-account pattern. Update the Persona Map rather than relying on overrides for repeated runs.
- All three personas currently share one test-account email (`rphilyaw@banyansoftware.com`) distinguished only by password/auth-reference and by which Odoo security groups that account belongs to at runtime (Sales-only vs. Accounting vs. Administrator). Ensure the underlying Odoo user's group membership is switched appropriately before each persona's walker run, or provision distinct Odoo users per role if walkers ever run in parallel across personas.
