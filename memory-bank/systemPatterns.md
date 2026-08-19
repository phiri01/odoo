# System Patterns

## Guiding Principles

| Principle | Description |
|-----------|--------------|
| Extend, don't modify | Use `_inherit`/`_inherits` and manifest `depends` rather than editing core or other modules' files directly |
| Data-driven configuration | Security, demo data, and views are declarative XML/CSV, not imperative code |
| Module isolation | Each addon is independently installable; the dependency graph is resolved by `odoo/modules/graph.py` |
| CLA / contribution requirements | Documented in `CONTRIBUTING.md` and `doc/cla/` |

## Directory Structure

| Dir | Purpose |
|---|---|
| `odoo/` | Core framework: ORM, HTTP layer, module loader, CLI, services. Not an addon itself. |
| `addons/` | ~621 addon modules (business apps + framework addons like `base`, `web`, `website`). Each is self-contained and declares dependencies. |
| `debian/` | Packaging metadata for building `.deb` distributions. |
| `docker/` | This fork's containerized dev setup (`odoo.conf`, mounted into the container). |
| `doc/` | Minimal; currently just `cla/` (Contributor License Agreement docs). |
| `setup/` | Install/package scaffolding (`setup.py` helpers, debian control files, RPM specs). |
| root | `odoo-bin` (entry script), `Dockerfile`, `docker-compose.yml`, `requirements.txt`. |

## Module (Addon) Structure

Standard Odoo convention, present across all 621 addons:

- `__manifest__.py` — metadata dict (`name`, `version`, `depends`, `data`, `assets`, etc.)
- `models/` — ORM model definitions (`models.Model`/`TransientModel` subclasses)
- `views/` — XML view/action/menu definitions
- `controllers/` — HTTP route handlers (`@http.route`)
- `security/` — `ir.model.access.csv` + `ir_rules.xml` (record rules)
- `static/src/` — JS (OWL components), SCSS, XML templates for frontend
- `data/`, `report/`, `wizard/`, `i18n/` — demo/config data, QWeb reports, transient wizards, translations
- `tests/` — module-specific tests

## Entry Points & Core Layers

- **`odoo-bin`** — thin launcher invoking `odoo.cli`.
- **`odoo/cli/`** — subcommands: `server.py` (main daemon), `shell.py`, `scaffold.py`, `db.py`, `deploy.py`, `populate.py`, `neutralize.py`, `upgrade_code.py`.
- **`odoo/service/`** — server internals: `server.py` (workers/threads), `model.py`, `db.py`, `security.py` (RPC dispatch layer).
- **`odoo/modules/`** — addon discovery/loading: `loading.py`, `graph.py` (dependency graph), `registry.py` (model registry cache), `migration.py`.
- **ORM**: `odoo/models.py` + `odoo/fields.py` — `Model`/`TransientModel`/`AbstractModel`, new-API decorators (`@api.depends`, `@api.constrains`, `@api.model`, `@api.onchange`), recordsets.
- **Web framework**: `odoo/http.py` — WSGI app, `Request`/`Response`, `@http.route` controller routing, session handling.

## Code Organization Patterns

- Primary backend language: **Python** (3.12 per Dockerfile), heavy use of the "new API" recordset/decorator style.
- Frontend: **OWL** (Odoo Web Library, `@odoo/owl`) reactive component framework used throughout `addons/web/static/src/` (core services, views, webclient) and `addons/website`; templates in QWeb XML, styling in SCSS.
- Business logic modules extend/inherit core models via `_inherit`, keeping composition additive rather than modifying core files.
- Security is co-located with each module (`security/ir.model.access.csv`, `ir_rules.xml`) rather than centralized.

| Directory / role | Dominant extension |
|---|---|
| `odoo/`, `addons/*/models`, `addons/*/controllers`, `addons/*/wizard` | `.py` |
| `addons/*/views`, `addons/*/data`, `addons/*/report` | `.xml` |
| `addons/*/security` | `.csv` / `.xml` |
| `addons/web/static/src`, `addons/website/static/src` | `.js` (OWL components) + `.xml` (QWeb templates) + `.scss` |
| `addons/*/i18n` | `.po` |

New addon modules follow the module-dir shape above (not flat files) — a new module gets its own directory with `__manifest__.py` plus the relevant subset of `models/`, `views/`, `security/`, etc.

## Testing Patterns

- `odoo/tests/` provides the test framework: `common.py` (`TransactionCase`, `HttpCase` base classes), `case.py`, `form.py` (Form emulation), `tag_selector.py`, `loader.py`, `suite.py`.
- Per-module tests live in `addons/<module>/tests/test_*.py`, registered via `tests/__init__.py`.
- Typical pattern: subclass `TransactionCase`/`HttpCase`, use `@tagged(...)` decorators for filtering, run via `odoo-bin -i <module> --test-enable --stop-after-init` or `--test-tags`.
- Naming: `test_<feature>.py`, e.g. `test_sale_order_cancel.py`, `test_access_rights.py`, `test_controllers.py` (HTTP-level tests).
- Test-to-source ratio and unit/integration emphasis vary widely by module; Odoo core favors integration-style `TransactionCase` tests over isolated unit tests, since most logic is expressed through the ORM/recordset layer.

## Fork-Specific Notes (`banyan` branch)

- Remote is `DaKaZ/odoo` (a fork), currently on branch `banyan` with a single custom commit: **"local docker setup"** (8a9ce028).
- Adds `Dockerfile`, `docker-compose.yml`, and `docker/odoo.conf` — **not present in stock Odoo** — providing a local containerized dev environment (Python 3.12-slim image, Postgres 16, live-reload via `dev_mode=reload` and `docker compose watch` sync/restart rules for `addons/` and `odoo/`).
- No other structural deviation from vanilla Odoo was found — core (`odoo/`) and addons (`addons/`) are stock Odoo 18.0 source.
