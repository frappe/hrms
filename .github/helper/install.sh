#!/bin/bash

set -e

cd ~ || exit

githubbranch=${GITHUB_BASE_REF:-${GITHUB_REF##*/}}
frappeuser=${FRAPPE_USER:-"frappe"}
frappebranch=${FRAPPE_BRANCH:-$githubbranch}
erpnextbranch=${ERPNEXT_BRANCH:-$githubbranch}
paymentsbranch=${PAYMENTS_BRANCH:-${githubbranch%"-hotfix"}}
lendingbranch="develop"

# ---------------------------------------------------------------------------
# Phase 1 — parallelise every slow, independent setup step:
#   a) system packages   b) frappe-bench pip install
#   c) shallow git clone of frappe and all dependency apps
#
# The dependency apps (frappe, payments, erpnext, lending) are cloned here
# --depth 1 instead of letting `bench get-app` fetch them later. erpnext in
# particular has a multi-GB history; a sequential full clone over the network
# was the main reason hrms CI install ran ~2x slower than erpnext's. Phase 2
# then installs them from these local checkouts, so no network re-clone.
# ---------------------------------------------------------------------------

sudo apt update

# apt remove/install must run sequentially but can overlap with pip and clones.
sudo apt remove mysql-server mysql-client
sudo apt install libcups2-dev redis-server mariadb-client libmariadb-dev &
apt_pid=$!

pip install frappe-bench &
pip_pid=$!

git clone "https://github.com/${frappeuser}/frappe" --branch "${frappebranch}" --depth 1 &
frappe_pid=$!

git clone "https://github.com/${frappeuser}/payments" --branch "${paymentsbranch}" --depth 1 &
payments_pid=$!

git clone "https://github.com/${frappeuser}/erpnext" --branch "${erpnextbranch}" --depth 1 &
erpnext_pid=$!

git clone "https://github.com/${frappeuser}/lending" --branch "${lendingbranch}" --depth 1 &
lending_pid=$!

wait $apt_pid
wait $pip_pid
wait $frappe_pid
wait $payments_pid
wait $erpnext_pid
wait $lending_pid

bench init --skip-assets --frappe-path ~/frappe --python "$(which python)" frappe-bench

mkdir ~/frappe-bench/sites/test_site
cp -r "${GITHUB_WORKSPACE}/.github/helper/site_config.json" ~/frappe-bench/sites/test_site/

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL character_set_server = 'utf8mb4'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"

# Belt-and-suspenders: also set performance variables at runtime in case
# MARIADB_EXTRA_FLAGS was not honoured by the container image.
mariadb --host 127.0.0.1 --port 3306 -u root -proot \
    -e "SET GLOBAL innodb_flush_log_at_trx_commit=0; SET GLOBAL sync_binlog=0;"

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "CREATE USER 'test_frappe'@'localhost' IDENTIFIED BY 'test_frappe'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "CREATE DATABASE test_frappe"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "GRANT ALL PRIVILEGES ON \`test_frappe\`.* TO 'test_frappe'@'localhost'"

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "FLUSH PRIVILEGES"

install_whktml() {
    # Re-use the tarball if the wkhtmltopdf cache step already restored it.
    if [ ! -f /tmp/wkhtmltox.tar.xz ]; then
        wget -O /tmp/wkhtmltox.tar.xz https://github.com/frappe/wkhtmltopdf/raw/master/wkhtmltox-0.12.3_linux-generic-amd64.tar.xz
    fi
    tar -xf /tmp/wkhtmltox.tar.xz -C /tmp
    sudo mv /tmp/wkhtmltox/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf
    sudo chmod o+x /usr/local/bin/wkhtmltopdf
}
install_whktml &

cd ~/frappe-bench || exit

sed -i 's/watch:/# watch:/g' Procfile
sed -i 's/schedule:/# schedule:/g' Procfile
sed -i 's/socketio:/# socketio:/g' Procfile
sed -i 's/redis_socketio:/# redis_socketio:/g' Procfile

# Install from the local checkouts cloned in Phase 1 (no network re-clone).
bench get-app payments ~/payments
bench get-app erpnext ~/erpnext --resolve-deps
bench get-app lending ~/lending
bench get-app hrms "${GITHUB_WORKSPACE}"
bench setup requirements --dev

bench start &>> ~/frappe-bench/bench_start.log &
CI=Yes bench build --app frappe &
bench --site test_site reinstall --yes

bench --verbose --site test_site install-app lending
bench --verbose --site test_site install-app hrms
