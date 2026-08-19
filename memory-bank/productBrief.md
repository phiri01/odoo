# Product Brief

> This document captures the **product and project context** for development teams.
> It ensures all agents understand the product's purpose, users, constraints, **and the project's foundation**.

## Project Foundation

- **Project Name**: odoo (fork of `DaKaZ/odoo`, working branch `banyan`)
- **Objectives**: Provide a local, containerized development environment for the Odoo ERP source tree, enabling live-reload development of Odoo core and custom addons without a manual Python/PostgreSQL setup.
- **Scope**: This repo is upstream Odoo (business apps + framework) plus a single addition on the `banyan` branch — a Docker-based dev environment (`Dockerfile`, `docker-compose.yml`, `docker/odoo.conf`). It does not add new business functionality; it wraps the existing suite for local runs.
- **Repository Structure**: `odoo/` (core framework: ORM, HTTP layer, module loader, CLI `odoo-bin`); `addons/` (621 first-party app/module directories, each self-contained per Odoo's module convention); `debian/`, `setup/` (packaging); root-level `Dockerfile`, `docker-compose.yml`, `docker/odoo.conf` (fork-added dev environment). See [[systemPatterns]] for directory-level detail.
- **Key Stakeholders**: Repo owner (GitHub `DaKaZ`); appears to be a solo/small-team developer maintaining a personal dev instance for Banyan Software (branch name `banyan` matches user's employer domain).

## Git Configuration

- **Repository**: Yes
- **Provider**: GitHub
- **CLI Available**: gh
- **Remote URL**: https://github.com/DaKaZ/odoo.git
- **Default Branch**: banyan (repo has no `main`/`master`)
- **Metadata Branch**: banyan
- **Routing Mode**: classic (unprotected — solo fork)
- **Sync Automation**: none
- **Archive Strategy**: local-merge

## Product Overview

- **Name**: Odoo
- **Value Proposition**: All-in-one open-source suite of integrated business applications (CRM, Sales, Inventory, Accounting, HR, Manufacturing, eCommerce, etc.) for SMBs and growing enterprises.
- **Product Type**: Platform / Web-based ERP application suite (Python/PostgreSQL backend, OWL-based web client)
- **Stage**: Mature (long-running upstream OSS project, release 18.0); this fork itself is an early-stage personal/team dev environment (single "local docker setup" commit on top of upstream)

## Key Functionality

Core capabilities present as top-level `addons/` categories:

- CRM & Sales (crm, sale, sale_management, event, event_sale)
- eCommerce/Website (website, website_sale)
- Inventory/Warehouse & Manufacturing (stock, mrp)
- Accounting/Invoicing (account, account_edi, account_payment, account_peppol)
- Human Resources (hr, hr_attendance, hr_contract, hr_expense, hr_holidays, hr_recruitment, hr_fleet)
- Point of Sale, Fleet, Calendar, Gamification, Digest/reporting, Barcode scanning
- Authentication (auth_ldap, auth_oauth, auth_totp, auth_passkey), Cloud storage (cloud_storage_azure/google)

## Markets Serviced

- **Primary Market**: SMB and mid-market ERP (general business operations)
- **Secondary Markets**: Vertical/localized markets via country-specific compliance modules
- **Geographic Focus**: Global — 228 `l10n_*` localization modules (e.g. l10n_ae, l10n_ar, l10n_at, l10n_au, l10n_bd, l10n_be) covering country-specific accounting/tax/legal rules
- **Market Size**: [To be determined]

## Competitive Landscape

- **Direct Competitors**: [To be determined — not discoverable from source]
- **Indirect Competitors**: [To be determined]
- **Key Differentiators**: Open-source, fully modular (install only needed apps), single integrated data model across all business functions
- **Competitive Advantages**: [To be determined]

## Key Personas

### Primary Users

| Persona | Role | Goals | Pain Points | Success Metrics |
|---------|------|-------|-------------|-----------------|
| End User | Sales rep / accountant / HR staff / warehouse worker | Use the respective business app day-to-day | [To be determined] | [To be determined] |

### Secondary Users

| Persona | Role | Goals |
|---------|------|-------|
| Administrator | Installs/configures apps, manages users & security groups | Keep the instance configured and secure |

### Administrators/Operators

| Persona | Role | Responsibilities |
|---------|------|------------------|
| Developer/Implementer | Builds/customizes addons, runs the Docker dev loop | Local iteration on `addons/` and `odoo/` via live-reload — this fork's apparent primary persona |

## User Flows

- **Primary Flow**: [To be determined — depends which Odoo apps are actually used]
- **Onboarding**: Standard Odoo install wizard / database creation on first run
- **Key Workflows**:
  - [To be determined]

## Success Metrics & KPIs

[To be determined — this fork has no product-level metrics; it's a dev environment wrapper around upstream Odoo]

## Non-Functional Requirements

### Performance
- [To be determined]

### Scalability
- [To be determined]

### Security
- **Authentication**: Odoo's built-in auth plus optional `auth_ldap`, `auth_oauth`, `auth_totp`, `auth_passkey` addons
- **Authorization**: Odoo record rules (`ir.rule`) + access control lists (`ir.model.access.csv`), per-module
- **Compliance**: [To be determined — no compliance requirements documented for this fork]
- **Data Classification**: [To be determined]
- **Encryption**: [To be determined]

### Availability & Reliability
- [To be determined — this is a local dev environment, not a production deployment]

### Data & Privacy
- [To be determined]

### Accessibility
- [To be determined]

### Internationalization (i18n)
- Odoo ships translations and locale-aware formatting across 228 `l10n_*` localization modules; RTL support via `rtlcss` (built into the fork's Docker image)

### Browser/Platform Support
- [To be determined]

## Integration Points

### External Systems

| System | Purpose | Protocol | Direction |
|--------|---------|----------|-----------|
| PostgreSQL 16 | Primary datastore | libpq | Both |
| Payment gateways (Adyen, Authorize.net, Buckaroo, Mercado Pago, Mollie, PayPal, Razorpay, Stripe, Worldline, Xendit, Flutterwave, AsiaPay, Nuvei, APS) | Payment processing | REST (per-provider addon) | Outbound |
| Peppol network (`account_peppol`) | E-invoicing | Peppol/AS4 | Both |
| LDAP / Google (`auth_ldap`, `google_account`, `google_calendar`, `google_gmail`) | Identity & calendar/email sync | LDAP / OAuth / REST | Both |
| SMS gateways (`calendar_sms`, `crm_sms`, `hr_recruitment_sms`) | Notifications | Provider REST APIs | Outbound |

### APIs Consumed / Provided

[To be determined — Odoo exposes XML-RPC/JSON-RPC APIs broadly across all installed modules; no fork-specific API surface documented]

## Constraints & Assumptions

### Business Constraints
- [To be determined]

### Technical Constraints
- Hard dependency on PostgreSQL (docker-compose uses `postgres:16`)
- Python `>=3.10` (setup.py); Docker image pins Python 3.12
- Requires system libs for compiling deps (libxml2, libxslt, libldap, libpq) and Node/npm + `rtlcss` for asset building — all baked into the fork's Dockerfile

### Assumptions
- Dev environment assumes local Docker Compose usage with bind-mounted `./addons` and `./odoo` for live-reload (`dev_mode = reload` in `docker/odoo.conf`)
- Single-node Postgres with default `odoo`/`odoo` credentials — dev-only, not production-hardened

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hardcoded dev credentials (`odoo`/`odoo`, `admin_passwd=admin`) in `docker/odoo.conf` reaching a shared/production environment | Medium | High | Never reuse this compose file outside local dev; rotate credentials before any shared deployment |
| No CI/CD configured — regressions in custom code aren't automatically caught | Medium | Medium | Add CI once this fork starts carrying custom module changes beyond stock Odoo |

## Open Questions

- [ ] What specific client/project or internal use case does this Banyan-branded fork support?
- [ ] Will custom addons/modules be added on top of stock Odoo, or is this purely a dev-environment wrapper?

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2026-08-19 | bmb:init | Initial creation via brownfield explorer synthesis |

## Last Refreshed

2026-08-19
