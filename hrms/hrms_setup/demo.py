# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import json
import os

import frappe
from frappe import _
from frappe.utils import getdate

DEMO_COMPANY = "Sparrow Tech Pvt Ltd"
DEMO_COMPANY_ABBR = "ST"


def setup_demo_data(args=None):
	from frappe.utils.telemetry import capture

	capture("demo_data_creation_started", "hrms")
	try:
		frappe.db.savepoint("demo_data")
		setup_demo(args)
		capture("demo_data_creation_completed", "hrms")
		frappe.clear_messages()
	except Exception:
		frappe.db.rollback(save_point="demo_data")
		error_log = frappe.log_error("Failed to create HR demo data")
		log_demo_data_failed_notification(error_log)
		capture("demo_data_creation_failed", "hrms", properties={"exception": frappe.get_traceback()})


@frappe.whitelist()
def clear_demo_data():
	from frappe.utils.telemetry import capture

	frappe.only_for("System Manager")

	capture("demo_data_erased", "hrms")
	try:
		delete_company(DEMO_COMPANY)
		default_company = frappe.db.get_single_value("Global Defaults", "default_company")
		frappe.db.set_default("company", default_company)
	except Exception:
		frappe.db.rollback()
		frappe.log_error("Failed to erase demo data")
		frappe.throw(
			_("Failed to erase demo data, please delete the demo company manually."),
			title=_("Could Not Delete Demo Data"),
		)


def delete_company(company):
	frappe.delete_doc("Company", company, ignore_permissions=True)


def log_demo_data_failed_notification(error_log):
	from frappe.core.doctype.role.role import get_users
	from frappe.desk.doctype.notification_log.notification_log import make_notification_logs

	frappe.msgprint(
		_("HR Demo data creation failed. Check notifications for more info."),
		alert=True,
		indicator="red",
		realtime=True,
	)

	users = get_users("System Manager")

	notif_log_doc = {
		"subject": _("HR Demo Data creation failed."),
		"type": "Alert",
		"link": frappe.utils.get_url_to_form("Error Log", error_log.name),
	}

	make_notification_logs(notif_log_doc, users)


def setup_demo(args):
	create_demo_company()
	setup_organization()
	setup_employment_types()
	setup_hr_masters()
	setup_payroll()
	setup_fixtures()
	setup_employees()


def create_demo_company():
	if frappe.db.exists("Company", DEMO_COMPANY):
		return

	from frappe.desk.page.setup_wizard.setup_wizard import make_records

	current_year = getdate().year
	fy_start = f"{current_year}-04-01"
	fy_end = f"{current_year + 1}-03-31"

	records = [
		{
			"doctype": "Fiscal Year",
			"year": f"{current_year}-{current_year + 1}",
			"year_start_date": fy_start,
			"year_end_date": fy_end,
		},
		{
			"doctype": "Company",
			"company_name": DEMO_COMPANY,
			"abbr": DEMO_COMPANY_ABBR,
			"default_currency": "INR",
			"country": "India",
			"create_chart_of_accounts_based_on": "Standard Template",
			"chart_of_accounts": "Standard",
			"domain": "Retail",
			"enable_perpetual_inventory": 1,
		},
	]
	make_records(records)


def setup_organization():
	from frappe.desk.page.setup_wizard.setup_wizard import make_records

	records = []
	records.extend(get_records_from_json("Department"))
	records.extend(get_records_from_json("Branch"))

	existing = {d.name for d in frappe.get_all("Designation", fields=["name"])}
	for record in get_records_from_json("Designation"):
		if record["designation_name"] not in existing:
			records.append(record)

	make_records(records)


def setup_employment_types():
	from frappe.desk.page.setup_wizard.setup_wizard import make_records

	records = []
	existing = {et.name for et in frappe.get_all("Employment Type", fields=["name"])}

	for record in get_records_from_json("Employment Type"):
		if record["employee_type_name"] not in existing:
			records.append(record)

	if records:
		make_records(records)


def setup_hr_masters():
	from frappe.desk.page.setup_wizard.setup_wizard import make_records

	records = []

	existing_leave_types = {lt.name for lt in frappe.get_all("Leave Type", fields=["name"])}
	for record in get_records_from_json("Leave Type"):
		if record["name"] not in existing_leave_types:
			records.append(record)

	existing_shift_types = {st.name for st in frappe.get_all("Shift Type", fields=["name"])}
	for record in get_records_from_json("Shift Type"):
		if record["shift_type_name"] not in existing_shift_types:
			records.append(record)

	make_records(records)
	create_holiday_lists()


def setup_payroll():
	ensure_salary_components()
	create_salary_structure()


def ensure_salary_components():
	from frappe.desk.page.setup_wizard.setup_wizard import make_records

	existing = {sc.name for sc in frappe.get_all("Salary Component", fields=["name"])}
	records = []

	for record in get_records_from_json("Salary Component"):
		if record["salary_component"] not in existing:
			records.append(record)

	if records:
		make_records(records)


