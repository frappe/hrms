## Overview
This repository is a fork of [Frappe HR official codebase](https://github.com/frappe/hrms).

Clone the branch `blue-develop` to set up Frappe HR containers plus the demo database used for benchmark development.

## Running local containers
You need Podman ( open source alternative to Docker) on your machine to run local containers. Refer [Podman Installation](https://podman.io/docs/installation) documentation.

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

The company `NovaSoft` with 107 employees, departments, positions, recruitment data, payroll data, leaves, and all other required data creation is now part of docker_frappe_1 container startup. It may take 1 to 2 mins for container to be up running, you can check container logs using 
```
podman logs -f docker_frappe_1
```

The script to create this company and populate all employee data exists here: `docker/entrypoint.sh`


The default docker-compose.yml file launches the application at: `localhost:8000`

> Note: If you prefer using Docker, refer to the original documentation.

#### Stop the hrms app
```
podman-compose down
```

### DB Access

To verify a clean start, log-in into the docker_mariadb_1 container, password is `123`.

```
podman exec -it docker_mariadb_1 mysql -u root -p
```

Only one user database should exist. The database ID is generated per setup — in this example it is `_3ba7b06c3cb19463`, but yours will differ.

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

Execute the following queries (`USE` command takes time). The output should show: 107 employees, 109 users (Administrator and Guest + 107 employees), and 1 company named `NovaSoft`.

```
USE _3ba7b06c3cb19463;
SELECT COUNT(*) FROM tabEmployee;
SELECT COUNT(*) FROM tabUser;
SELECT name FROM tabCompany;
```

### Adding / Updating / Deleting data in running container for development purposes

For adding or updating data, modify the demo data locally and copy updated to container,

```
podman cp hrms/demo_data/. docker_frappe_1:/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/
```


If you need to clean(remove) the attendance data for development purposes use:
```
podman exec -it docker_frappe_1 bash -c 'bench --site hrms.localhost execute hrms.demo_data.attendance_setup.clear_attendance_data --kwargs "{\"company\": \"NovaSoft\", \"attendance_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employee_attendance.json\"}"'
```

<!-- TODO: Re-add clear_recruitment_data once recruitment cleanup is reworked without raw SQL -->
<!-- To clear recruitment data for development purposes:
podman exec -it docker_frappe_1 bash -c 'bench --site hrms.localhost execute hrms.demo_data.recruitment_setup.clear_recruitment_data --kwargs "{\"company\": \"NovaSoft\"}"'
-->

To clear performance data for development purposes:
```
podman exec -it docker_frappe_1 bash -c 'bench --site hrms.localhost execute hrms.demo_data.performance_setup.clear_performance_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

To clear tenure data for development purposes:
```
podman exec -it docker_frappe_1 bash -c 'bench --site hrms.localhost execute hrms.demo_data.tenure_setup.clear_tenure_data --kwargs "{\"company\": \"NovaSoft\"}"'
```

If you need to clean the leaves data for development purposes use:
```
podman exec -it docker_frappe_1 bash -c 'bench --site hrms.localhost execute hrms.demo_data.leaves_setup.clear_leave_configuration --kwargs "{\"company\": \"NovaSoft\", \"leaves_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employee_leaves.json\"}"'
```

To clear payroll data for development purposes:
```
podman exec -it docker_frappe_1 bash -c 'bench --site hrms.localhost execute hrms.demo_data.payroll_setup.clear_payroll_data --kwargs "{\"company\": \"NovaSoft\", \"payroll_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employee_payroll.json\"}"'
```

To clear expense claims data for development purposes:
```
podman exec -it docker_frappe_1 bash -c 'bench --site hrms.localhost execute hrms.demo_data.expense_claims_setup.clear_expense_claims_data --kwargs "{\"company\": \"NovaSoft\", \"data_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/expense_claims_data.json\"}"'
```

## Verifying Data in the App

Navigate to `http://localhost:8000/app`, select the `NovaSoft` company, and confirm that the employees and related records have been created.

Log in using the `Administrator` user, an HR user, and another user to check access and permission to transactions.

## UI troubleshooting

* The UI displays the setup wizard and does not offer an option to skip it the first time you log in, go through it and create a new `test` company.
* If you are not logged as Administrator, the impersonation feature might be active. Simply log-off and log-in again.

## Contributing / Git Workflow

```
git checkout blue-develop
git pull origin blue-develop
git checkout -b feature/my-db-updates
# ... make changes ... or git stash pop # to recover uncommitted updates (if needed)
git add .
git commit -m "feat: description"
git push origin feature/my-db-updates
```

Then, create a PR on GitHub

- base: blue-develop
- compare: feature/my-db-updates
- assign a reviewer to your PR