# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import json
import os

import frappe
from frappe import _

DEMO_COMPANY = "Sparrow Tech Pvt Ltd"
DEMO_COMPANY_ABBR = "ST"
DYNAMIC_DEMO_DATA_JOB_ID = "hrms_demo_dynamic_data_generation"
DEMO_APPRAISALS_JOB_ID = "hrms_demo_appraisals_setup"
DEMO_ASSIGNMENTS_JOB_ID = "hrms_demo_assignments_setup"
DEMO_ATTENDANCE_JOB_ID = "hrms_demo_attendance_setup"
DEMO_PAYROLL_JOB_ID = "hrms_demo_payroll_setup"


def extend_bootinfo(bootinfo):
	"""Inject the demo company name into the boot payload.

	The frontend JS reads ``frappe.boot.sysdefaults.demo_company`` to decide
	whether to show the "Demo Company" badge and the "Clear Demo Data" button.
	We populate it only when the HRMS demo company exists and Global Defaults
	hasn't already been set to a different value by another app's demo setup.
	"""
	if not bootinfo.sysdefaults.get("demo_company") and frappe.db.exists("Company", DEMO_COMPANY):
		bootinfo.sysdefaults.demo_company = DEMO_COMPANY


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
		company = get_demo_company_to_clear()
		if not company:
			return

		clear_company_transactions(company)
		if company == DEMO_COMPANY:
			clear_hrms_masters(company)
		clear_erpnext_masters()
		clear_erpnext_demo_companies()
		delete_company(company)

		default_company = frappe.db.get_single_value("Global Defaults", "default_company")
		frappe.db.set_default("company", default_company)
	except Exception:
		frappe.db.rollback()
		frappe.log_error("Failed to erase demo data")
		frappe.throw(
			_("Failed to erase demo data, please delete the demo company manually."),
			title=_("Could Not Delete Demo Data"),
		)


def get_demo_company_to_clear():
	return frappe.db.get_single_value("Global Defaults", "demo_company") or frappe.db.exists(
		"Company", DEMO_COMPANY
	)


def clear_company_transactions(company):
	from erpnext.setup.demo import create_transaction_deletion_record

	if frappe.db.exists("Company", company):
		create_transaction_deletion_record(company)


def clear_erpnext_masters():
	"""Clear ERPNext demo master records using force deletion to bypass link validation."""
	from erpnext.setup.demo import read_data_file_using_hooks as erpnext_read_data_file

	for doctype in frappe.get_hooks("demo_master_doctypes")[::-1]:
		try:
			data = erpnext_read_data_file(doctype)
		except (FileNotFoundError, OSError):
			continue
		if data:
			for item in json.loads(data):
				clear_demo_record(item)


def clear_erpnext_demo_companies():
	"""Delete ERPNext-style demo companies (those ending with ' (Demo)').

	ERPNext's demo setup creates a company named '<original_company> (Demo)' and
	stores it in ``Global Defaults.demo_company``.  HRMS's ``create_demo_company``
	overwrites that field with the HRMS company name, so calling ERPNext's
	``clear_demo_data()`` directly would read the wrong company.

	Instead we call the same three steps ERPNext's ``clear_demo_data`` performs
	internally — TDR, ``clear_masters``, ``delete_company`` — but pass the
	correct company name explicitly.
	"""
	from erpnext.setup.demo import (
		create_transaction_deletion_record,
	)
	from erpnext.setup.demo import (
		delete_company as erpnext_delete_company,
	)

	erpnext_demo_companies = frappe.get_all(
		"Company",
		filters={"company_name": ["like", "% (Demo)"]},
		pluck="name",
	)
	for company in erpnext_demo_companies:
		try:
			create_transaction_deletion_record(company)
			erpnext_delete_company(company)
		except Exception:
			frappe.log_error(f"Failed to delete ERPNext demo company: {company}")


def clear_hrms_masters(company):
	# First delete records that TDR skips (company_data_to_be_ignored) to unblock master deletion
	clear_company_ignored_hrms_data(company)
	clear_expense_claim_type_accounts(company)
	for hook_name in (
		"hrms_demo_background_transaction_doctypes",
		"hrms_demo_transaction_doctypes",
		"hrms_demo_background_master_doctypes",
	):
		clear_demo_records_from_hook(hook_name)

	clear_demo_records("employee")
	clear_demo_records_from_hook("hrms_demo_master_doctypes")


