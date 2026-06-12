# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import json
import os

import frappe
from frappe import _

DEMO_COMPANY_SUFFIX = " (Demo)"
DEMO_FISCAL_YEAR = "2026"
DYNAMIC_DEMO_DATA_JOB_ID = "hrms_demo_dynamic_data_generation"


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

	from erpnext.setup.demo import clear_demo_data as clear_erpnext_demo_data

	frappe.only_for("System Manager")

	capture("demo_data_erased", "hrms")
	try:
		company = get_demo_company_from_global_defaults()
		if not company:
			return

		clear_hrms_masters(company)
		clear_demo_fiscal_years(company)
		clear_erpnext_demo_data()
	except Exception:
		frappe.db.rollback()
		frappe.log_error("Failed to erase demo data")
		frappe.throw(
			_("Failed to erase demo data, please delete the demo company manually."),
			title=_("Could Not Delete Demo Data"),
		)


def clear_hrms_masters(company):
	clear_company_ignored_hrms_data(company)
	clear_expense_claim_type_accounts(company)
	clear_demo_appraisal_feedback()
	for hook_name in (
		"hrms_demo_background_transaction_doctypes",
		"hrms_demo_transaction_doctypes",
		"hrms_demo_background_master_doctypes",
	):
		clear_demo_records_from_hook(hook_name)

	clear_demo_records("employee")
	clear_demo_records_from_hook("hrms_demo_master_doctypes")


def clear_demo_fiscal_years(company):
	context = get_demo_company_context()
	for record in get_demo_records("demo_company", context):
		if record.get("doctype") != "Fiscal Year":
			continue

		fiscal_year = record.get("year")
		if not frappe.db.exists("Fiscal Year Company", {"parent": fiscal_year, "company": company}):
			continue

		frappe.delete_doc("Fiscal Year", fiscal_year, ignore_permissions=True, force=True)


def clear_company_ignored_hrms_data(company):
	for doctype in frappe.get_hooks("company_data_to_be_ignored") or []:
		try:
			meta = frappe.get_meta(doctype)
			company_field = next(
				(f.fieldname for f in meta.fields if f.fieldtype == "Link" and f.options == "Company"),
				None,
			)
			if not company_field:
				continue

			names = frappe.get_all(doctype, filters={company_field: company}, pluck="name")
			if not names:
				continue

			for child_df in meta.get_table_fields():
				frappe.db.delete(child_df.options, {"parent": ["in", names]})

			frappe.db.delete(doctype, {"name": ["in", names]})
		except Exception:
			frappe.log_error(f"Failed to clear {doctype} for demo company during demo clear")


def clear_expense_claim_type_accounts(company):
	for expense_claim_type in frappe.get_all("Expense Claim Type", pluck="name"):
		doc = frappe.get_doc("Expense Claim Type", expense_claim_type)
		original_count = len(doc.accounts)
		doc.accounts = [account for account in doc.accounts if account.company != company]
		if len(doc.accounts) != original_count:
			doc.save(ignore_permissions=True)


def clear_demo_records_from_hook(hook_name):
	for doctype in frappe.get_hooks(hook_name)[::-1]:
		clear_demo_records(doctype)


def clear_demo_records(doctype):
	if doctype in ("gender", "salutation"):
		return

	data = read_data_file_using_hooks(doctype)
	if not data:
		return

	for record in json.loads(data)[::-1]:
		clear_demo_record(record)


def clear_demo_record(record):
	record = record.copy()
	doctype = record.pop("doctype")

	if doctype in ("Company", "Fiscal Year"):
		return

	if record.get("name"):
		delete_demo_doc(doctype, record["name"])
		return

	valid_columns = frappe.get_meta(doctype).get_valid_columns()
	skip_fields = {"total_score", "final_score", "total_claimed_amount", "total_sanctioned_amount"}
	filters = {
		key: value
		for key, value in record.items()
		if key in valid_columns and key not in skip_fields and not isinstance(value, list)
	}
	if not filters:
		return

	name = frappe.db.get_value(doctype, filters)
	if name:
		delete_demo_doc(doctype, name)


