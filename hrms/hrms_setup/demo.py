# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import json
import os

import frappe
from frappe import _

from hrms.hrms_setup.demo_expense import setup_expense_claim_type_accounts
from hrms.hrms_setup.demo_payroll import setup_payroll_runs

DEMO_FISCAL_YEAR = "2026"
DYNAMIC_DEMO_DATA_JOB_ID = "hrms_demo_dynamic_data_generation"
SKIP_CLEAR_DOCTYPES = {"gender", "salutation"}
HRMS_DEMO_TRANSACTION_DOCTYPES_TO_CLEAR = {
	"Expense Claim",
	"Appraisal",
	"Employee Performance Feedback",
	"Salary Structure Assignment",
	"Leave Allocation",
	"Leave Application",
}


def setup_demo_data(setup_wizard_values=None):
	from frappe.utils.telemetry import capture

	capture("demo_data_creation_started", "hrms")
	try:
		frappe.db.savepoint("demo_data")
		setup_demo()
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

	from erpnext.setup.demo import clear_demo_data as clear_erpnext_demo_data

	frappe.only_for("System Manager")

	capture("demo_data_erased", "hrms")
	try:
		company = get_demo_company_from_global_defaults()
		if not company:
			return

		clear_hrms_demo_data(company)
		clear_erpnext_demo_data()
	except Exception:
		frappe.db.rollback()
		frappe.log_error("Failed to erase demo data")
		frappe.throw(
			_("Failed to erase demo data, please delete the demo company manually."),
			title=_("Could Not Delete Demo Data"),
		)


def clear_hrms_demo_data(company):
	clear_demo_attendance(company)
	clear_leave_ledger_entries(company)
	clear_ignored_transactions()
	clear_demo_payroll_entries(company)
	clear_demo_records("employee")
	clear_masters()
	clear_expense_claim_type_accounts(company)
	clear_demo_fiscal_years(company)


def clear_ignored_transactions():
	doctypes_to_clear = HRMS_DEMO_TRANSACTION_DOCTYPES_TO_CLEAR | set(
		frappe.get_hooks("company_data_to_be_ignored") or []
	)

	for hook_name in ("hrms_demo_background_transaction_doctypes", "hrms_demo_transaction_doctypes"):
		for doctype in frappe.get_hooks(hook_name)[::-1]:
			if frappe.unscrub(doctype) in doctypes_to_clear:
				clear_demo_records(doctype)


def clear_leave_ledger_entries(company):
	frappe.db.delete("Leave Ledger Entry", {"company": company})


def clear_demo_attendance(company):
	for attendance in frappe.get_all("Attendance", filters={"company": company}, pluck="name"):
		doc = frappe.get_doc("Attendance", attendance)
		if doc.meta.is_submittable:
			doc.db_set("docstatus", 0)
		doc.delete(ignore_permissions=True, force=True)


def clear_demo_payroll_entries(company):
	for payroll_entry in frappe.get_all("Payroll Entry", filters={"company": company}, pluck="name"):
		doc = frappe.get_doc("Payroll Entry", payroll_entry)
		if doc.docstatus == 1:
			doc.cancel()
		doc.delete(ignore_permissions=True, force=True)


def clear_masters():
	for hook_name in ("hrms_demo_background_master_doctypes", "hrms_demo_master_doctypes"):
		for doctype in frappe.get_hooks(hook_name)[::-1]:
			clear_demo_records(doctype)


def clear_expense_claim_type_accounts(company):
	frappe.db.delete("Expense Claim Account", {"company": company})


def clear_demo_fiscal_years(company):
	abbr = frappe.db.get_value("Company", company, "abbr")
	fiscal_year = f"{DEMO_FISCAL_YEAR} - {abbr}"
	if frappe.db.exists("Fiscal Year Company", {"parent": fiscal_year, "company": company}):
		frappe.delete_doc("Fiscal Year", fiscal_year, ignore_permissions=True, force=True)


