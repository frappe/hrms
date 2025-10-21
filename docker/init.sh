#!/bin/bash

# Wait for MariaDB to be ready
echo "Waiting for MariaDB to be ready..."
until mysql -h mariadb -u root -p${MYSQL_ROOT_PASSWORD} -e "SELECT 1" &>/dev/null; do
    echo "MariaDB is unavailable - sleeping"
    sleep 2
done
echo "MariaDB is up and ready!"

cd /home/frappe/frappe-bench

# Check if site already exists
if [ -d "sites/${SITE_NAME}" ]; then
    echo "Site ${SITE_NAME} already exists, starting bench..."
    bench start
    exit 0
fi

echo "Creating new site: ${SITE_NAME}..."

# Create new site
bench new-site ${SITE_NAME} \
--force \
--mariadb-root-password ${MYSQL_ROOT_PASSWORD} \
--admin-password ${ADMIN_PASSWORD} \
--no-mariadb-socket

# Install and configure HRMS app
bench --site ${SITE_NAME} install-app hrms
bench --site ${SITE_NAME} set-config developer_mode 1
bench --site ${SITE_NAME} enable-scheduler
bench --site ${SITE_NAME} clear-cache
bench use ${SITE_NAME}

echo "Site created successfully, starting bench..."
bench start