def delete_demo_doc(doctype, name):
	if not frappe.db.exists(doctype, name):
		return

	meta = frappe.get_meta(doctype)
	if meta.is_submittable:
		frappe.db.set_value(doctype, name, "docstatus", 0)

	frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)


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
	process_masters()
	setup_payroll_accounts()
	submit_holiday_list_assignments()
	setup_employees()
	setup_expense_claim_type_accounts()
	process_transactions()
	submit_decided_expense_claims()
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

	from hrms.hrms_setup.demo_dynamic import (
		setup_leave_and_attendance,
		setup_salary_structure_assignments,
	)

	capture("dynamic_demo_data_creation_started", "hrms")
	try:
		company = company or get_demo_company()
		process_background_masters()
		submit_salary_structures()
		set_employee_recruitment_links()
		submit_accepted_job_offers()
		setup_demo_appraisals()
		setup_salary_structure_assignments(company)
		setup_leave_and_attendance(company)
		setup_payroll_accounts()
		setup_payroll_runs()
	except Exception:
		frappe.log_error("Failed to create HR dynamic demo data")
		capture("dynamic_demo_data_creation_failed", "hrms", properties={"exception": frappe.get_traceback()})
		raise

	capture("dynamic_demo_data_creation_completed", "hrms")


def process_masters():
	process_demo_records("hrms_demo_master_doctypes")


def process_transactions():
	process_demo_records("hrms_demo_transaction_doctypes")


def process_background_masters():
	process_demo_records("hrms_demo_background_master_doctypes")


def process_background_transactions():
	process_demo_records("hrms_demo_background_transaction_doctypes")


def process_demo_records(hook_name):
	for doctype in frappe.get_hooks(hook_name):
		data = read_data_file_using_hooks(doctype)
		if data:
			for item in json.loads(data):
				create_demo_record(item)


def create_demo_record(record):
	from frappe.modules import scrub

	doc = frappe.get_doc(record)

	parent_link_field = "parent_" + scrub(doc.doctype)
	if doc.meta.get_field(parent_link_field) and not doc.get(parent_link_field):
		doc.flags.ignore_mandatory = True

	previous_in_import = getattr(frappe.flags, "in_import", False)
	if record.get("name"):
		frappe.flags.in_import = True

	try:
		doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
	finally:
		frappe.flags.in_import = previous_in_import


def setup_demo_appraisals():
	process_background_transactions()
	for record in get_appraisal_feedback_records():
		submit_demo_appraisal_feedback(create_appraisal_feedback(record))

	submit_demo_appraisals()


def submit_demo_appraisal_feedback(feedback):
	if feedback and frappe.db.get_value("Employee Performance Feedback", feedback, "docstatus") == 0:
		frappe.get_doc("Employee Performance Feedback", feedback).submit()


def submit_demo_appraisals():
	for record in json.loads(read_data_file_using_hooks("appraisal")):
		appraisal = frappe.db.get_value(
			"Appraisal",
			{
				"employee": record.get("employee"),
				"appraisal_cycle": record.get("appraisal_cycle"),
				"docstatus": 0,
			},
			"name",
		)
		if appraisal:
			frappe.get_doc("Appraisal", appraisal).submit()


def create_appraisal_feedback(record):
	record = record.copy()
	appraisal = get_appraisal_for_feedback(record)
	if not appraisal:
		return

	feedback_filters = {
		"employee": record.get("employee"),
		"reviewer": record.get("reviewer"),
		"appraisal": appraisal,
		"docstatus": ("!=", 2),
	}
	feedback = frappe.db.get_value(
		"Employee Performance Feedback",
		feedback_filters,
		"name",
	)
	if feedback:
		return feedback

	record["appraisal"] = appraisal
	create_demo_record(record)
	return frappe.db.get_value(
		"Employee Performance Feedback",
		feedback_filters,
		"name",
	)


