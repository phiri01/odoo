# Project Configuration

## Banyan Memory Bank

This section is auto-managed by `/bmb:init`. Do not edit manually.

- **Banyan Version**: 2.2.1
- **Initialized**: 2026-08-19
- **Last Updated**: 2026-08-19

## Git & Branching (v2)

Read by every banyan command for branch routing and protected-branch enforcement.

```yaml
metadata_branch: banyan
protected_branches: []
pr_target: banyan
sync_automation: none
archive_strategy: local-merge
worktree_root: ~/banyan-wt/odoo/
```

Solo/personal fork with a single branch (`banyan` — the fork has no `main`/`master` at all, only `banyan` locally and on `origin`). No dev/main promotion; no protection, so banyan writes commit directly rather than routing through a PR. Completed tasks are merged locally.

## Agent Backends

```yaml
backends:
  plan:                  anthropic
  tdd:                   anthropic
  code-review:           anthropic
  creative-architecture: anthropic
  creative-uiux:         anthropic
  creative-algorithm:    anthropic
  creative-user-journey: anthropic
  creative-critique:     codex
  auto-final-review:     anthropic
  availability:          auto
```

Codex companion not detected on this machine — every seam runs on Anthropic (default). `creative-critique` will self-enable if Codex is installed later.

## Team

```yaml
team:
  # <git-email>: <friendly first name>
  # Crowd-sourced and self-populating — no upfront roster collection at init.
```

## UAT

Not configured. Run `/bmb:uat-init` if browser-based UAT is needed later (this repo currently shows no obvious web/UI surface signal for the fork itself — Odoo's own web client is part of stock addons, not this fork's product surface).

## Notes

- This is upstream Odoo 18.0 plus a single custom commit ("local docker setup") adding a Dockerized local dev environment.
- No CI/CD is configured yet.
- `docker/odoo.conf` contains hardcoded dev-only credentials (`odoo`/`odoo`, `admin_passwd=admin`) — never reuse this file outside local dev.
