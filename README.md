# HortiHub

HortiHub is a customized mobile PWA for HR operations, built on top of [Frappe HRMS](https://github.com/frappe/hrms) and designed to install alongside ERPNext. It strips the full HRMS down to a focused employee-facing progressive web app with a HortiHub-specific feature set.

## Features

- **Check-In / Check-Out** with optional geolocation tracking
- **Camera-only photo capture** on check-in, saved as an attachment to the check-in record
- **Live location tracking** — track field workers continuously while they are checked in (background tracking via the Android APK; foreground-only in the browser)
- **Daily Reports** — employees submit a dated report with a file attachment; HR sets an approval status
- **Leave requests** — apply and track leave applications
- **Attendance requests** — submit attendance correction requests
- **Salary slips** — view pay slips on the go
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
| Enable Live Location Tracking | Off | Tracks an employee's location while they are checked in |
| Location Tracking Interval | 60s | Seconds between location pings while tracking is active |

These settings are stored in **HR Settings** (ERPNext backend) and apply app-wide.

## Bottom Navigation

| Tab | Route |
|---|---|
| Home | `/home` |
| Attendance | `/dashboard/attendance` |
| Leaves | `/dashboard/leaves` |
| Salary | `/dashboard/salary-slips` |

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

## Live Location Tracking

When **Enable Live Location Tracking** is on, the app records the employee's
position while they are checked in:

- **Start/stop** is tied to the check-in lifecycle — tracking starts on Check In
  and stops on Check Out. It also resumes automatically if the app restarts mid-shift.
- **In the Android APK**, tracking continues in the background (foreground-service
  notification) via `@capacitor-community/background-geolocation`.
- **In a plain browser/PWA**, tracking is foreground-only (`navigator.geolocation.watchPosition`).
- Pings are **buffered and sent in batches** to `hr_app.api.log_locations`; a
  `localStorage` queue makes them survive connectivity drops and restarts.
- A **one-time consent prompt** is shown before tracking starts.

Pings are stored in the **Employee Location Log** doctype. HR Managers can view
them on the **Employee Location Map** desk page (`/app/location-map`) or via the
standard list view.

> **Privacy:** Background location tracking requires a clear disclosure to
> employees and, for Google Play distribution, a Data Safety declaration.

## Android APK

The APK is a **Capacitor remote-URL shell**: the native app loads the live site
(`server.url` in `frontend/capacitor.config.json`) in its webview, so the existing
cookie auth and relative API calls keep working unchanged, while native plugins
(background GPS, camera) function. Update `server.url` to your own site before building.

Because Frappe Cloud only hosts the backend, the APK is built off-platform — either
locally or via the included GitHub Actions workflow (`.github/workflows/android.yml`,
run manually or by pushing an `android-v*` tag), which uploads the APK as a build artifact.

### Build locally

```sh
cd frontend
yarn install
npx cap sync android          # wires plugins into the native project
yarn apk:debug                # -> android/app/build/outputs/apk/debug/app-debug.apk
```

For a signed release build, create a keystore, configure signing in
`android/app/build.gradle`, then run `yarn apk:release`.

## Tech Stack

- **Frontend**: Vue 3, Ionic Vue, Vite, TailwindCSS, Frappe UI
- **PWA**: `vite-plugin-pwa`, Workbox, Firebase Cloud Messaging
- **Backend**: Python, Frappe Framework, ERPNext

## Based On

This project is a customization of [Frappe HRMS](https://github.com/frappe/hrms) by [Frappe Technologies](https://frappe.io). The original project is open-source under the GNU GPL v3 license.
