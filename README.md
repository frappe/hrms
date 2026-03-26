# HortiHub

HortiHub is a customized mobile PWA for HR operations, built on top of [Frappe HRMS](https://github.com/frappe/hrms) and designed to install alongside ERPNext. It strips the full HRMS down to a focused employee-facing progressive web app with a HortiHub-specific feature set.

## Features

- **Check-In / Check-Out** with optional geolocation tracking
- **Camera-only photo capture** on check-in, saved as an attachment to the check-in record
- **Leave requests** — apply and track leave applications
- **Attendance requests** — submit attendance correction requests
- **Salary slips** — view pay slips on the go
- **Chat** — direct link to Raven (`/raven`) for team messaging
- **Push notifications** via Firebase Cloud Messaging

### Removed from upstream HRMS PWA
- Shift requests and shift assignments
- Expense claims (hidden by default; can be re-enabled via settings)
- Employee advances (hidden by default; can be re-enabled via settings)

## HortiHub Settings

HR Managers and System Managers can toggle the following from the **Settings** page inside the app:

| Setting | Default | Description |
|---|---|---|
| Require Photo on Check-in | Off | Forces employees to capture a camera photo before confirming check-in/out |
| Hide Accounting Features | On | Hides expense claims and employee advances from Quick Links and the request feed |

These settings are stored in **HR Settings** (ERPNext backend) and apply app-wide.

## Bottom Navigation

| Tab | Route |
|---|---|
| Home | `/home` |
| Attendance | `/dashboard/attendance` |
| Leaves | `/dashboard/leaves` |
| Salary | `/dashboard/salary-slips` |
| Chat | `/raven` |

## Installation

HortiHub is installed as the `hrms` Frappe app alongside ERPNext.

### Prerequisites

- Frappe Framework >= 17
- ERPNext >= 17
- [Raven](https://github.com/The-Commit-Company/raven) (for the Chat tab)

### Local Development

1. Set up a Frappe bench and start the server:
   ```sh
   bench start
   ```

2. In a separate terminal:
   ```sh
   bench new-site hortihub.localhost
   bench get-app erpnext
   bench get-app https://github.com/mkamalc/hr-app
   bench --site hortihub.localhost install-app hrms
   bench --site hortihub.localhost add-to-hosts
   ```

3. Build the PWA frontend:
   ```sh
   cd apps/hrms
   yarn install
   yarn build
   ```

4. Access the app at `http://hortihub.localhost:8080/hrms`

### Docker

```sh
git clone https://github.com/mkamalc/hr-app
cd hr-app/docker
docker-compose up
```

Access at `http://localhost:8000` — login with `Administrator` / `admin`.

## Tech Stack

- **Frontend**: Vue 3, Ionic Vue, Vite, TailwindCSS, Frappe UI
- **PWA**: `vite-plugin-pwa`, Workbox, Firebase Cloud Messaging
- **Backend**: Python, Frappe Framework, ERPNext

## Based On

This project is a customization of [Frappe HRMS](https://github.com/frappe/hrms) by [Frappe Technologies](https://frappe.io). The original project is open-source under the GNU GPL v3 license.
