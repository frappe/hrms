#!/bin/bash

set -e

cd ~ || exit

sudo apt update
sudo apt remove mysql-server mysql-client
sudo apt install libcups2-dev redis-server mariadb-client libmariadb-dev

pip install frappe-bench

githubbranch=${GITHUB_BASE_REF:-${GITHUB_REF##*/}}
frappeuser=${FRAPPE_USER:-"frappe"}
frappebranch=${FRAPPE_BRANCH:-$githubbranch}
erpnextbranch=${ERPNEXT_BRANCH:-$githubbranch}
paymentsbranch=${PAYMENTS_BRANCH:-${githubbranch%"-hotfix"}}
lendingbranch="develop"

git clone "https://github.com/${frappeuser}/frappe" --branch "${frappebranch}" --depth 1
bench init --skip-assets --frappe-path ~/frappe --python "$(which python)" frappe-bench

mkdir ~/frappe-bench/sites/test_site
cp -r "${GITHUB_WORKSPACE}/.github/helper/site_config.json" ~/frappe-bench/sites/test_site/

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL character_set_server = 'utf8mb4'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "CREATE USER 'test_frappe'@'localhost' IDENTIFIED BY 'test_frappe'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "CREATE DATABASE test_frappe"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "GRANT ALL PRIVILEGES ON \`test_frappe\`.* TO 'test_frappe'@'localhost'"

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "FLUSH PRIVILEGES"

install_whktml() {
    local arch os_like wkhtml_package

    arch="$(dpkg --print-architecture)"
    os_like="$(. /etc/os-release && printf '%s %s' "$ID" "$ID_LIKE")"

    if echo "$os_like" | grep -Eq '(^| )ubuntu( |$)'; then
        wkhtml_package="wkhtmltox_0.12.6.1-3.jammy_${arch}.deb"
    elif echo "$os_like" | grep -Eq '(^| )debian( |$)'; then
        wkhtml_package="wkhtmltox_0.12.6.1-3.bookworm_${arch}.deb"
    fi

    if [ -n "$wkhtml_package" ]; then
        wget -O "/tmp/${wkhtml_package}" "https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/${wkhtml_package}"
        sudo apt install -y xvfb xfonts-75dpi xfonts-base "/tmp/${wkhtml_package}"
        return
    fi

    wget -O /tmp/wkhtmltox.tar.xz https://github.com/frappe/wkhtmltopdf/raw/master/wkhtmltox-0.12.3_linux-generic-amd64.tar.xz
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

bench get-app "https://github.com/${frappeuser}/payments" --branch "$paymentsbranch"
bench get-app "https://github.com/${frappeuser}/erpnext" --branch "$erpnextbranch" --resolve-deps
bench get-app "https://github.com/${frappeuser}/lending" --branch "$lendingbranch"
bench get-app hrms "${GITHUB_WORKSPACE}"
bench setup requirements --dev

bench start &>> ~/frappe-bench/bench_start.log &
CI=Yes bench build --app frappe &
bench --site test_site reinstall --yes

bench --verbose --site test_site install-app lending
bench --verbose --site test_site install-app hrms
