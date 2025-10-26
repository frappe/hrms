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

    # Ensure the site is set as current site
    echo "${SITE_NAME}" > sites/currentsite.txt
    bench use ${SITE_NAME}
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

# Check if assets need to be built (they should already exist from Docker image)
echo "========================================="
echo "ASSET CHECK"
echo "========================================="

if [ -d "sites/assets/frappe/dist" ] && [ "$(ls -A sites/assets/frappe/dist/css 2>/dev/null)" ] && [ -f "sites/assets/frappe/icons/timeless/icons.svg" ]; then
    echo "✓ Assets already exist and are complete (including icons)"
    echo "Skipping asset build for faster startup..."
    echo ""
    echo "Sample CSS files:"
    ls -lh sites/assets/frappe/dist/css/*.css 2>/dev/null | head -2
    echo ""
    echo "Icons verified:"
    ls sites/assets/frappe/icons/ 2>/dev/null | head -3
else
    echo "⚠ Assets incomplete or missing, building now..."

    # CRITICAL: First copy all static assets from app public folders
    echo "Copying static assets (icons, fonts, images)..."
    mkdir -p sites/assets
    for app in frappe erpnext hrms; do
        if [ -d "apps/$app/$app/public" ]; then
            echo "  - Copying $app static assets..."
            cp -r apps/$app/$app/public sites/assets/$app
        fi
    done

    # Then build the JS/CSS bundles
    echo "Building production JS/CSS bundles..."
    bench build --production --hard-link --force
    echo "Assets built successfully!"

    # Ensure assets are readable by nginx
    echo "Setting asset permissions..."
    chmod -R 755 sites/assets
    find sites/assets -type f -exec chmod 644 {} \;
    echo "Permissions set!"
fi

echo ""
echo "Assets path: $(pwd)/sites/assets"
echo "========================================="

# Start bench with the updated configuration
echo "Starting bench..."
bench start