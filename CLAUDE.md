# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Frappe HR (`hrms`) — an open-source HR & Payroll app built on the **Frappe Framework** and **ERPNext**. It is **not a standalone app**: it must be installed into a Frappe *bench* alongside `frappe` and `erpnext` (declared in `required_apps` / `[tool.bench.frappe-dependencies]`). Almost every command runs through the `bench` CLI from the bench directory (typically `~/frappe-bench`), not from this repo directory.

A "DocType" is Frappe's core unit: a model defined by a `<doctype>.json` (schema/fields), a `<doctype>.py` controller (server logic, subclass of `Document`), and a `<doctype>.js` (desk client form logic). Tests live next to them as `test_<doctype>.py`.

## Commands

Run inside the bench (`cd ~/frappe-bench`), with the site usually `test_site` in CI or `hrms.localhost` locally.

```sh
bench start                          # run the full dev stack (web, workers, watcher)
bench --site <site> migrate          # apply schema changes + patches.txt after pulling/editing doctypes
bench --site <site> console          # interactive Python shell with frappe loaded
bench --site <site> execute hrms.path.to.function   # run a server function directly
bench build --app hrms               # build desk JS/CSS bundles
```

Tests (Frappe's unittest-based runner, not pytest):

```sh
# Full suite the way CI runs it (sharded)
bench --site test_site run-parallel-tests --app hrms --total-builds 3 --build-number 1 --lightmode

# One module
bench --site <site> run-tests --module hrms.hr.doctype.leave_application.test_leave_application

# One DocType / one test
bench --site <site> run-tests --doctype "Leave Application"
bench --site <site> run-tests --module hrms.payroll.doctype.salary_slip.test_salary_slip --test test_salary_slip_with_holidays_included
```

`hooks.py` sets `before_tests = "hrms.tests.test_utils.before_tests"` (fiscal year, default company, etc. created before the suite runs).

Lint/format — **Ruff**, configured in `pyproject.toml`. Note the deliberate house style: **tab indentation, double quotes, line length 110**. Pre-commit also runs Prettier on JS/TS/Vue/CSS (the `frontend/` dir is excluded) and blocks direct commits to `develop`.

```sh
pre-commit install      # one-time
pre-commit run --all-files
ruff check --fix . && ruff format .
```

## Frontends (Vue SPAs)

Two separate Vue 3 + Vite + frappe-ui single-page apps live alongside the Python app. Build output is served by Frappe under `/assets/hrms/...` (route rules in `hooks.py`). `frappe-ui` is a **git submodule** — run `git submodule update --init` after cloning.

- `frontend/` — the **PWA / Employee Self-Service mobile app** (Ionic Vue, Firebase push). Dev: `cd frontend && yarn dev`. Served at `/hrms`.
- `roster/` — the **shift planning / roster** SPA. Dev: `cd roster && yarn dev`. Served at `/hr`. Backed by `hrms/api/roster.py`.

From repo root, `yarn build` builds both; `yarn dev-pwa` / `yarn dev-roster` run them individually. The desk-side `.js` files under `hrms/**/doctype/**` and `hrms/public/js/` are classic Frappe form scripts, unrelated to these SPAs.

## Architecture

Three modules (see `hrms/modules.txt`), each a top-level package with the same internal layout (`doctype/`, `report/`, `dashboard_chart/`, `number_card/`, `workspace/`, `notification/`):

- **`hrms/hr/`** — leave, attendance, shifts, expense claims, recruitment, onboarding/separation, appraisal, employee lifecycle. The largest module.
- **`hrms/payroll/`** — salary structures, salary slips, payroll entry, tax slabs, withholding.
- **`hrms/organization_structure/`** — a custom position-management / org-chart module (Nested Set trees of Organization Units and Positions, auto branch staffing). It has its own thorough `README.md` — read it before touching that module. Reports/cards/charts and the org & location chart pages live here.

Cross-cutting wiring is centralized in **`hrms/hooks.py`** — read it first to understand runtime behavior. It declares:
- `override_doctype_class` — HRMS subclasses ERPNext's `Employee`, `Timesheet`, `Payment Entry`, `Project` (implementations in `hrms/overrides/`).
- `doc_events` — hooks into ERPNext/Frappe doctypes (Journal Entry, Payment Entry, Company, User, etc.) so HRMS reacts to accounting/master-data events. When changing expense-claim or payroll payment flows, trace through these.
- `scheduler_events` — cron-like background jobs (auto-attendance, leave allocation/expiry, reminders, interview notifications).
- `regional_overrides` — India/UAE-specific logic swapped in via `hrms/regional/`.
- `override_doctype_dashboards`, `global_search_doctypes`, accounting-dimension and repost configs.

Other shared code: `hrms/controllers/` (employee boarding, reminders — shared logic across doctypes), `hrms/mixins/` (e.g. appraisal, PWA notifications), `hrms/api/` (whitelisted endpoints for the SPAs; note `roster.py` whitelists allowed filter keys explicitly), `hrms/utils/` (holiday list caching, hierarchy charts).

## Conventions & gotchas

- **Migrations are `patches.txt`**, not Django/Alembic. Data/schema migrations are Python modules under `hrms/patches/` listed in `patches.txt` (split into `[pre_model_sync]` / `[post_model_sync]`); they run on `bench migrate`. Append new patches; date-comment them as existing entries do.
- **API methods must be type-annotated.** `hooks.py` sets `require_type_annotated_api_methods = True` and `export_python_type_annotations = True` — whitelisted methods without annotations will fail.
- **Editing a workspace** (`*/workspace/*/*.json`): Frappe only re-imports on `bench migrate` if the JSON `modified` timestamp is newer than the DB copy. Bump `modified` (or run the module's `refresh_*` helper) or the change won't apply.
- DocType schema changes live in the `.json`; after editing, run `bench --site <site> migrate` to sync the DB.
- Don't commit directly to `develop` (pre-commit blocks it); branch off it. Commits follow conventional-commits (`commitlint.config.js`), enforced for release notes.

## Docker dev

`docker/docker-compose.yml` + `docker/init.sh` bootstrap a full bench, create a site, and install hrms — `cd docker && docker-compose up`, then `http://localhost:8000` (Administrator / admin). Use this when you don't already have a bench.
