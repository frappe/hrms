import json
import random

import frappe
from frappe import _
from frappe.utils import add_days, getdate


def setup_expense_claim_type_accounts():
	companies = frappe.get_all("Company", fields=["name"])
	if not companies:
		return

	company = None
	for c in companies:
		if "Sparrow" in c.name:
			company = c.name
			break
	if not company:
		company = companies[0].name

	accounts = frappe.get_all(
		"Account",
		filters={"company": company, "is_group": 0},
		pluck="name",
	)

	if not accounts:
		return

	account_map = {}
	for acc in accounts:
		acc_lower = acc.lower()
		if "travel" in acc_lower:
			account_map["Travel"] = acc
		elif "food" in acc_lower or "accommodation" in acc_lower:
			account_map["Food"] = acc
		elif "medical" in acc_lower:
			account_map["Medical"] = acc
		elif "misc" in acc_lower or "other" in acc_lower:
			account_map["Others"] = acc
		elif "call" in acc_lower or "communication" in acc_lower:
			account_map["Calls"] = acc

	expense_types_needed = ["Calls", "Food", "Medical"]
	for exp_type in expense_types_needed:
		if exp_type not in account_map and accounts:
			account_map[exp_type] = accounts[0]

	for exp_type, default_account in account_map.items():
		if not frappe.db.exists("Expense Claim Type", exp_type):
			continue

		ect = frappe.get_doc("Expense Claim Type", exp_type)

		has_account = False
		for acc in ect.accounts:
			if acc.company == company:
				acc.default_account = default_account
				has_account = True
				break

		if not has_account:
			ect.append("accounts", {"company": company, "default_account": default_account})

		ect.save(ignore_permissions=True)


def setup_expense_claims():
	from frappe.desk.page.setup_wizard.setup_wizard import make_records

	companies = frappe.get_all("Company", fields=["name"])
	if not companies:
		frappe.publish_realtime("demo_progress", {"message": "No companies found, skipping expense claims"})
		return

	company = None
	for c in companies:
		if "Sparrow" in c.name:
			company = c.name
			break
	if not company:
		company = companies[0].name

	records = get_records_from_json("Expense Claim")
	if not records:
		frappe.publish_realtime("demo_progress", {"message": "No expense claims found in JSON"})
		return

	# Get employees with their reports_to for approver mapping
	employees = frappe.get_all(
		"Employee",
		filters={"company": company, "status": "Active"},
		fields=["name", "employee_name", "reports_to", "user_id"],
	)

	employee_name_to_id = {emp.employee_name: emp.name for emp in employees}
	reports_to_map = {emp.name: emp.reports_to for emp in employees}

	processed_records = []
	for record in records:
		employee_name = record.get("employee")
		if employee_name not in employee_name_to_id:
			continue

		employee_id = employee_name_to_id[employee_name]

		# Set employee ID
		processed_record = record.copy()
		processed_record["employee"] = employee_id
		processed_record["company"] = company
		processed_record["exchange_rate"] = 1
		processed_record["currency"] = "USD"

		# Get payable account
		payable_accounts = frappe.get_all(
			"Account",
			filters={"company": company, "account_type": "Payable", "is_group": 0},
			pluck="name",
			limit=1,
		)
		if payable_accounts:
			processed_record["payable_account"] = payable_accounts[0]

		# Set expense approver from reports_to
		manager = reports_to_map.get(employee_id)
		if manager:
			manager_user = frappe.get_value("Employee", manager, "user_id")
			if manager_user:
				processed_record["expense_approver"] = manager_user

		# Process expenses child table
		if "expenses" in processed_record:
			processed_expenses = []
			for exp in processed_record["expenses"]:
				exp_copy = exp.copy()
				processed_expenses.append(exp_copy)
			processed_record["expenses"] = processed_expenses

		processed_records.append(processed_record)

	if processed_records:
		make_records(processed_records)

	# Submit approved claims
	approved_count = 0
	for ec in frappe.get_all("Expense Claim", {"approval_status": "Approved", "docstatus": 0}):
		try:
			frappe.get_doc("Expense Claim", ec.name).submit()
			approved_count += 1
		except Exception:
			continue

	frappe.publish_realtime(
		"demo_progress",
		{"message": f"Created {len(processed_records)} Expense Claims, submitted {approved_count}"},
	)


def get_records_from_json(doctype):
	import os

	data_path = os.path.join(
		os.path.dirname(__file__), "demo_data", f"{doctype.lower().replace(' ', '_')}.json"
	)

	if not os.path.exists(data_path):
		return []

	with open(data_path) as f:
		return json.load(f)