def create_salary_structure():
	from frappe.desk.page.setup_wizard.setup_wizard import make_records

	records = get_records_from_json("Salary Structure")
	if records:
		make_records(records)


def create_holiday_lists():
	from frappe.desk.page.setup_wizard.setup_wizard import make_records

	current_year = getdate().year
	records = []

	BRANCH_HOLIDAYS = [
		("Mumbai HQ", "MH"),
		("Bangalore Office", "KA"),
	]

	for branch_name, state_code in BRANCH_HOLIDAYS:
		hl_name = f"Holiday List - {branch_name} - {current_year}"
		hl_from = f"{current_year}-01-01"
		hl_to = f"{current_year}-12-31"

		if frappe.db.exists("Holiday List", hl_name):
			continue

		holidays = get_state_holidays("IN", state_code, current_year, hl_from, hl_to)

		records.append(
			{
				"doctype": "Holiday List",
				"holiday_list_name": hl_name,
				"from_date": hl_from,
				"to_date": hl_to,
				"country": "India",
				"subdivision": state_code,
				"holidays": holidays,
			}
		)

	if records:
		make_records(records)

	hl_name = f"Holiday List - Mumbai HQ - {current_year}"
	if not frappe.db.exists(
		"Holiday List Assignment",
		{"assigned_to": DEMO_COMPANY, "from_date": f"{current_year}-01-01", "docstatus": 1},
	):
		records = [
			{
				"doctype": "Holiday List Assignment",
				"naming_series": "HR-HLA-.YYYY.-",
				"applicable_for": "Company",
				"assigned_to": DEMO_COMPANY,
				"holiday_list": hl_name,
				"from_date": f"{current_year}-01-01",
			}
		]
		make_records(records)


def get_state_holidays(country, subdivision, year, from_date, to_date):
	from holidays import country_holidays

	fd = getdate(from_date)
	td = getdate(to_date)

	holidays = []
	for holiday_date, holiday_name in country_holidays(
		country,
		subdiv=subdivision,
		years=list(range(fd.year, td.year + 1)),
	).items():
		if fd <= holiday_date <= td:
			holidays.append(
				{
					"doctype": "Holiday",
					"holiday_date": holiday_date.strftime("%Y-%m-%d"),
					"description": holiday_name,
				}
			)
	return holidays


def setup_fixtures():
	for gender in ("Male", "Female", "Other"):
		if not frappe.db.exists("Gender", gender):
			frappe.get_doc({"doctype": "Gender", "gender": gender}).insert(
				ignore_permissions=True, ignore_if_duplicate=True
			)

	for salutation in ("Mr", "Ms", "Mrs", "Dr"):
		if not frappe.db.exists("Salutation", salutation):
			frappe.get_doc({"doctype": "Salutation", "salutation": salutation}).insert(
				ignore_permissions=True, ignore_if_duplicate=True
			)


def setup_employees():
	from frappe.desk.page.setup_wizard.setup_wizard import make_records

	records = get_records_from_json("Employee")
	if not records:
		return

	department_names = set(r["department"] for r in records if r.get("department"))
	department_map = {}
	for dept_name in department_names:
		dept = frappe.get_all("Department", filters={"department_name": dept_name}, fields=["name"])
		if dept:
			department_map[dept_name] = dept[0].name

	for r in records:
		if r.get("department") and department_map.get(r["department"]):
			r["department"] = department_map[r["department"]]

	manager_names = {}
	for r in records:
		if r.get("reports_to"):
			manager_names[r["reports_to"]] = None

	for r in records:
		r.pop("reports_to", None)

	make_records(records)

	for name in manager_names:
		emp_list = frappe.get_all("Employee", filters={"employee_name": name}, fields=["name"])
		if emp_list:
			manager_names[name] = emp_list[0].name

	for r in get_records_from_json("Employee"):
		if r.get("reports_to"):
			manager_name = manager_names.get(r["reports_to"])
			if manager_name:
				emp_list = frappe.get_all(
					"Employee", filters={"employee_name": r["employee_name"]}, fields=["name"]
				)
				if emp_list:
					frappe.db.set_value("Employee", emp_list[0].name, "reports_to", manager_name)


def get_records_from_json(doctype):
	path = get_data_path(doctype)
	with open(path) as f:
		records = json.load(f)

	for record in records:
		for key, value in record.items():
			if isinstance(value, str) and value == "__DEMO_COMPANY__":
				record[key] = DEMO_COMPANY
			elif isinstance(value, list):
				for item in value:
					if isinstance(item, dict):
						for k, v in item.items():
							if isinstance(v, str) and v == "__DEMO_COMPANY__":
								item[k] = DEMO_COMPANY

	return records


def get_data_path(doctype):
	return os.path.join(os.path.dirname(__file__), "demo_data", f"{doctype.lower().replace(' ', '_')}.json")
