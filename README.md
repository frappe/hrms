## Overview
This repository is a fork of [Frappe HR official codebase](https://github.com/frappe/hrms).

Clone the branch `blue-develop` to set up Frappe HR containers plus the demo database used for benchmark development.

# Running local containers
You need Podman ( open source altervative to Docker) on your machine to run local containers. Refer [Podman Installation](https://podman.io/docs/installation) documentation.

### Setting Up Local Containers with Podman
Create and start the Podman virtual machine:

```
podman machine init
podman machine start
```

Authenticate with Docker Hub to allow Podman to pull images from the Docker registry:

```
podman login docker.io
podman pull frappe/bench:v5.22.8
```

### Development setup

#### Cloning Repo
```
git clone git@github.com:blue-enterprise/hrms.git
```

#### Start the hrms app
```
cd hrms/docker
podman-compose up
```
Note: Start new terminal sessions for further work.

This will download the required image and start 3 containers, which you can verify using command `podman ps`

```
docker_mariadb_1
docker_redis_1
docker_frappe_1
```


The containers will be set up with the following software stack:
```
frappe/bench:v5.22.8 (base image)
Frappe v15.95.0
ERPNext v15.95.0
HRMS v15.55.0
```

The default docker-compose.yml file launches the application at: `localhost:8000`

> Note: If you prefer using Docker, refer to the original documentation.

#### Stop the hrms app
```
podman compose down
```


### Adding Employee Data to an Existing Container Programmatically

Follow the instructions to add a company called `NovaSoft` with 107 employees. For clean testing of task development or code updates we recommend a fresh start, including volumes pruning.

```
podman-compose down
podman volume prune
podman-compose up
```

To verify a clean start log-in into the DB container, password is `123`.

```
podman exec -it docker_mariadb_1 mysql -u root -p
```

Only one user database should exist, in this example the id `_3ba7b06c3cb19463` is assigned.

```
MariaDB [(none)]> SHOW DATABASES;
+--------------------+
| Database           |
+--------------------+
| _3ba7b06c3cb19463  |
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
5 rows in set (0.001 sec)
```

Execute the following queries (`USE` command takes time). The output should show: 0 employees, 2 users (Administrator and Guest), and 0 companies.

```
USE _3ba7b06c3cb19463;
SELECT COUNT(*) FROM tabEmployee;
SELECT COUNT(*) FROM tabUser;
SELECT name FROM tabCompany;
```

Assuming the container is already running, copy the script and data into the container. In the example below, the container name is `docker_frappe_1` (verify using `podman ps`). Use the following commands to create a parent directory and to copy  scripts, employee roster, and other files.

```
podman exec docker_frappe_1 mkdir -p /home/frappe/frappe-bench/apps/hrms/hrms/demo_data

podman cp hrms/demo_data/. docker_frappe_1:/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/
```

Then execute the script inside the container (it will create the company if it does not already exist):
```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.company_setup.create_demo_data --kwargs "{\"company\": \"NovaSoft\", \"abbr\": \"NS\", \"roster_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employees_roster.json\"}"'
```

Verify the DB content again, the queries should return: 107 employees, 109 users, and 1 company.

```
USE _3ba7b06c3cb19463;
SELECT COUNT(*) FROM tabEmployee;
SELECT COUNT(*) FROM tabUser;
SELECT name FROM tabCompany;
```

### Adding Attendance Data to Existing Company Programmatically

Assuming the script has been already copied to the containter, execute it (attendance records for certain employees will be added):

```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.attendance_setup.create_attendance_data --kwargs "{\"company\": \"NovaSoft\", \"attendance_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employee_attendance.json\"}"'
```

If you need to clean the attendance data for development purposes use:
```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.attendance_setup.clear_attendance_data --kwargs "{\"company\": \"NovaSoft\", \"attendance_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employee_attendance.json\"}"'
```

### Adding Recruitment Data to Existing Company Programmatically

Creates recruitment demo data including: Skills, Interview Types, Staffing Plans, Job Requisitions, Job Openings, Job Applicants, Interviews, Job Offers, and Appointment Letters.

```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.recruitment_setup.create_recruitment_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

To clear recruitment data for development purposes:
```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.recruitment_setup.clear_recruitment_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

### Adding Performance Management Data to Existing Company Programmatically

Creates performance management demo data including: Feedback Criteria, KRAs, Appraisal Templates, Appraisal Cycles, Employee Goals (with sub-goals), Appraisals, and Performance Feedback.

```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.performance_setup.create_performance_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

To clear performance data for development purposes:
```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.performance_setup.clear_performance_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

### Adding Employee Lifecycle (Tenure) Data to Existing Company Programmatically

Creates employee lifecycle demo data including: Onboarding Templates, Employee Onboardings, Training Programs, Training Events, Training Results, Training Feedback, Skills, Employee Skill Maps, Employee Promotions, Employee Transfers, Separation Templates, Employee Separations, Exit Interviews, Full & Final Statements, Grievance Types, Employee Grievances, Daily Work Summary Groups, and Daily Work Summaries.

```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.tenure_setup.create_tenure_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

To clear tenure data for development purposes:
```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.tenure_setup.clear_tenure_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

### Adding Leaves Management Data
Assuming the script has been already copied to the containter, execute it (leave management records for certain employees will be added):

```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.leaves_setup.configure_leave_management --kwargs "{\"company\": \"NovaSoft\", \"leaves_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employee_leaves.json\"}"'
```

If you need to clean the leaves data for development purposes use:
```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.leaves_setup.clear_leave_configuration --kwargs "{\"company\": \"NovaSoft\", \"leaves_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employee_leaves.json\"}"'
```

### Adding Payroll Data to Existing Company Programmatically

Creates payroll demo data including: Fiscal Year, Payroll Period, Income Tax Slab (federal brackets), Salary Components (earnings and deductions), Salary Structures (Salaried/Hourly), Salary Structure Assignments, and Salary Slips for November 2025. All configuration is loaded from the JSON file.

Note: This script requires company and employee data to be set up first (via `company_setup.py`).

```
podman cp hrms/demo_data/payroll_setup.py docker_frappe_1:/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/payroll_setup.py

podman cp hrms/demo_data/employee_payroll.json docker_frappe_1:/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employee_payroll.json

podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.payroll_setup.create_payroll_data --kwargs "{\"company\": \"NovaSoft\", \"payroll_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employee_payroll.json\"}"'
```

To clear payroll data for development purposes:
```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.payroll_setup.clear_payroll_data --kwargs "{\"company\": \"NovaSoft\", \"payroll_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employee_payroll.json\"}"'
```

<!-- To run the payroll test suite, first install pytest in the container, then run the tests directly with pytest (not via `bench run-tests`, which triggers a `before_tests` hook that creates a holiday list for the current year):
```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && ./env/bin/pip install pytest'

podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && ./env/bin/python -m pytest apps/hrms/hrms/demo_data/test_payroll_setup.py -v'
``` -->

## Verifying Data in the App

Navigate to `http://localhost:8000/app`, select the `NovaSoft` company, and confirm that the employees and related records have been created.

Log in using the `Administrator` user, and HR user, and another user to check access and permission to transactions.

## UI troubleshooting

* The UI displays the setup wizard and does not offer an option to skip it the first time you log in, go through it and create a new `test` company.
* If you are not logged as Administrator, the impersonation feature might be active. Simply log-off and log-in again.

## DB Updates

```
git checkout blue-develop
git pull origin blue-develop
git checkout -b feature/my-db-updates
# ... make changes ... or git stash pop # to recover uncommited updates (if needed)
git add .
git commit -m "feat: description"
git push origin feature/my-db-updates
```

Then, create a PR on GitHub

- base: blue-develop
- compare: feature/my-db-updates
- assign a reviewer to your PR