def clear_demo_records(doctype):
	if doctype in SKIP_CLEAR_DOCTYPES:
		return

	data = read_data_file_using_hooks(doctype)
	if not data:
		return

	for record in json.loads(data)[::-1]:
		clear_demo_record(record)


def clear_demo_record(record):
	document_type = record.get("doctype")
	del record["doctype"]

	if document_type in ("Company", "Fiscal Year"):
		return

	valid_columns = frappe.get_meta(document_type).get_valid_columns()
	filters = record
	for key in list(filters):
		if key not in valid_columns or isinstance(filters[key], list):
			filters.pop(key, None)

	try:
		doc = frappe.get_doc(document_type, filters)
		if doc.meta.is_submittable:
			if document_type == "Expense Claim" and doc.docstatus == 1:
				doc.cancel()
			else:
				doc.db_set("docstatus", 0)
		frappe.delete_doc(document_type, doc.name, ignore_permissions=True, force=True)
	except frappe.exceptions.DoesNotExistError:
		frappe.clear_last_message()
		pass


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


def setup_demo():
	process_demo_records("hrms_demo_master_doctypes")
	setup_demo_fiscal_years()
	setup_payroll_accounts()
	setup_employees()
	setup_expense_claim_type_accounts()
	process_demo_records("hrms_demo_transaction_doctypes")
	enqueue_dynamic_demo_data()


def _is_in_test():
	return getattr(frappe.flags, "in_test", False) or getattr(frappe, "in_test", False)


def enqueue_dynamic_demo_data():
	company = get_demo_company()
	company_key = "".join(c for c in frappe.scrub(company) if c.isalnum() or c == "_")
	frappe.enqueue(
		"hrms.hrms_setup.demo.setup_dynamic_demo_data",
		queue="long",
		timeout=3600,
		job_id=f"{DYNAMIC_DEMO_DATA_JOB_ID}:{company_key}",
		deduplicate=True,
		enqueue_after_commit=True,
		now=_is_in_test(),
		company=company,
	)


def setup_dynamic_demo_data(company=None):
	from frappe.utils.telemetry import capture

	from hrms.hrms_setup.demo_dynamic import setup_leave_and_attendance

	capture("dynamic_demo_data_creation_started", "hrms")
	try:
		company = company or get_demo_company()
		process_demo_records("hrms_demo_background_master_doctypes")
		set_employee_recruitment_links()
		process_demo_records("hrms_demo_background_transaction_doctypes")
		setup_leave_and_attendance(company)
		setup_payroll_accounts()
		setup_payroll_runs()
	except Exception:
		frappe.log_error("Failed to create HR dynamic demo data")
		capture("dynamic_demo_data_creation_failed", "hrms", properties={"exception": frappe.get_traceback()})
		raise

	capture("dynamic_demo_data_creation_completed", "hrms")


def process_demo_records(hook_name):
	from frappe.desk.page.setup_wizard.setup_wizard import make_records

	for doctype in frappe.get_hooks(hook_name):
		data = read_data_file_using_hooks(doctype)
		if data:
			make_records(json.loads(data))


def read_data_file_using_hooks(doctype, context=None):
	with open(get_data_path(doctype)) as f:
		return render_demo_template(f.read(), context)


def get_demo_records(doctype, context=None):
	data = read_data_file_using_hooks(doctype, context)
	return json.loads(data or "[]")


def render_demo_template(data, context=None):
	if not data:
		return data

	return frappe.render_template(data, context or get_demo_company_context())


def setup_demo_fiscal_years(context=None):
	context = context or get_demo_company_context()
	for record in get_demo_records("demo_company", context):
		if record.get("doctype") != "Fiscal Year":
			continue

		if fiscal_year_exists_for_company(
			record.get("year_start_date"), record.get("year_end_date"), context.demo_company
		):
			continue

		frappe.get_doc(record).insert(ignore_permissions=True)