def clear_company_ignored_hrms_data(company):
	"""Delete HRMS records that TDR skips (company_data_to_be_ignored hook).

	Uses direct DB deletion (same as ERPNext TDR) to avoid controller-level
	link validation that would otherwise block deletion and accumulate error messages.
	"""
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

			# Delete child tables first (same approach as TDR)
			for child_df in meta.get_table_fields():
				frappe.db.delete(child_df.options, {"parent": ["in", names]})

			# Direct DB delete — bypasses all controller logic, link checks, and submission state
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
	# Skip child table lists and calculated fields that may differ from creation values
	skip_fields = {"total_score", "final_score", "total_claimed_amount", "total_sanctioned_amount"}
	filters = {
		key: value
		for key, value in record.items()
		if key in valid_columns and key not in skip_fields and not isinstance(value, list)
	}
	if not filters:
		return

	# Use frappe.db.get_value instead of frappe.get_doc to avoid adding "not found"
	# messages to frappe's message queue when the record doesn't exist
	name = frappe.db.get_value(doctype, filters)
	if name:
		delete_demo_doc(doctype, name)


def delete_demo_doc(doctype, name):
	if not frappe.db.exists(doctype, name):
		return

	meta = frappe.get_meta(doctype)
	if meta.is_submittable:
		# Set docstatus to draft directly — skip cancel() which accumulates
		# "Cannot cancel because linked" messages in frappe's message queue
		# even when the exception is caught. This mirrors the TDR force-delete approach.
		frappe.db.set_value(doctype, name, "docstatus", 0)

	frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)


def delete_company(company):
	frappe.db.set_single_value("Global Defaults", "demo_company", "")
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
	process_masters()
	setup_payroll_accounts()
	submit_holiday_list_assignments()
	setup_employees()
	setup_expense_claim_type_accounts()
	process_transactions()
	submit_approved_expense_claims()
	enqueue_dynamic_demo_data()


def _is_in_test():
	return getattr(frappe.flags, "in_test", False) or getattr(frappe, "in_test", False)


def enqueue_dynamic_demo_data():
	frappe.enqueue(
		"hrms.hrms_setup.demo.setup_dynamic_demo_data",
		queue="long",
		timeout=3600,
		job_id=DYNAMIC_DEMO_DATA_JOB_ID,
		deduplicate=True,
		enqueue_after_commit=True,
		now=_is_in_test(),
	)


def setup_dynamic_demo_data():
	"""Step 1 — background masters + recruitment.

	Each step commits its own data and chains the next step as a separate
	background job so results are visible progressively in the UI.
	"""
	from frappe.utils.telemetry import capture

	capture("dynamic_demo_data_creation_started", "hrms")
	try:
		process_background_masters()
		submit_salary_structures()
		set_employee_recruitment_links()
		submit_accepted_job_offers()
	except Exception:
		capture("dynamic_demo_data_creation_failed", "hrms", properties={"exception": frappe.get_traceback()})
		raise

	frappe.enqueue(
		"hrms.hrms_setup.demo.setup_demo_appraisals",
		queue="long",
		timeout=1800,
		job_id=DEMO_APPRAISALS_JOB_ID,
		deduplicate=True,
		enqueue_after_commit=True,
		now=_is_in_test(),
	)


def setup_demo_appraisals():
	"""Step 2 — appraisals (background transactions)."""
	try:
		process_background_transactions()
	except Exception:
		frappe.log_error("Failed to create demo appraisals")
		raise

	frappe.enqueue(
		"hrms.hrms_setup.demo.setup_demo_salary_assignments",
		queue="long",
		timeout=1800,
		job_id=DEMO_ASSIGNMENTS_JOB_ID,
		deduplicate=True,
		enqueue_after_commit=True,
		now=_is_in_test(),
	)


