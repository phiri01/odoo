# Tech Context

## Language & Version

- **Python** 3.10–3.14 supported (version-conditioned deps in `requirements.txt`); Docker image pins **Python 3.12** (`python:3.12-slim`).
- Odoo release: **18.0** (`odoo/release.py`).
- No `.python-version` file present.

## Frameworks

- **Odoo ORM/Framework** (`odoo/` core): custom object-relational mapper, XML-RPC/JSON-RPC server, `ir.*` model system, QWeb templating for reports/views.
- **OWL** (Odoo Web Library) — Odoo's own component-based JS frontend framework, used throughout `addons/web/static/src`. No React/Vue/Angular.
- **Werkzeug** for the WSGI/HTTP layer.

## Key Dependencies (`requirements.txt`)

- **psycopg2** — PostgreSQL driver
- **lxml**, **Babel**, **docutils** — XML/i18n/doc processing
- **Pillow** — image processing
- **reportlab**, **PyPDF2/PyPDF** — PDF generation/parsing
- **openpyxl**, **XlsxWriter**, **xlrd/xlwt** — Excel import/export
- **gevent**/**greenlet** — async worker model (long-polling/cron)
- **passlib**, **cryptography**, **pyopenssl** — auth/security
- **num2words**, **python-stdnum**, **vobject**, **zeep** (SOAP), **qrcode**, **geoip2**, **python-ldap** — misc business/integration features
- **libsass** — SCSS compilation for web assets

## Build Tools / Package Managers

- **pip** with `requirements.txt` / `setup.py` (`setuptools`) for Python packaging.
- **npm** is used only inside the Docker image to install **rtlcss** and **node-less** for CSS/RTL asset processing during Odoo's asset bundling — there is no root-level `package.json` or JS build pipeline (Odoo bundles assets server-side via its own asset framework, not webpack/vite).

## Database / Storage

- **PostgreSQL 16** (see `docker-compose.yml`, `psycopg2` driver) — sole supported RDBMS.
- Filestore: local filesystem storage for attachments (`data_dir` in `docker/odoo.conf`, `odoo-filestore` volume in `docker-compose.yml`).

## Repository Structure

- **Type**: Poly-repo (single application), organized internally via Odoo's own module/addon convention rather than a JS-style workspace tool.
- **Workspace Tool**: None (no pnpm/lerna/nx/turbo/rush/go.work/Cargo workspace detected) — Odoo's own `addons_path` + manifest dependency graph (`odoo/modules/graph.py`) serves the equivalent role.
- **Workspace Root**: N/A
- **Apps/Services**: 621 addon modules under `addons/` (each self-contained, declares `depends` in `__manifest__.py`)
- **Shared Packages**: `odoo/` core (ORM, HTTP layer, CLI) is the shared framework all addons build on

## Infrastructure — Docker (custom, added on `banyan` branch)

Vanilla Odoo ships no Docker tooling; this fork adds a full local dev environment on top (commit "local docker setup", 8a9ce028):

- **`Dockerfile`** (root, new): `python:3.12-slim` base; installs system build deps (libxml2, libldap, libpq, wkhtmltopdf font deps, etc.), Node/npm + `rtlcss`; installs `requirements.txt`; copies source to `/opt/odoo`; runs `odoo-bin` on port 8069.
- **`docker-compose.yml`** (root, new): two services —
  - `db`: `postgres:16`, creds `odoo`/`odoo`, db `postgres`, persisted via `pg-data` volume.
  - `odoo`: built from the Dockerfile, depends on `db`, publishes `8069:8069`, mounts `./docker/odoo.conf` read-only at `/etc/odoo/odoo.conf` and a named volume `odoo-filestore` at `/var/lib/odoo`. Sets `PYTHONDONTWRITEBYTECODE=1`.
  - Uses Compose Watch (`develop.watch`): syncs/restarts on changes to `./addons` and `./odoo`, rebuilds on `requirements.txt` changes — live local dev without image rebuilds each time.
- **`docker/odoo.conf`** (new): `addons_path` pointed at the mounted repo, `db_host=db`, `db_port=5432`, `db_user=odoo`, `db_password=odoo`, `admin_passwd=admin`, `data_dir=/var/lib/odoo`, `dev_mode=reload`.
- Also added by this commit: `.github/ISSUE_TEMPLATE/`, `PULL_REQUEST_TEMPLATE.md`, `CONTRIBUTING.md`, `SECURITY.md`, `.gitignore`, `.weblate.json` (translation platform config) — project hygiene, not functional code.

## CI/CD

- **None currently configured** — no `.github/workflows/`, `.gitlab-ci.yml`, or `Makefile`. Only issue/PR templates exist under `.github/`.

## Development Commands

**Docker (primary path for this fork):**
```bash
docker compose up --build      # build + start db + odoo
docker compose watch           # live-reload dev loop (sync/restart on addons/ and odoo/ changes)
# → reachable at http://localhost:8069
```

**Bare-metal (secondary; deps are NOT installed in the host Python env currently):**
```bash
pip install -r requirements.txt
python3 odoo-bin -c odoo.conf
```
Common `odoo-bin` flags: `-d <db>` (database), `-i <module>` (install), `-u <module>` (update), `--test-enable`, `--test-tags <tag>`, `--dev=reload,qweb,xml` (autoreload).

**Testing:**
```bash
docker compose run odoo python odoo-bin -c /etc/odoo/odoo.conf --test-enable -i <module> --stop-after-init
```
No pytest setup; standard Odoo `TransactionCase`/`HttpCase` tests are discovered via each module's `tests/` package.

**Linting:**
- `setup.cfg` has a `[flake8]` section (extend-select `RST`, docstring role/directive config, excludes `.git,.tx,debian,doc,setup`)
- No `.pre-commit-config.yaml` or `pyproject.toml` found

**Environment/config:**
- No `.env` file or root `odoo.conf` — only `docker/odoo.conf`, mounted into the container
- DB/admin credentials are hardcoded there (`odoo`/`odoo`, `admin_passwd=admin`) — dev-only, not secrets-managed

**Task runner:** None (no Makefile/scripts dir) — `docker-compose.yml` is effectively the task runner for this fork.

## Custom vs. Stock Odoo

- **Stock**: the entire `odoo/` core and `addons/` business modules are unmodified upstream Odoo 18.0.
- **Custom (banyan fork additions)**: `Dockerfile`, `docker-compose.yml`, `docker/odoo.conf` (containerized local dev stack with live-reload watch), plus GitHub issue/PR templates and contributor docs (`CONTRIBUTING.md`, `SECURITY.md`).
