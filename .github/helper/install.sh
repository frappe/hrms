#!/bin/bash

set -eo pipefail

export PATH="$HOME/pilot/bin:$HOME/.local/bin:$PATH"
export UV_PYTHON="${UV_PYTHON:-3.14}"
if [ -n "${GITHUB_PATH:-}" ]; then
    printf '%s\n' "$HOME/pilot/bin" "$HOME/.local/bin" >> "$GITHUB_PATH"
fi

githubbranch=${GITHUB_BASE_REF:-${GITHUB_REF##*/}}
frappeuser=${FRAPPE_USER:-"frappe"}

resolve_branch() {
    local repo="$1" candidate="$2"
    if [ -n "$candidate" ] && git ls-remote --exit-code --heads "https://github.com/${frappeuser}/${repo}" "$candidate" >/dev/null 2>&1; then
        echo "$candidate"
    else
        echo "develop"
    fi
}

frappebranch="$(resolve_branch frappe "${FRAPPE_BRANCH:-$githubbranch}")"
erpnextbranch="$(resolve_branch erpnext "${ERPNEXT_BRANCH:-$githubbranch}")"
paymentsbranch="$(resolve_branch payments "${PAYMENTS_BRANCH:-${githubbranch%"-hotfix"}}")"
lendingbranch="develop"

install_whktml() {
    wget -q -O /tmp/wkhtmltox.tar.xz https://github.com/frappe/wkhtmltopdf/raw/master/wkhtmltox-0.12.3_linux-generic-amd64.tar.xz
    tar -xf /tmp/wkhtmltox.tar.xz -C /tmp
    sudo mv /tmp/wkhtmltox/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf
    sudo chmod o+x /usr/local/bin/wkhtmltopdf
}
install_whktml &
wkhtml_pid=$!

curl -fsSL https://raw.githubusercontent.com/frappe/pilot/develop/install.sh | sh -s -- --ci

pilot new frappe-bench --frappe-branch "${frappebranch}"
pilot -b frappe-bench set-bench-config python "3.14"
pilot -b frappe-bench set-bench-config admin_allow_site_to_pilot_communication false
pilot -b frappe-bench set-bench-config watch_apps_js false
pilot -b frappe-bench set-bench-config mariadb_existing true
pilot -b frappe-bench set-bench-config mariadb_host 127.0.0.1
pilot -b frappe-bench set-bench-config mariadb_port 3306
pilot -b frappe-bench set-bench-config mariadb_admin_user root
pilot -b frappe-bench set-bench-config mariadb_password root
pilot -b frappe-bench init

printf '[client]\nskip-ssl\n' > ~/.my.cnf
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL character_set_server = 'utf8mb4'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"

cd "$HOME/pilot/benches/frappe-bench" || exit 1

uv pip install --python env/bin/python -e "apps/frappe[test]"
pilot get-app "https://github.com/${frappeuser}/payments" --branch "$paymentsbranch" --skip-assets
pilot get-app "https://github.com/${frappeuser}/erpnext" --branch "$erpnextbranch" --skip-assets
pilot get-app "https://github.com/${frappeuser}/lending" --branch "$lendingbranch" --skip-assets
pilot get-app "${GITHUB_WORKSPACE}" --skip-assets

pilot -b frappe-bench start > "${RUNNER_TEMP:-/tmp}/pilot.log" 2>&1 &
curl --fail --silent --show-error --retry 30 --retry-connrefused --retry-delay 1 \
    http://127.0.0.1:7000/api/v1/health

pilot build --apps frappe
pilot build --apps hrms --force

if [ "${SKIP_SITE_SETUP:-0}" != "1" ]; then
    pilot new-site test_site --admin-password admin --apps frappe payments erpnext lending hrms --skip-assets
    pilot frappe --site test_site set-config -p allow_tests True
    pilot frappe --site test_site set-config -p use_mysqlclient 1
    pilot frappe --site test_site set-config host_name "http://test_site:8000"
    pilot frappe --site test_site set-config auto_email_id "test@example.com"
    pilot frappe --site test_site set-config mail_server "smtp.example.com"
    pilot frappe --site test_site set-config mail_login "test@example.com"
    pilot frappe --site test_site set-config mail_password "test"
    pilot frappe --site test_site set-config -p throttle_user_limit 100
fi

wait "$wkhtml_pid"
