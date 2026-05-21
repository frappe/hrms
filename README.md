# Realtyna HRMS

A customised fork of [Frappe HRMS](https://github.com/frappe/hrms) built for Realtyna's internal team.  
Base version: **HRMS 16.7.1** on the `version-16` branch.

---

## What's different from the original HRMS?

The original Frappe HRMS is a full-featured HR platform with dozens of modules (Recruitment, Performance, Payroll, Attendance, Shifts, and more). This fork strips that back to the workflows Realtyna actually uses and adds a few tools that make the day-to-day faster.

### 1. Clockify-style Time Tracker

The original HRMS requires you to open a Timesheet form, add rows manually, fill in start/end times, and save. This fork replaces that with a **live timer**:

- Hit **Start** and describe what you're working on (Activity Type, Project, optional note)
- Hit **Stop** — a submitted Timesheet is created automatically
- **Discard** cancels the session without saving anything
- The timer survives page navigation (stored in `localStorage`)
- Lives at **Quick Links → Start Timer** on the Home screen and in the sidebar

Technically: a new `save_timer_log` API endpoint in `hrms/api/__init__.py` handles finding or creating the right Timesheet document for the day and appending the time log to it.

---

### 2. Desktop Layout with Sidebar

The original HRMS is a mobile-first PWA — on desktop it renders a narrow column centred on screen. This fork adds a **full desktop layout**:

- A **256 px sidebar** (`DesktopSidebar.vue`) shows at `md:` breakpoint and above
- The sidebar contains branding, user info, notification bell, and a sectioned nav (Timesheets / HR)
- The main content area fills the remaining width
- Mobile view is unchanged — the sidebar hides and the bottom tab bar appears as before

---

### 3. Simplified Timesheet Form

The original Timesheet form has ~20 fields (billing rate, exchange rate, company, employee, currency…). This fork trims it to the three fields an employee actually needs:

| Field | Notes |
|---|---|
| **Time Logs** | The table of individual work sessions — editable, each row has a pencil icon |
| **Note** | Free-text description or summary |
| **Attachment** | File upload |

Everything else (employee, company, dates, totals) is auto-filled by the system on save.

Each time log row is also **editable after the fact** — click the pencil icon to open the edit modal pre-filled with that row's values.

---

### 4. Home Screen Dashboard

The original home screen is a grid of links. This fork adds a **Working Hours Dashboard** directly on the home page:

- **Period selector** — Week (7 days), 2 Weeks (14 days), Month (30 days)
- **Total hours** for the period, displayed prominently
- **Bar chart** of hours per day — today highlighted in blue, zero-days in light grey
- **My Projects** section — top projects ranked by hours logged, with a proportional bar

Data comes from two new API endpoints (`get_working_hours_summary`, `get_employee_project_summary`).

---

### 5. Attendance & Shift Features Removed

The original app surfaces Attendance, Check-In/Out, and Shift Requests prominently. Realtyna tracks time through Timesheets, not attendance punches. These have been removed from:

- The bottom tab bar (mobile)
- The desktop sidebar navigation
- The Home screen Quick Links
- The Request Panel (pending items widget)

The underlying doctypes and data still exist in Frappe — only the frontend entry points are removed.

---

### 6. Permission & Settings Patches

Two backend changes are applied automatically on `bench migrate`:

| Change | Why |
|---|---|
| `Employee` role gets `submit=1` on Timesheet | Without this, employees can save but not submit their own timesheets |
| `Projects Settings.ignore_employee_time_overlap = 1` | Without this, the timer throws a 417 error if two time logs touch the same minute |

These are in `hrms/patches/v16_0/configure_timesheet_for_mobile_timer.py`.

---

### 7. Navigation Direction Fix

Ionic Vue's `ion-router-outlet` maintains a navigation stack. In the original app, navigating from (for example) Timesheets back to Home could trigger a "back" animation — popping the stack instead of loading Home fresh. Every sidebar link and tab button now uses `routerDirection="root"` to ensure it always lands on the correct page.

---

## Screens at a glance

| Screen | Path | Notes |
|---|---|---|
| Home | `/home` | Working hours dashboard + quick links + request panel |
| Timer | `/timesheets/timer` | Live Clockify-style timer |
| My Timesheets | `/timesheets` | List of your timesheets |
| Timesheet Detail | `/timesheets/:id` | Simplified form (Time Logs, Note, Attachment) |
| Leaves | `/dashboard/leaves` | Leave application and balance |
| Expenses | `/dashboard/expense-claims` | Expense claims |
| Salary Slips | `/dashboard/salary-slips` | View payslips |
| Profile / Settings | `/profile` | User profile |

---

## Setup

See [SETUP.md](../../SETUP.md) in the bench root for the full setup guide (bench install, site creation, first run).

A demo data script is included to pre-populate leave types, users, and salary slips:

```bash
bench --site hr.localhost execute hrms.demo_setup.execute
```

This creates:

- **8 leave types** — Annual, Sick, Casual, Maternity, Paternity, Bereavement, Study, Unpaid
- **HR Manager** — `sarah.johnson@realtyna.net` (password: `Realtyna@2024!`)
- **Employee** — `james.wilson@realtyna.net` (password: `Realtyna@2024!`)
- **3 months of Salary Slips** for the primary employee (Feb – Apr of current year)

---

## Key files changed vs upstream

```
frontend/src/
├── views/
│   ├── Home.vue                          # Added WorkingHoursDashboard, updated quick links
│   └── timesheet/
│       ├── Timer.vue                     # NEW — live timer
│       └── Form.vue                      # Simplified to 3 fields
├── components/
│   ├── DesktopSidebar.vue                # NEW — desktop nav sidebar
│   ├── WorkingHoursDashboard.vue         # NEW — hours chart + projects
│   ├── BottomTabs.vue                    # Removed attendance; fixed routerDirection
│   ├── BaseLayout.vue                    # Responsive width; header hidden on desktop
│   ├── RequestPanel.vue                  # Removed shift/attendance requests
│   ├── TimeLogsTable.vue                 # Added edit (pencil) button per row
│   ├── FormView.vue                      # Removed narrow mobile constraints
│   └── ListView.vue                      # Removed narrow mobile constraints
├── router/
│   ├── index.js                          # Removed attendance route
│   └── timesheets.js                     # Added /timesheets/timer route
└── App.vue                               # Added sidebar slot; showSidebar guard

hrms/
├── api/__init__.py                       # Added save_timer_log, get_working_hours_summary,
│                                         #   get_employee_project_summary
├── patches/v16_0/
│   └── configure_timesheet_for_mobile_timer.py   # NEW — submit permission + overlap setting
└── demo_setup.py                         # NEW — demo data script
```

---

## Original HRMS

Full documentation for the upstream project: https://docs.frappe.io/hrms

Source: https://github.com/frappe/hrms
