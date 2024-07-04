#!/bin/bash
set -e
cd ~ || exit

echo "Setting Up Bench..."

pip install frappe-bench
bench -v init frappe-bench --skip-assets --skip-redis-config-generation --python "$(which python)" --frappe-branch "${BASE_BRANCH}"
cd ./frappe-bench || exit

echo "Get HRMS..."
bench get-app --skip-assets hrms "${GITHUB_WORKSPACE}"

echo "Generating POT file..."
bench generate-pot-file --app hrms

cd ./apps/hrms || exit

echo "Configuring git user..."
git config user.email "developers@erpnext.com"
git config user.name "frappe-pr-bot"

echo "Setting the correct git remote..."
# Here, the git remote is a local file path by default. Let's change it to the upstream repo.
git remote set-url upstream https://github.com/frappe/hrms.git

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
