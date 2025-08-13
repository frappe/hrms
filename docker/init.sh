#!/usr/bin/env bash
set -euo pipefail

cd /home/frappe

# If a bench folder exists, don't try to re-init; just fix perms and start
if [ -d "frappe-bench" ]; then
  echo ">> Bench already exists; fixing permissions and starting..."
  cd frappe-bench
  mkdir -p logs sites

  # Create Procfile if it doesn't exist
  if [ ! -f "Procfile" ]; then
    echo ">> Creating Procfile..."
    cat > Procfile <<EOF
web: bench serve --port 8000
schedule: bench schedule
socketio: node apps/frappe/socketio.js
EOF
    chmod 664 Procfile
  fi
  # ensure current user (likely 'frappe') can write logs & sites
  chmod -R u+rwX,g+rwX logs sites || true
  # if logs were created as root in a previous attempt, force reset:
  if ! touch logs/.perm_test 2>/dev/null; then
    echo ">> Resetting ownership on logs/sites..."
    chown -R "$(id -u)":"$(id -g)" logs sites || true
  else
    rm -f logs/.perm_test
  fi
  exec bench start
fi

echo ">> Creating new bench..."
bench init --skip-redis-config-generation --skip-assets --frappe-branch version-15 frappe-bench

cd frappe-bench

echo ">> Pointing services at docker hosts..."
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

# Create a minimal Procfile
echo ">> Creating Procfile..."
cat > Procfile <<EOF
web: bench serve --port 8000
schedule: bench schedule
socketio: node apps/frappe/socketio.js
EOF
chmod 664 Procfile


# Create a minimal Procfile

bench get-app hrms

echo ">> Creating site hrms.localhost ..."
bench new-site hrms.localhost --force --mariadb-root-password 123 --admin-password admin --no-mariadb-socket
bench --site hrms.localhost install-app hrms
bench --site hrms.localhost set-config developer_mode 1
bench --site hrms.localhost enable-scheduler
bench --site hrms.localhost clear-cache
bench use hrms.localhost

bench build --apps frappe || true
exec bench start
