#!/bin/bash

# Wait for MariaDB to be ready
echo "Waiting for MariaDB to be ready..."
until mysql -h mariadb -u root -p${MYSQL_ROOT_PASSWORD} -e "SELECT 1" &>/dev/null; do
    echo "MariaDB is unavailable - sleeping"
    sleep 2
done
echo "MariaDB is up and ready!"

cd /home/frappe/frappe-bench

# Configure Procfile to use Gunicorn instead of development server
echo "Configuring production web server (Gunicorn)..."

# Ensure logs directory exists
mkdir -p /home/frappe/frappe-bench/logs

# Update Procfile to use Gunicorn with proper working directory
sed -i 's|web: bench serve.*|web: sh -c "cd /home/frappe/frappe-bench/sites \&\& /home/frappe/frappe-bench/env/bin/gunicorn -b 0.0.0.0:8000 -w 4 --max-requests 5000 --max-requests-jitter 500 -t 120 --graceful-timeout 30 frappe.app:application"|' Procfile

# Check if site already exists
if [ -d "sites/${SITE_NAME}" ]; then
    echo "Site ${SITE_NAME} already exists, starting bench..."
else

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

echo "Site created successfully!"
fi

# Build production assets with hard links for nginx access
echo "Building production assets..."
bench build --production --hard-link --force
echo "Assets built successfully!"

# Ensure assets are readable by nginx (fix permissions)
echo "Setting asset permissions for nginx access..."
chmod -R 755 sites/assets
find sites/assets -type f -exec chmod 644 {} \;
echo "Permissions set!"

# Verify assets were created
echo "========================================="
echo "ASSET VERIFICATION"
echo "========================================="
if [ -d "sites/assets/frappe/dist" ]; then
    echo "✓ Assets verified: frappe/dist directory exists"
    echo "Sample CSS files:"
    ls -lh sites/assets/frappe/dist/css/*.css 2>/dev/null | head -2
    echo ""
    echo "Sample JS files:"
    ls -lh sites/assets/frappe/dist/js/*.js 2>/dev/null | head -2
    echo ""
    echo "Assets path: $(pwd)/sites/assets"
else
    echo "✗ WARNING: Assets directory not found!"
    echo "Expected location: $(pwd)/sites/assets/frappe/dist"
fi
echo "========================================="

# Start bench with the updated configuration
echo "Starting bench..."
bench start