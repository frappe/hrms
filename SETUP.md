# Realtyna HRMS — Setup Guide

A customised fork of [Frappe HRMS](https://github.com/frappe/hrms) (v16) for Realtyna, built on Frappe Framework v16 + ERPNext v16.

## What's different from upstream HRMS

| Feature | Description |
|---|---|
| **Mobile Timer** | Clockify-style timer on the home screen — tap Start, fill in activity/project/description, tap Stop to auto-save a Timesheet log |
| **Simplified Timesheet form** | Shows only Time Logs, Note, and Attachment; all other fields are auto-filled |
| **Desktop sidebar layout** | On screens ≥ 768 px the app switches to a two-panel layout: navigation sidebar on the left, content on the right |
| **Timesheet submit for Employee** | Employees can submit their own timesheets from the mobile app |
| **Cleaned home screen** | Check-In, Request Attendance, and Request Shift removed from quick links |

---

## Prerequisites

| Tool | Minimum version | Notes |
|---|---|---|
| Python | 3.10 | 3.12 recommended |
| Node.js | 18 | Use [nvm](https://github.com/nvm-sh/nvm): `nvm install 18 && nvm use 18` |
| MariaDB | 10.6 | Must be configured for `utf8mb4` (see below) |
| Redis | 6 | Must be running before `bench start` |
| wkhtmltopdf | 0.12.6 | Required for PDF generation |
| Git | 2.x | |
| pip / frappe-bench | latest | `pip install frappe-bench` |

### MariaDB character-set configuration

Create or edit `/etc/mysql/conf.d/frappe.cnf` (path may vary by OS):

```ini
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
```

Restart MariaDB after saving (`brew services restart mariadb` on macOS).

---

## Installation

### 1. Install frappe-bench CLI

```bash
pip install frappe-bench
```

### 2. Initialise a new bench

```bash
bench init frappe-hr --frappe-branch version-16
cd frappe-hr
```

### 3. Get ERPNext

```bash
bench get-app erpnext --branch version-16
```

### 4. Get this custom HRMS fork

```bash
bench get-app hrms git@github.com:chandler-realtyna/hrms.git --branch version-16
```

> Make sure you have SSH access to the GitHub repo, or use the HTTPS URL:
> `https://github.com/chandler-realtyna/hrms.git`

### 5. Create a site

```bash
bench new-site hr.localhost \
  --mariadb-root-password <your-mariadb-root-password> \
  --admin-password <choose-an-admin-password>
```

### 6. Install apps on the site

```bash
bench --site hr.localhost install-app erpnext
bench --site hr.localhost install-app hrms
```

### 7. Enable developer mode

```bash
bench --site hr.localhost set-config developer_mode 1
bench --site hr.localhost clear-cache
```

### 8. Run migrations

```bash
bench --site hr.localhost migrate
```

This runs all pending patches, including the one that:
- Grants the **Employee** role `submit` permission on Timesheets
- Enables `ignore_employee_time_overlap` in Projects Settings (required for the timer)

### 9. Build the frontend

```bash
cd apps/hrms/frontend
npm install
npm run build
cd ../../..
```

### 10. Start the server

```bash
bench start
```

Open **http://hr.localhost:8000/hrms** in your browser.

---

## Daily development workflow

### Rebuild the frontend after any JS/Vue changes

```bash
cd apps/hrms/frontend && npm run build && cd ../../..
bench --site hr.localhost clear-cache
```

The `postbuild` script automatically copies the compiled `index.html` into `hrms/www/hrms.html` with the correct asset hashes — no manual update needed.

### Run the dev server with hot-reload (no Frappe backend changes needed)

```bash
cd apps/hrms/frontend
npm run dev
```

Then open **http://hr.localhost:8080/hrms** — the Vite dev server proxies API calls to the bench.

### Apply Python/DB changes

```bash
bench --site hr.localhost migrate
bench --site hr.localhost clear-cache
```

---

## Repository layout (custom files)

```
apps/hrms/
├── SETUP.md                             ← this file
├── frontend/src/
│   ├── App.vue                          # Root shell — mounts DesktopSidebar
│   ├── components/
│   │   ├── DesktopSidebar.vue           # Sidebar on md+ screens
│   │   ├── TimeLogsTable.vue            # Time log rows + add/edit modal
│   │   ├── BaseLayout.vue              # Responsive width fixes
│   │   ├── FormView.vue                # Responsive width + submit flow
│   │   └── icons/TimerIcon.vue         # Stopwatch SVG icon
│   ├── data/notifications.js           # null-safe user filter fix
│   ├── router/timesheets.js            # Adds /timesheets/timer route
│   └── views/
│       ├── Home.vue                    # Quick links (Timer first)
│       └── timesheet/
│           ├── Form.vue                # Simplified form (logs + note only)
│           └── Timer.vue              # Clockify-style timer
└── hrms/
    ├── api/__init__.py                 # save_timer_log API endpoint
    └── patches/v16_0/
        └── configure_timesheet_for_mobile_timer.py
```

---

## Important notes

- **`sites/<site>/site_config.json`** holds your DB name and password. It is git-ignored and must never be committed.
- **`Procfile`** at the bench root contains machine-specific Node.js paths from `nvm`. Each developer gets their own Procfile when they run `bench init` — do not commit or copy it between machines.
- Redis ports default to `13000` (cache) and `11000` (queue). Edit `config/redis_cache.conf` and `config/redis_queue.conf` if there are port conflicts.

---

## Pulling upstream HRMS updates

```bash
cd apps/hrms
git fetch upstream
git merge upstream/version-16
# resolve any conflicts
cd frontend && npm install && npm run build && cd ../../..
bench --site hr.localhost migrate
bench --site hr.localhost clear-cache
```

---

## Remotes

| Remote | URL |
|---|---|
| `origin` | `git@github.com:chandler-realtyna/hrms.git` (our fork) |
| `upstream` | `https://github.com/frappe/hrms.git` (official HRMS) |