def clear_demo_appraisal_feedback():
	for record in get_appraisal_feedback_records():
		appraisal = get_appraisal_for_feedback(record)
		if not appraisal:
			continue

		for feedback in frappe.get_all(
			"Employee Performance Feedback",
			filters={
				"employee": record.get("employee"),
				"reviewer": record.get("reviewer"),
				"appraisal": appraisal,
				"docstatus": ("!=", 2),
			},
			pluck="name",
		):
			delete_demo_doc("Employee Performance Feedback", feedback)


def get_appraisal_feedback_records():
	try:
		data = read_data_file_using_hooks("employee_performance_feedback")
	except FileNotFoundError:
		return []

	return json.loads(data or "[]")


def get_appraisal_for_feedback(record):
	if record.get("appraisal"):
		return record["appraisal"]

	filters = {
		"employee": record.get("employee"),
		"docstatus": ("!=", 2),
	}
	if record.get("appraisal_cycle"):
		filters["appraisal_cycle"] = record["appraisal_cycle"]

	return frappe.db.get_value("Appraisal", filters, "name")


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


def setup_expense_claim_type_accounts():
	from hrms.hrms_setup.demo_expense import setup_expense_claim_type_accounts as set_accounts

	set_accounts()


def setup_payroll_runs():
	from hrms.hrms_setup.demo_payroll import setup_payroll_runs as run_payroll

	run_payroll()


def submit_decided_expense_claims():
	for ec in frappe.get_all(
		"Expense Claim",
		{"approval_status": ("in", ["Approved", "Rejected"]), "docstatus": 0},
	):
		try:
			frappe.get_doc("Expense Claim", ec.name).submit()
		except Exception:
			continue


def create_demo_company(args=None):
	from erpnext.setup.demo import create_demo_company as create_erpnext_demo_company

	context = get_demo_company_context(args)
	if not frappe.db.exists("Company", context.demo_company):
		create_erpnext_demo_company(context.base_company)
		context = get_demo_company_context(args)

	frappe.db.set_single_value("Global Defaults", "demo_company", context.demo_company)
	frappe.db.set_default("company", context.demo_company)
	setup_demo_fiscal_years(context)
	setup_demo_company_defaults(context)

	return context.demo_company


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


def setup_demo_company_defaults(context):
	set_company_default_if_missing(
		context.demo_company,
		"default_expense_claim_payable_account",
		context.demo_expense_payable_account,
	)
	set_company_default_if_missing(
		context.demo_company,
		"default_payroll_payable_account",
		context.demo_payroll_payable_account,
	)


def set_company_default_if_missing(company, fieldname, account):
	if not account or not frappe.db.exists("Account", account):
		return

	if not frappe.db.get_value("Company", company, fieldname):
		frappe.db.set_value("Company", company, fieldname, account)


def setup_payroll_accounts():
	context = get_demo_company_context()

	if frappe.db.exists("Account", context.demo_payroll_payable_account):
		frappe.db.set_value("Account", context.demo_payroll_payable_account, "account_type", "Payable")

	setup_salary_component_accounts()


def setup_salary_component_accounts():
	context = get_demo_company_context()
	if not frappe.db.exists("Account", context.demo_salary_account):
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
		component.append(
			"accounts", {"company": context.demo_company, "account": context.demo_salary_account}
		)
		component.save(ignore_permissions=True)


def submit_salary_structures():
	for ss in frappe.get_all("Salary Structure", {"company": get_demo_company(), "docstatus": 0}):
		frappe.get_doc("Salary Structure", ss.name).submit()


def submit_holiday_list_assignments():
	for hla in frappe.get_all(
		"Holiday List Assignment", {"assigned_to": get_demo_company(), "docstatus": 0}, pluck="name"
	):
		frappe.get_doc("Holiday List Assignment", hla).submit()


def setup_employees():
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

		create_demo_record(record)

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


def submit_accepted_job_offers():
	for job_offer in frappe.get_all("Job Offer", {"status": "Accepted", "docstatus": 0}, pluck="name"):
		try:
			offer = frappe.get_doc("Job Offer", job_offer)
			offer.flags.ignore_mandatory = True
			offer.submit()
		except Exception:
			continue


