<div align="center">
	<a href="https://frappe.io/hr">
		<img src=".github/frappe-hr-logo.png" height="80px" width="80px" alt="Frappe HR Logo">
	</a>
	<h2>Frappe HR</h2>
	<p align="center">
		<p>Open Source, modern, and easy-to-use HR and Payroll Software</p>
	</p>

[![CI](https://github.com/frappe/hrms/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/frappe/hrms/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/frappe/hrms/branch/develop/graph/badge.svg?token=0TwvyUg3I5)](https://codecov.io/gh/frappe/hrms)

<a href="https://trendshift.io/repositories/10972" target="_blank"><img src="https://trendshift.io/api/badge/repositories/10972" alt="frappe%2Fhrms | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</div>

<div align="center">
	<img src=".github/hrms-hero.png"/>
</div>

<div align="center">
	<a href="https://frappe.io/hr">Website</a>
	-
	<a href="https://docs.frappe.io/hr/introduction">Documentation</a>
</div>

## Frappe HR

Frappe HR has everything you need to drive excellence within the company. It's a complete HRMS solution with over 13 different modules right from Employee Management, Onboarding, Leaves, to Payroll, Taxation, and more!

## Motivation
When Frappe team started growing in terms of size, we needed an open-source HR and Payroll software. We didn't find any "true" open-source HR software out there and so decided to build one ourselves.
Initially, it was a set of modules within ERPNext but version 14 onwards, as the modules became more mature, Frappe HR was created as a separate product.

## Key Features

- **Employee Lifecycle**: From onboarding employees, managing promotions and transfers, all the way to documenting feedback with exit interviews, make life easier for employees throughout their life cycle.
- **Leave and Attendance**: Configure leave policies, pull regional holidays with a click, check-in and check-out with geolocation capturing, track leave balances and attendance with reports.
- **Expense Claims and Advances**: Manage employee advances, claim expenses, configure multi-level approval workflows, all this with seamless integration with ERPNext accounting.
- **Performance Management**: Track goals, align goals with key result areas (KRAs), enable employees to evaluate themselves, make managing appraisal cycles easy.
- **Payroll & Taxation**: Create salary structures, configure income tax slabs, run standard payroll, accomodate additional salaries and off cycle payments, view income breakup on salary slips and so much more.
- **Frappe HR Mobile App**: Apply for and approve leaves on the go, check-in and check-out, access employee profile right from the mobile app.

<details open>

<summary>View Screenshots</summary>
	<img src=".github/hrms-appraisal.png"/>
	<img src=".github/hrms-requisition.png"/>
	<img src=".github/hrms-attendance.png"/>
	<img src=".github/hrms-salary.png"/>
	<img src=".github/hrms-pwa.png"/>
</details>

### Under the Hood

- [**Frappe Framework**](https://github.com/frappe/frappe): A full-stack web application framework written in Python and Javascript. The framework provides a robust foundation for building web applications, including a database abstraction layer, user authentication, and a REST API.

- [**Frappe UI**](https://github.com/frappe/frappe-ui): A Vue-based UI library, to provide a modern user interface. The Frappe UI library provides a variety of components that can be used to build single-page applications on top of the Frappe Framework.

## Production Setup

### Managed Hosting

You can try [Frappe Cloud](https://frappecloud.com), a simple, user-friendly and sophisticated [open-source](https://github.com/frappe/press) platform to host Frappe applications with peace of mind.

It takes care of installation, setup, upgrades, monitoring, maintenance and support of your Frappe deployments. It is a fully featured developer platform with an ability to manage and control multiple Frappe deployments.

<div>
	<a href="https://frappecloud.com/hrms/signup" target="_blank">
		<picture>
			<source media="(prefers-color-scheme: dark)" srcset="https://frappe.io/files/try-on-fc-white.png">
			<img src="https://frappe.io/files/try-on-fc-black.png" alt="Try on Frappe Cloud" height="28" />
		</picture>
	</a>
</div>


## Development setup
### Docker
You need Docker, docker-compose and git setup on your machine. Refer [Docker documentation](https://docs.docker.com/). After that, run the following commands:
```
git clone https://github.com/frappe/hrms
cd hrms/docker
docker-compose up
```

Wait for some time until the setup script creates a site. After that you can access `http://localhost:8000` in your browser and the login screen for HR should show up.

Use the following credentials to log in:

- Username: `Administrator`
- Password: `admin`

### Local

1. Set up bench by following the [Installation Steps](https://frappeframework.com/docs/user/en/installation) and start the server and keep it running
	```sh
	$ bench start
	```
2. In a separate terminal window, run the following commands
	```sh
	$ bench new-site hrms.local
	$ bench get-app erpnext
	$ bench get-app hrms
	$ bench --site hrms.local install-app hrms
	$ bench --site hrms.local add-to-hosts
	```
3. You can access the site at `http://hrms.local:8080`

## Testing

Frappe HR has a comprehensive test suite to ensure code quality and prevent regressions. Before submitting a pull request, please make sure all tests pass locally.

### Setting Up Tests

**For Docker setup:**
```bash
# Enable testing on the site (one-time)
docker exec docker-frappe-1 bash -c "cd /home/frappe/frappe-bench && bench --site hrms.localhost set-config allow_tests true"
```

**For local bench setup:**
```bash
# Enable testing on your site (one-time)
bench --site hrms.local set-config allow_tests true
```

### Running Tests

**For Docker setup:**
```bash
# Run all HRMS tests
docker exec docker-frappe-1 bash -c "cd /home/frappe/frappe-bench && bench --site hrms.localhost run-tests --app hrms"

# Run tests for a specific doctype
docker exec docker-frappe-1 bash -c "cd /home/frappe/frappe-bench && bench --site hrms.localhost run-tests --doctype 'Leave Application'"

# Run tests for a specific module
docker exec docker-frappe-1 bash -c "cd /home/frappe/frappe-bench && bench --site hrms.localhost run-tests --module 'hrms.hr.doctype.attendance'"
```

**For local bench setup:**
```bash
# Run all HRMS tests
bench --site hrms.local run-tests --app hrms

# Run tests for a specific doctype
bench --site hrms.local run-tests --doctype "Leave Application"

# Run tests for a specific module
bench --site hrms.local run-tests --module "hrms.hr.doctype.attendance"

# Run parallel tests (faster, same as CI)
bench --site hrms.local run-parallel-tests --app hrms
```

### Writing Tests

HRMS uses Frappe's testing framework. Test files are located alongside the code in `test_<doctype>.py` files. For example:
- `hrms/hr/doctype/leave_application/test_leave_application.py`
- `hrms/payroll/doctype/salary_slip/test_salary_slip.py`

Tests inherit from `IntegrationTestCase` or `HRMSTestSuite` (which provides HRMS-specific test utilities).

For more details on writing tests, refer to the [Frappe Testing Documentation](https://frappeframework.com/docs/user/en/testing).

## Code Quality

Frappe HR uses [Ruff](https://github.com/astral-sh/ruff) for linting and code formatting. Before submitting code, please ensure it passes linting and is properly formatted.

### Setting Up Ruff

**For Docker setup:**
```bash
# Install Ruff in the container (one-time)
docker exec docker-frappe-1 pip3 install ruff
```

**For local bench setup:**
```bash
# Activate bench environment and install Ruff
cd ~/frappe-bench
source env/bin/activate
pip install ruff
```

### Running Ruff

**For Docker setup:**
```bash
# Check code quality
docker exec docker-frappe-1 bash -c "cd /home/frappe/frappe-bench/apps/hrms && ruff check ."

# Auto-format code
docker exec docker-frappe-1 bash -c "cd /home/frappe/frappe-bench/apps/hrms && ruff format ."

# Check specific files or directories
docker exec docker-frappe-1 bash -c "cd /home/frappe/frappe-bench/apps/hrms && ruff check hrms/hr/doctype/leave_application/"
```

**For local bench setup:**
```bash
# Navigate to HRMS app directory
cd ~/frappe-bench/apps/hrms

# Check code quality
ruff check .

# Auto-format code
ruff format .

# Check specific files or directories
ruff check hrms/hr/doctype/leave_application/
```

### Code Style Guidelines

**Important:** HRMS uses **tabs for indentation** (not spaces). This is configured in `pyproject.toml` and enforced by Ruff.

**Key style rules:**
- **Indentation:** Tabs (not spaces)
- **Line length:** 110 characters maximum
- **Import ordering:** Imports should be organized in this order:
  1. Standard library
  2. Third-party packages
  3. `frappe`
  4. `erpnext`
  5. `hrms`
  6. Local imports

Ruff will automatically organize imports when you run `ruff format .`

### Pre-commit Checks

Before committing, ensure:
1. **All tests pass** - Run the test commands for your setup (see [Testing](#testing) section above)
2. **Code is formatted** - Run `ruff format .` (see [Running Ruff](#running-ruff) section above)
3. **No linting errors** - Run `ruff check .` (see [Running Ruff](#running-ruff) section above)
4. **Commit messages follow conventions** - Use [conventional commits](http://karma-runner.github.io/4.0/dev/git-commit-msg.html) format (enforced by commitlint)

## Learning and Community

1. [Frappe School](https://frappe.school) - Learn Frappe Framework and ERPNext from the various courses by the maintainers or from the community.
2. [Documentation](https://docs.frappe.io/hr) - Extensive documentation for Frappe HR.
3. [User Forum](https://discuss.erpnext.com/) - Engage with the community of ERPNext users and service providers.
4. [Telegram Group](https://t.me/frappehr) - Get instant help from the community of users.


## Contributing

We welcome contributions to Frappe HR! Before you start, please review the guidelines below.

### Getting Started

1. Read the [Testing](#testing) and [Code Quality](#code-quality) sections above
2. Follow the [ERPNext Issue Guidelines](https://github.com/frappe/erpnext/wiki/Issue-Guidelines) when reporting bugs
3. Review the [Pull Request Requirements](https://github.com/frappe/erpnext/wiki/Contribution-Guidelines) before submitting code
4. For security vulnerabilities, please [report them responsibly](https://erpnext.com/security)

### Frontend Development

Frappe HR includes two Vue.js frontend applications:

**PWA (Progressive Web App)** - Mobile-friendly employee self-service app
```bash
# Development
yarn dev-pwa

# Build for production
yarn build-pwa
```

**Roster App** - Shift scheduling and roster management
```bash
# Development
yarn dev-roster

# Build for production
yarn build-roster
```

Both apps use Vue 3, Vite, and Tailwind CSS. Frontend code is located in `frontend/` and `roster/` directories.

### Commit Message Convention

This project follows [Conventional Commits](http://karma-runner.github.io/4.0/dev/git-commit-msg.html). Your commit messages should be structured as:

```
<type>: <description>

[optional body]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Example:** `docs: add testing and code quality guidelines to README`


## Logo and Trademark Policy

Please read our [Logo and Trademark Policy](TRADEMARK_POLICY.md).

<br />
<br />
<div align="center" style="padding-top: 0.75rem;">
	<a href="https://frappe.io" target="_blank">
		<picture>
			<source media="(prefers-color-scheme: dark)" srcset="https://frappe.io/files/Frappe-white.png">
			<img src="https://frappe.io/files/Frappe-black.png" alt="Frappe Technologies" height="28"/>
		</picture>
	</a>
</div>

