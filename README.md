## Overview
This repository is a fork of [Frappe HR official codebase](https://github.com/frappe/hrms).

Clone the branch `blue-develop` to set up the frappe HR and containers plus the demo database used for benchmark development. Follow the instructions below.

### Setting Up Local Containers with Podman
Initialize and start the Podman virtual machine:

```
podman machine init
podman machine start
```

Authenticate with Docker Hub to allow Podman to pull images from the Docker registry:

```
podman login docker.io
```

Start or stop the containers:
```
podman-compose up
podman compose down
```

The default docker-compose.yml file launches the application at: `localhost:8000`

> Note: If you prefer using Docker, refer to the original documentation.

### Adding Employee Data to an Existing Container Programmatically

Follow the instructions to add a company called `NovaSoft` with 106 employees. For clean testing of task development or code updates we recommend a fresh start, including volumes pruning.

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

Assuming the container is already running, copy the script and data into the container. In the example below, the container name is `docker_frappe_1` (verify using `podman ps`). The command first creates a parent directory, to then copy a folder with scripts and employee roster file.

```
podman exec docker_frappe_1 mkdir -p /home/frappe/frappe-bench/apps/hrms/hrms/demo_data

podman cp hrms/demo_data/. docker_frappe_1:/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/
```

Then execute the script inside the container (it will create the company if it does not already exist):
```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.company_setup.create_demo_data --kwargs "{\"company\": \"NovaSoft\", \"abbr\": \"NS\", \"roster_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employees_roster.json\"}"'
```

Verify the DB content again, the queries should return: 106 employees, 108 users, and 1 company.

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
podman cp hrms/demo_data/recruitment_setup.py docker_frappe_1:/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/recruitment_setup.py

podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.recruitment_setup.create_recruitment_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

To clear recruitment data for development purposes:
```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.recruitment_setup.clear_recruitment_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

### Adding Performance Management Data to Existing Company Programmatically

Creates performance management demo data including: Feedback Criteria, KRAs, Appraisal Templates, Appraisal Cycles, Employee Goals (with sub-goals), Appraisals, and Performance Feedback.

```
podman cp hrms/demo_data/performance_setup.py docker_frappe_1:/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/performance_setup.py

podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.performance_setup.create_performance_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

To clear performance data for development purposes:
```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.performance_setup.clear_performance_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

### Adding Employee Lifecycle (Tenure) Data to Existing Company Programmatically

Creates employee lifecycle demo data including: Onboarding Templates, Employee Onboardings, Training Programs, Training Events, Training Results, Training Feedback, Skills, Employee Skill Maps, Employee Promotions, Employee Transfers, Separation Templates, Employee Separations, Exit Interviews, Full & Final Statements, Grievance Types, Employee Grievances, Daily Work Summary Groups, and Daily Work Summaries.

```
podman cp hrms/demo_data/tenure_setup.py docker_frappe_1:/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/tenure_setup.py

podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.tenure_setup.create_tenure_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

To clear tenure data for development purposes:
```
podman exec -it docker_frappe_1 bash -c 'cd frappe-bench && bench --site hrms.localhost execute hrms.demo_data.tenure_setup.clear_tenure_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

## Verifying Data in the App

Navigate to `http://localhost:8000/app`, select the `NovaSoft` company, and confirm that the employees and related records have been created.

Log in using the `Administrator` user, and HR user, and another user to check access and permission to transactions.

## UI troubleshooting

* The UI displays the setup wizard and does not offer an option to skip it the first time you log in, go trhough it and create a new `test` company.
* If you are not logged as Administrator, the impersonation feature might be active. Simploy log-off and log-in again.