def get_data_path(doctype):
	return os.path.join(os.path.dirname(__file__), "demo_data", f"{doctype}.json")


def get_demo_company():
	return get_demo_company_context().demo_company


def get_demo_company_from_global_defaults():
	demo_company = frappe.db.get_single_value("Global Defaults", "demo_company")
	if demo_company and frappe.db.exists("Company", demo_company):
		return demo_company


def get_demo_company_context(args=None):
	demo_company = get_demo_company_from_global_defaults()
	if demo_company:
		demo_company_abbr = frappe.db.get_value("Company", demo_company, "abbr")
		base_company = None
	else:
		base_company = get_base_company(args)
		company_doc = frappe.get_doc("Company", base_company)
		demo_company = get_erpnext_demo_company_name(company_doc.company_name)
		demo_company_abbr = f"{company_doc.abbr}D"

	context = frappe._dict(
		base_company=base_company,
		demo_company=demo_company,
		demo_company_abbr=demo_company_abbr,
		demo_fiscal_year=f"{DEMO_FISCAL_YEAR} - {demo_company_abbr}",
	)
	context.demo_payroll_payable_account = get_demo_payroll_payable_account(context)
	context.demo_salary_account = get_demo_salary_account(context)
	context.demo_expense_payable_account = get_demo_expense_payable_account(context)
	context.demo_cash_account = get_demo_cash_account(context)

	return context


def get_demo_payroll_payable_account(context):
	return (
		get_company_default_account(context.demo_company, "default_payroll_payable_account")
		or get_company_account(
			context.demo_company, account_names=("Payroll Payable",), account_type="Payable"
		)
		or f"Payroll Payable - {context.demo_company_abbr}"
	)


def get_demo_salary_account(context):
	return (
		get_company_account(
			context.demo_company,
			account_names=("Salary", "Salaries", "Salary Expenses"),
			root_type="Expense",
		)
		or f"Salary - {context.demo_company_abbr}"
	)


def get_demo_expense_payable_account(context):
	return (
		get_company_default_account(context.demo_company, "default_expense_claim_payable_account")
		or get_company_default_account(context.demo_company, "default_payable_account")
		or get_company_account(
			context.demo_company,
			account_names=("Employee Advances", "Creditors", "Accounts Payable"),
			account_type="Payable",
		)
		or f"Employee Advances - {context.demo_company_abbr}"
	)


def get_demo_cash_account(context):
	return (
		get_company_account(context.demo_company, account_names=("Cash",), account_type="Cash")
		or f"Cash - {context.demo_company_abbr}"
	)


def get_company_default_account(company, fieldname):
	if not frappe.db.exists("Company", company):
		return

	account = frappe.db.get_value("Company", company, fieldname)
	if account and frappe.db.exists("Account", account):
		return account


def get_company_account(company, account_names=(), account_type=None, root_type=None):
	if not frappe.db.exists("Company", company):
		return

	filters = {"company": company, "is_group": 0}
	if account_names:
		filters["account_name"] = ["in", account_names]
	if account_type:
		filters["account_type"] = account_type
	if root_type:
		filters["root_type"] = root_type

	return frappe.db.get_value("Account", filters, "name", order_by="lft")


def get_base_company(args=None):
	args = frappe._dict(args or {})
	company = args.get("company_name") or frappe.db.get_single_value("Global Defaults", "default_company")
	if company and frappe.db.exists("Company", company):
		return company

	company = frappe.db.get_value("Company", {"company_name": ["not like", f"%{DEMO_COMPANY_SUFFIX}"]})
	if company:
		return company

	frappe.throw(_("Please set up a company before creating HR demo data."))


def get_erpnext_demo_company_name(company_name):
	if company_name.endswith(DEMO_COMPANY_SUFFIX):
		return company_name

	return f"{company_name}{DEMO_COMPANY_SUFFIX}"
