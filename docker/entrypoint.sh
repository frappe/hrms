#!/bin/bash
cd /home/frappe/frappe-bench

# Wait for MariaDB to be ready
until mysqladmin ping -h"mariadb" --silent; do
    echo "Waiting for MariaDB..."
    sleep 2
done

# Create site if it doesn't exist
if [ ! -d "sites/hrms.localhost" ]; then
    bench new-site hrms.localhost \
        --force \
        --mariadb-root-password 123 \
        --admin-password admin \
        --no-mariadb-socket
    
    bench --site hrms.localhost install-app hrms
    bench --site hrms.localhost set-config developer_mode 1
    bench --site hrms.localhost enable-scheduler
    bench --site hrms.localhost clear-cache
    bench use hrms.localhost
fi

# Create employee roster
bench --site hrms.localhost execute hrms.demo_data.company_setup.create_demo_data --kwargs "{\"company\": \"NovaSoft\", \"abbr\": \"NS\", \"roster_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employees_roster.json\"}"
# Adding Attendance Data 
bench --site hrms.localhost execute hrms.demo_data.attendance_setup.create_attendance_data --kwargs "{\"company\": \"NovaSoft\", \"attendance_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employee_attendance.json\"}"
# Adding Recruitment Data
bench --site hrms.localhost execute hrms.demo_data.recruitment_setup.create_recruitment_data --kwargs "{\"company\": \"NovaSoft\"}"
# Adding Performance Management Data
bench --site hrms.localhost execute hrms.demo_data.performance_setup.create_performance_data --kwargs "{\"company\": \"NovaSoft\"}"
# Adding Employee Lifecycle (Tenure) Data 
bench --site hrms.localhost execute hrms.demo_data.tenure_setup.create_tenure_data --kwargs "{\"company\": \"NovaSoft\"}"
# Adding Leaves Management Data
bench --site hrms.localhost execute hrms.demo_data.leaves_setup.configure_leave_management --kwargs "{\"company\": \"NovaSoft\", \"leaves_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employee_leaves.json\"}"
# Adding Payroll Data 
bench --site hrms.localhost execute hrms.demo_data.payroll_setup.create_payroll_data --kwargs "{\"company\": \"NovaSoft\", \"payroll_path\": \"/home/frappe/frappe-bench/apps/hrms/hrms/demo_data/employee_payroll.json\"}"


bench start
