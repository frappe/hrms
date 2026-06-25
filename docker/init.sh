#!/bin/bash
set -e

export PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}"
export GIT_TERMINAL_PROMPT=0
export CI=1

BENCH_DIR="/home/frappe/frappe-bench"
APPS_TXT="${BENCH_DIR}/sites/apps.txt"
COMMON_SITE_CONFIG="${BENCH_DIR}/sites/common_site_config.json"

# Named volume mounts are created root-owned, but we run as the frappe user.
# Take ownership so bench can create directories inside the volume.
if [ -d "${BENCH_DIR}" ] && [ ! -w "${BENCH_DIR}" ]; then
	echo "Fixing ownership of ${BENCH_DIR}..."
	sudo chown -R "$(id -u):$(id -g)" "${BENCH_DIR}" || true
fi

if ! command -v bench >/dev/null 2>&1 || ! bench --version >/dev/null 2>&1; then
	echo "bench CLI missing or broken; installing frappe-bench..."
	pip install --user frappe-bench
	export PATH="/home/frappe/.local/bin:${PATH}"
fi

# Reduce flaky git clone failures inside Docker (HTTP/2 stream resets, TLS drops, etc.)
git config --global http.version HTTP/1.1
git config --global http.postBuffer 524288000
git config --global core.compression 0

clean_yarn_cache() {
	echo "Clearing corrupted yarn cache..."
	rm -rf /home/frappe/.cache/yarn
	yarn cache clean --force >/dev/null 2>&1 || true
}

retry() {
	local max_attempts=$1
	shift
	local attempt=1

	until "$@"; do
		if [ "$attempt" -ge "$max_attempts" ]; then
			return 1
		fi
		echo "Command failed (attempt ${attempt}/${max_attempts}), retrying in 20s..."
		clean_yarn_cache
		sleep 20
		attempt=$((attempt + 1))
	done
}

is_app_on_bench() {
	local app=$1
	[ -f "${APPS_TXT}" ] && grep -qxF "${app}" "${APPS_TXT}"
}

is_app_healthy() {
	local app=$1
	[ -f "${BENCH_DIR}/apps/${app}/${app}/__init__.py" ]
}

is_bench_healthy() {
	is_app_healthy frappe && [ -f "${COMMON_SITE_CONFIG}" ]
}

clear_bench_contents() {
	if [ ! -d "${BENCH_DIR}" ]; then
		return 0
	fi

	echo "Clearing broken or partial bench contents..."
	# The bench path is a Docker volume mount and cannot be removed itself.
	find "${BENCH_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
}

init_bench() {
	clear_bench_contents
	echo "Creating new bench..."
	bench init --skip-redis-config-generation --ignore-exist frappe-bench
}

reset_bench_app() {
	local app=$1

	echo "Resetting broken ${app} installation..."
	if is_app_on_bench "${app}"; then
		bench remove-app "${app}" --force --no-backup || true
	fi

	rm -rf "${BENCH_DIR}/apps/${app}"
	rm -rf "${BENCH_DIR}/apps/frappe/${app}"
}

ensure_bench_app() {
	local app=$1
	shift
	local extra_args=("$@")

	if is_app_on_bench "${app}" && is_app_healthy "${app}"; then
		echo "${app} already installed on bench, skipping get-app"
		return 0
	fi

	clean_yarn_cache

	if is_app_on_bench "${app}" || [ -d "${BENCH_DIR}/apps/${app}" ]; then
		reset_bench_app "${app}"
	fi

	retry 5 bench get-app --overwrite "${extra_args[@]}" "${app}"
}

site_has_app() {
	local site=$1
	local app=$2
	bench --site "${site}" list-apps 2>/dev/null | grep -qxF "${app}"
}

# The GitHub hrms clone does not know about our locally-developed module, so
# make sure it is registered in modules.txt (idempotent) before install/migrate.
ensure_module_registered() {
	local modules_txt="${BENCH_DIR}/apps/hrms/hrms/modules.txt"
	local module="Organization Structure"

	if [ -f "${modules_txt}" ] && ! grep -qxF "${module}" "${modules_txt}"; then
		echo "Registering '${module}' in modules.txt..."
		# Ensure the file ends with a newline before appending.
		[ -n "$(tail -c1 "${modules_txt}")" ] && echo "" >>"${modules_txt}"
		echo "${module}" >>"${modules_txt}"
	fi
}

if ! is_bench_healthy; then
	retry 5 init_bench
fi

if ! is_bench_healthy; then
	echo "ERROR: Bench setup failed; frappe is not ready."
	exit 1
fi

cd "${BENCH_DIR}"

# Use containers instead of localhost
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

# Remove redis, watch from Procfile
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile

# Install erpnext first; do not use --resolve-deps for hrms because it
# incorrectly looks for frappe/erpnext at apps/frappe/erpnext/.
ensure_bench_app erpnext
ensure_bench_app hrms
ensure_module_registered

if [ ! -d "${BENCH_DIR}/sites/hrms.localhost" ]; then
	bench new-site hrms.localhost \
		--force \
		--mariadb-root-password 123 \
		--admin-password admin \
		--no-mariadb-socket
fi

if ! site_has_app hrms.localhost erpnext; then
	bench --site hrms.localhost install-app erpnext
fi

if ! site_has_app hrms.localhost hrms; then
	bench --site hrms.localhost install-app hrms
fi

bench --site hrms.localhost set-config developer_mode 1
bench --site hrms.localhost enable-scheduler

# Sync host-side changes to the bind-mounted module (doctypes, reports,
# workspace, number cards) on every startup. clear-cache first so the
# module-to-app map is rebuilt before migrate runs.
bench --site hrms.localhost clear-cache
bench --site hrms.localhost migrate
bench --site hrms.localhost clear-cache

bench use hrms.localhost

bench start
