#!/bin/bash
set -e

BENCH_DIR="/home/frappe/frappe-bench"

# Toolchain versions come straight from what frappe's develop branch declares:
#   frappe/pyproject.toml -> requires-python = ">=3.14,<3.15"
#   frappe/package.json   -> engines.node    = ">=24"
# The frappe/bench image lags behind both (3.11 / 20.x), which makes `pip install
# -e apps/frappe` die with a SyntaxError on frappe's PEP 695 `type` aliases, so
# provision the interpreters here when they are missing.
REQUIRED_PYTHON="3.14"
REQUIRED_NODE="24"

setup_node() {
    set +e
    . "${NVM_DIR}/nvm.sh"
    set -e

    if ! nvm which "$REQUIRED_NODE" >/dev/null 2>&1; then
        echo "Installing Node ${REQUIRED_NODE} (image ships $(node -v))..."
        nvm install "$REQUIRED_NODE"
    fi

    # `nvm use` loses against the PATH baked into the image, so prepend explicitly.
    # The alias is for shells opened later via `docker compose exec`.
    nvm alias default "$REQUIRED_NODE" >/dev/null
    export PATH="$(dirname "$(nvm which "$REQUIRED_NODE")"):${PATH}"

    command -v yarn >/dev/null 2>&1 || npm install -g yarn
}

setup_python() {
    if command -v "python${REQUIRED_PYTHON}" >/dev/null 2>&1; then
        PYTHON_BIN="$(command -v "python${REQUIRED_PYTHON}")"
        return
    fi

    # The uv bundled in the image is old enough that it only resolves 3.14
    # pre-releases, so refresh it before asking for an interpreter.
    export UV_INSTALL_DIR="${HOME}/.local/bin"
    curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null
    export PATH="${UV_INSTALL_DIR}:${PATH}"

    echo "Installing Python ${REQUIRED_PYTHON}..."
    uv python install "$REQUIRED_PYTHON"
    PYTHON_BIN="$(uv python find "$REQUIRED_PYTHON")"
}

setup_node

if [ -d "${BENCH_DIR}/apps/frappe" ]; then
    echo "Bench already exists, starting bench..."
    cd "$BENCH_DIR"

    # Ensure socket.io dependencies are installed
    if [ ! -d "./apps/frappe/node_modules/socket.io" ]; then
        echo "Installing Node modules for Frappe realtime..."
        (cd ./apps/frappe && yarn install)
    fi

    exec bench start
fi

setup_python

# The frappe-bench named volume mounts root-owned until something writes to it.
if [ -d "$BENCH_DIR" ] && [ ! -w "$BENCH_DIR" ]; then
    sudo chown "$(id -u):$(id -g)" "$BENCH_DIR"
fi

echo "Creating new bench with $("$PYTHON_BIN" -V) and $(node -v)..."

# --ignore-exist: the volume mount means the target directory is already there
bench init --skip-redis-config-generation --ignore-exist --python "$PYTHON_BIN" frappe-bench

cd frappe-bench

# Use containers instead of localhost
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

# Remove redis, watch from Procfile
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile

if [ ! -d "apps/erpnext" ]; then
    bench get-app erpnext
fi

if [ ! -d "apps/hrms" ]; then
    # Prefer the checkout bind-mounted at /workspace over a fresh clone
    if [ -f "/workspace/hrms/__init__.py" ]; then
        bench get-app /workspace
    else
        bench get-app hrms
    fi
fi

# Ensure yarn dependencies are installed for socket.io realtime server
(cd apps/frappe && yarn install)

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

exec bench start