def fiscal_year_exists_for_company(year_start_date, year_end_date, company):
	for fiscal_year in frappe.get_all(
		"Fiscal Year",
		filters={"year_start_date": year_start_date, "year_end_date": year_end_date},
		pluck="name",
	):
		if frappe.db.exists("Fiscal Year Company", {"parent": fiscal_year, "company": company}):
			return True

	return False


def setup_payroll_accounts():
	context = get_demo_company_context()
	payroll_payable_account = f"Payroll Payable - {context.demo_company_abbr}"

	if frappe.db.exists("Account", payroll_payable_account):
		frappe.db.set_value("Account", payroll_payable_account, "account_type", "Payable")

	setup_salary_component_accounts()


def setup_salary_component_accounts():
	context = get_demo_company_context()
	salary_account = f"Salary - {context.demo_company_abbr}"
	if not frappe.db.exists("Account", salary_account):
		return

	for record in get_demo_records("salary_component"):
		salary_component = record.get("salary_component") or record.get("name")
		if not salary_component or not frappe.db.exists("Salary Component", salary_component):
			continue

		if frappe.db.exists(
			"Salary Component Account",
			{"parent": salary_component, "company": context.demo_company},
		):
			continue

		component = frappe.get_doc("Salary Component", salary_component)
		component.append("accounts", {"company": context.demo_company, "account": salary_account})
		component.save(ignore_permissions=True)


def setup_employees():
	from frappe.desk.page.setup_wizard.setup_wizard import make_records

	records = json.loads(read_data_file_using_hooks("employee"))
	if not records:
		return

	employee_approvers = {}
	for record in records:
		approvers = {}
		for fieldname in ("leave_approver", "expense_approver"):
			value = record.pop(fieldname, None)
			if value:
				approvers[fieldname] = value

		if record.get("name") and approvers:
			employee_approvers[record["name"]] = approvers

		record.pop("job_applicant", None)

		if record.get("create_user_automatically") and record.get("create_user_permission") is None:
			record["create_user_permission"] = 0

	make_records(records)

	set_employee_approvers(employee_approvers)


def set_employee_approvers(employee_approvers):
	for employee, approvers in employee_approvers.items():
		if not frappe.db.exists("Employee", employee):
			continue

		employee_doc = frappe.get_doc("Employee", employee)
		has_changes = False
		for fieldname, value in approvers.items():
			if employee_doc.get(fieldname) != value:
				employee_doc.set(fieldname, value)
				has_changes = True

		if has_changes:
			employee_doc.save(ignore_permissions=True)


def set_employee_recruitment_links():
	for record in json.loads(read_data_file_using_hooks("employee")):
		employee = record.get("name")
		job_applicant = record.get("job_applicant")
		if not employee or not job_applicant:
			continue
		if not frappe.db.exists("Employee", employee) or not frappe.db.exists("Job Applicant", job_applicant):
			continue

		employee_doc = frappe.get_doc("Employee", employee)
		if employee_doc.job_applicant != job_applicant:
			employee_doc.job_applicant = job_applicant
			employee_doc.save(ignore_permissions=True)


def get_data_path(doctype):
	return os.path.join(os.path.dirname(__file__), "demo_data", f"{doctype}.json")


def get_demo_company():
	return get_demo_company_context().demo_company


def get_demo_company_from_global_defaults():
	demo_company = frappe.db.get_single_value("Global Defaults", "demo_company")
	if demo_company and frappe.db.exists("Company", demo_company):
		return demo_company


def get_demo_company_context():
	demo_company = get_demo_company_from_global_defaults()
	if not demo_company:
		frappe.throw(_("Demo company is not set. Please run ERPNext demo setup first."))

	demo_company_abbr, demo_company_currency = frappe.db.get_value(
		"Company", demo_company, ["abbr", "default_currency"]
	)

	context = frappe._dict(
		demo_company=demo_company,
		demo_company_abbr=demo_company_abbr,
		demo_company_currency=demo_company_currency,
		demo_fiscal_year=f"{DEMO_FISCAL_YEAR} - {demo_company_abbr}",
	)

	return context