def setup_demo_salary_assignments():
	"""Step 3 — salary structure assignments."""
	from hrms.hrms_setup.demo_dynamic import setup_salary_structure_assignments

	try:
		setup_salary_structure_assignments(DEMO_COMPANY)
	except Exception:
		frappe.log_error("Failed to create demo salary structure assignments")
		raise

	frappe.enqueue(
		"hrms.hrms_setup.demo.setup_demo_leave_and_attendance",
		queue="long",
		timeout=1800,
		job_id=DEMO_ATTENDANCE_JOB_ID,
		deduplicate=True,
		enqueue_after_commit=True,
		now=_is_in_test(),
	)


def setup_demo_leave_and_attendance():
	"""Step 4 — leave allocations, leave applications, attendance records."""
	from hrms.hrms_setup.demo_dynamic import setup_leave_and_attendance

	try:
		setup_leave_and_attendance(DEMO_COMPANY)
	except Exception:
		frappe.log_error("Failed to create demo leave and attendance")
		raise

	frappe.enqueue(
		"hrms.hrms_setup.demo.setup_demo_payroll",
		queue="long",
		timeout=1800,
		job_id=DEMO_PAYROLL_JOB_ID,
		deduplicate=True,
		enqueue_after_commit=True,
		now=_is_in_test(),
	)


def setup_demo_payroll():
	"""Step 5 — payroll runs (final step)."""
	from frappe.utils.telemetry import capture

	try:
		setup_payroll_runs()
	except Exception:
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


def read_data_file_using_hooks(doctype):
	with open(get_data_path(doctype)) as f:
		return f.read()


def setup_expense_claim_type_accounts():
	from hrms.hrms_setup.demo_expense import setup_expense_claim_type_accounts as set_accounts

	set_accounts()


def setup_payroll_runs():
	from hrms.hrms_setup.demo_payroll import setup_payroll_runs as run_payroll

	run_payroll()


def submit_approved_expense_claims():
	for ec in frappe.get_all("Expense Claim", {"approval_status": "Approved", "docstatus": 0}):
		try:
			frappe.get_doc("Expense Claim", ec.name).submit()
		except Exception:
			continue


def create_demo_company(args=None):
	from frappe.desk.page.setup_wizard.setup_wizard import make_records

	records = []
	for record in json.loads(read_data_file_using_hooks("demo_company")):
		if record.get("doctype") == "Fiscal Year":
			fiscal_year = record.get("name") or record.get("year")
			if frappe.db.exists("Fiscal Year", fiscal_year):
				continue
			if fiscal_year_exists_for_dates(record.get("year_start_date"), record.get("year_end_date")):
				continue

		if record.get("doctype") == "Company" and frappe.db.exists("Company", record.get("company_name")):
			continue

		records.append(record)

	if records:
		make_records(records)

	if frappe.db.exists("Company", DEMO_COMPANY):
		frappe.db.set_single_value("Global Defaults", "demo_company", DEMO_COMPANY)
		frappe.db.set_default("company", DEMO_COMPANY)


def fiscal_year_exists_for_dates(year_start_date, year_end_date):
	return bool(
		frappe.db.exists(
			"Fiscal Year",
			{
				"year_start_date": ["<=", year_end_date],
				"year_end_date": [">=", year_start_date],
			},
		)
	)


def setup_payroll_accounts():
	company = frappe.db.exists("Company", DEMO_COMPANY)
	if not company:
		first = frappe.get_all("Company", pluck="name")
		if not first:
			return
		company = first[0]
	else:
		company = DEMO_COMPANY

	accounts = frappe.get_all(
		"Account",
		filters={
			"company": company,
			"account_name": ["like", "%Payroll Payable%"],
		},
		pluck="name",
	)

	if accounts:
		frappe.db.set_value("Account", accounts[0], "account_type", "Payable")


def submit_salary_structures():
	for ss in frappe.get_all("Salary Structure", {"company": DEMO_COMPANY, "docstatus": 0}):
		frappe.get_doc("Salary Structure", ss.name).submit()


def submit_holiday_list_assignments():
	for hla in frappe.get_all(
		"Holiday List Assignment", {"assigned_to": DEMO_COMPANY, "docstatus": 0}, pluck="name"
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
