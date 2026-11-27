#!/bin/bash
set -euo pipefail

BENCH_NAME="frappe-bench"
BENCH_PATH="$HOME/pilot/benches/$BENCH_NAME"
export PATH="$HOME/pilot/bin:$HOME/.local/bin:$PATH"

cleanup() {
    pilot -b "$BENCH_NAME" stop >/dev/null 2>&1 || true
}
trap cleanup EXIT

cd ~

echo "Setting Up Pilot..."

curl -fsSL https://raw.githubusercontent.com/frappe/pilot/develop/install.sh | sh -s -- --ci

pilot new "$BENCH_NAME" --frappe-branch "$BASE_BRANCH" --database sqlite
pilot -b "$BENCH_NAME" init --skip-frontend --no-dev

echo "Get ERPNext..."
pilot get-app https://github.com/frappe/erpnext --branch "$BASE_BRANCH" --skip-assets

echo "Get HRMS..."
pilot get-app "$GITHUB_WORKSPACE" --branch "$BASE_BRANCH" --skip-assets

echo "Generating POT file..."
pilot frappe generate-pot-file --app hrms

cd "$BENCH_PATH/apps/hrms"

echo "Configuring git user..."
git config user.email "developers@erpnext.com"
git config user.name "frappe-pr-bot"

echo "Setting the correct git remote..."
git remote remove upstream 2>/dev/null || true
git remote add upstream https://github.com/frappe/hrms.git

echo "Creating a new branch..."
isodate=$(date -u +"%Y-%m-%d")
branch_name="pot_${BASE_BRANCH}_${isodate}"
git checkout -b "${branch_name}"

echo "Commiting changes..."
git add hrms/locale/main.pot
git commit -m "chore: update POT file"

gh auth setup-git
git push -u upstream "${branch_name}"

echo "Creating a PR..."
gh pr create --fill --base "${BASE_BRANCH}" --head "${branch_name}" -R frappe/hrms
