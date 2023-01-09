import frappe
import os
import click
from frappe import _

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.desk.page.setup_wizard.setup_wizard import make_records
from frappe.installer import update_site_config

from hrms.subscription_utils import update_erpnext_access


def after_install():
	create_custom_fields(get_custom_fields())
	make_fixtures()
	setup_notifications()
	update_hr_defaults()
	add_non_standard_user_types()
	set_single_defaults()
	update_erpnext_access()
	frappe.db.commit()
	run_post_install_patches()
	click.secho("Thank you for installing Frappe HR!", fg="green")


def get_custom_fields():
	"""HR specific custom fields that need to be added to the masters in ERPNext"""
	return {
		"Employee": [
			{
				"fieldname": "employment_type",
				"fieldtype": "Link",
				"ignore_user_permissions": 1,
				"label": "Employment Type",
				"oldfieldname": "employment_type",
				"oldfieldtype": "Link",
				"options": "Employment Type",
				"insert_after": "department",
			},
			{
				"fieldname": "job_applicant",
				"fieldtype": "Link",
				"label": "Job Applicant",
				"options": "Job Applicant",
				"insert_after": "employment_details",
			},
			{
				"fieldname": "grade",
				"fieldtype": "Link",
				"label": "Grade",
				"options": "Employee Grade",
				"insert_after": "branch",
			},
			{
				"fieldname": "default_shift",
				"fieldtype": "Link",
				"label": "Default Shift",
				"options": "Shift Type",
				"insert_after": "holiday_list",
			},
			{
				"collapsible": 1,
				"fieldname": "health_insurance_section",
				"fieldtype": "Section Break",
				"label": "Health Insurance",
				"insert_after": "health_details",
			},
			{
				"fieldname": "health_insurance_provider",
				"fieldtype": "Link",
				"label": "Health Insurance Provider",
				"options": "Employee Health Insurance",
				"insert_after": "health_insurance_section",
			},
			{
				"depends_on": "eval:doc.health_insurance_provider",
				"fieldname": "health_insurance_no",
				"fieldtype": "Data",
				"label": "Health Insurance No",
				"insert_after": "health_insurance_provider",
			},
			{
				"fieldname": "approvers_section",
				"fieldtype": "Section Break",
				"label": "Approvers",
				"insert_after": "default_shift",
			},
			{
				"fieldname": "expense_approver",
				"fieldtype": "Link",
				"label": "Expense Approver",
				"options": "User",
				"insert_after": "approvers_section",
			},
			{
				"fieldname": "leave_approver",
				"fieldtype": "Link",
				"label": "Leave Approver",
				"options": "User",
				"insert_after": "expense_approver",
			},
			{
				"fieldname": "column_break_45",
				"fieldtype": "Column Break",
				"insert_after": "leave_approver",
			},
			{
				"fieldname": "shift_request_approver",
				"fieldtype": "Link",
				"label": "Shift Request Approver",
				"options": "User",
				"insert_after": "column_break_45",
			},
			{
				"fieldname": "salary_cb",
				"fieldtype": "Column Break",
				"insert_after": "salary_mode",
			},
			{
				"fetch_from": "department.payroll_cost_center",
				"fetch_if_empty": 1,
				"fieldname": "payroll_cost_center",
				"fieldtype": "Link",
				"label": "Payroll Cost Center",
				"options": "Cost Center",
				"insert_after": "salary_cb",
			},
		],
		"Company": [
			{
				"fieldname": "hr_settings_section",
				"fieldtype": "Section Break",
				"label": "HR & Payroll Settings",
				"insert_after": "credit_limit",
			},
			{
				"depends_on": "eval:!doc.__islocal",
				"fieldname": "default_expense_claim_payable_account",
				"fieldtype": "Link",
				"ignore_user_permissions": 1,
				"label": "Default Expense Claim Payable Account",
				"no_copy": 1,
				"options": "Account",
				"insert_after": "hr_settings_section",
			},
			{
				"fieldname": "default_employee_advance_account",
				"fieldtype": "Link",
				"label": "Default Employee Advance Account",
				"no_copy": 1,
				"options": "Account",
				"insert_after": "default_expense_claim_payable_account",
			},
			{
				"fieldname": "column_break_10",
				"fieldtype": "Column Break",
				"insert_after": "default_employee_advance_account",
			},
			{
				"depends_on": "eval:!doc.__islocal",
				"fieldname": "default_payroll_payable_account",
				"fieldtype": "Link",
				"ignore_user_permissions": 1,
				"label": "Default Payroll Payable Account",
				"no_copy": 1,
				"options": "Account",
				"insert_after": "column_break_10",
			},
		],
		"Department": [
			{
				"fieldname": "section_break_4",
				"fieldtype": "Section Break",
				"insert_after": "disabled",
			},
			{
				"fieldname": "payroll_cost_center",
				"fieldtype": "Link",
				"label": "Payroll Cost Center",
				"options": "Cost Center",
				"insert_after": "section_break_4",
			},
			{
				"fieldname": "column_break_9",
				"fieldtype": "Column Break",
				"insert_after": "payroll_cost_center",
			},
			{
				"description": "Days for which Holidays are blocked for this department.",
				"fieldname": "leave_block_list",
				"fieldtype": "Link",
				"in_list_view": 1,
				"label": "Leave Block List",
				"options": "Leave Block List",
				"insert_after": "column_break_9",
			},
			{
				"description": "The first Approver in the list will be set as the default Approver.",
				"fieldname": "approvers",
				"fieldtype": "Section Break",
				"label": "Approvers",
				"insert_after": "leave_block_list",
			},
			{
				"fieldname": "shift_request_approver",
				"fieldtype": "Table",
				"label": "Shift Request Approver",
				"options": "Department Approver",
				"insert_after": "approvers",
			},
			{
				"fieldname": "leave_approvers",
				"fieldtype": "Table",
				"label": "Leave Approver",
				"options": "Department Approver",
				"insert_after": "shift_request_approver",
			},
			{
				"fieldname": "expense_approvers",
				"fieldtype": "Table",
				"label": "Expense Approver",
				"options": "Department Approver",
				"insert_after": "leave_approvers",
			},
		],
		"Designation": [
			{
				"fieldname": "required_skills_section",
				"fieldtype": "Section Break",
				"label": "Required Skills",
				"insert_after": "description",
			},
			{
				"fieldname": "skills",
				"fieldtype": "Table",
				"label": "Skills",
				"options": "Designation Skill",
				"insert_after": "required_skills_section",
			},
		],
		"Project": [
			{
				"fieldname": "total_expense_claim",
				"fieldtype": "Currency",
				"label": "Total Expense Claim (via Expense Claims)",
				"read_only": 1,
				"insert_after": "total_costing_amount",
			},
		],
		"Task": [
			{
				"fieldname": "total_expense_claim",
				"fieldtype": "Currency",
				"label": "Total Expense Claim (via Expense Claim)",
				"options": "Company:company:default_currency",
				"read_only": 1,
				"insert_after": "total_costing_amount",
			},
		],
		"Timesheet": [
			{
				"fieldname": "salary_slip",
				"fieldtype": "Link",
				"label": "Salary Slip",
				"no_copy": 1,
				"options": "Salary Slip",
				"print_hide": 1,
				"read_only": 1,
				"insert_after": "column_break_3",
			},
		],
		"Terms and Conditions": [
			{
				"default": "1",
				"fieldname": "hr",
				"fieldtype": "Check",
				"label": "HR",
				"insert_after": "buying",
			},
		],
		"Loan": [
			{
				"default": "0",
				"depends_on": 'eval:doc.applicant_type=="Employee"',
				"fieldname": "repay_from_salary",
				"fieldtype": "Check",
				"label": "Repay From Salary",
				"insert_after": "status",
			},
		],
		"Loan Repayment": [
			{
				"default": "0",
				"fetch_from": "against_loan.repay_from_salary",
				"fieldname": "repay_from_salary",
				"fieldtype": "Check",
				"label": "Repay From Salary",
				"insert_after": "is_term_loan",
			},
			{
				"depends_on": "eval:doc.repay_from_salary",
				"fieldname": "payroll_payable_account",
				"fieldtype": "Link",
				"label": "Payroll Payable Account",
				"mandatory_depends_on": "eval:doc.repay_from_salary",
				"options": "Account",
				"insert_after": "rate_of_interest",
			},
		],
	}


def make_fixtures():
	records = [
		# expense claim type
		{"doctype": "Expense Claim Type", "name": _("Calls"), "expense_type": _("Calls")},
		{"doctype": "Expense Claim Type", "name": _("Food"), "expense_type": _("Food")},
		{"doctype": "Expense Claim Type", "name": _("Medical"), "expense_type": _("Medical")},
		{"doctype": "Expense Claim Type", "name": _("Others"), "expense_type": _("Others")},
		{"doctype": "Expense Claim Type", "name": _("Travel"), "expense_type": _("Travel")},
		# leave type
		{
			"doctype": "Leave Type",
			"leave_type_name": _("Casual Leave"),
			"name": _("Casual Leave"),
			"allow_encashment": 1,
			"is_carry_forward": 1,
			"max_continuous_days_allowed": "3",
			"include_holiday": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("Compensatory Off"),
			"name": _("Compensatory Off"),
			"allow_encashment": 0,
			"is_carry_forward": 0,
			"include_holiday": 1,
			"is_compensatory": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("Sick Leave"),
			"name": _("Sick Leave"),
			"allow_encashment": 0,
			"is_carry_forward": 0,
			"include_holiday": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("Privilege Leave"),
			"name": _("Privilege Leave"),
			"allow_encashment": 0,
			"is_carry_forward": 0,
			"include_holiday": 1,
		},
		{
			"doctype": "Leave Type",
			"leave_type_name": _("Leave Without Pay"),
			"name": _("Leave Without Pay"),
			"allow_encashment": 0,
			"is_carry_forward": 0,
			"is_lwp": 1,
			"include_holiday": 1,
		},
		# Employment Type
		{"doctype": "Employment Type", "employee_type_name": _("Full-time")},
		{"doctype": "Employment Type", "employee_type_name": _("Part-time")},
		{"doctype": "Employment Type", "employee_type_name": _("Probation")},
		{"doctype": "Employment Type", "employee_type_name": _("Contract")},
		{"doctype": "Employment Type", "employee_type_name": _("Commission")},
		{"doctype": "Employment Type", "employee_type_name": _("Piecework")},
		{"doctype": "Employment Type", "employee_type_name": _("Intern")},
		{"doctype": "Employment Type", "employee_type_name": _("Apprentice")},
		# Job Applicant Source
		{"doctype": "Job Applicant Source", "source_name": _("Website Listing")},
		{"doctype": "Job Applicant Source", "source_name": _("Walk In")},
		{"doctype": "Job Applicant Source", "source_name": _("Employee Referral")},
		{"doctype": "Job Applicant Source", "source_name": _("Campaign")},
		# Offer Term
		{"doctype": "Offer Term", "offer_term": _("Date of Joining")},
		{"doctype": "Offer Term", "offer_term": _("Annual Salary")},
		{"doctype": "Offer Term", "offer_term": _("Probationary Period")},
		{"doctype": "Offer Term", "offer_term": _("Employee Benefits")},
		{"doctype": "Offer Term", "offer_term": _("Working Hours")},
		{"doctype": "Offer Term", "offer_term": _("Stock Options")},
		{"doctype": "Offer Term", "offer_term": _("Department")},
		{"doctype": "Offer Term", "offer_term": _("Job Description")},
		{"doctype": "Offer Term", "offer_term": _("Responsibilities")},
		{"doctype": "Offer Term", "offer_term": _("Leaves per Year")},
		{"doctype": "Offer Term", "offer_term": _("Notice Period")},
		{"doctype": "Offer Term", "offer_term": _("Incentives")},
		# Email Account
		{"doctype": "Email Account", "email_id": "jobs@example.com", "append_to": "Job Applicant"},
	]

	make_records(records)


def setup_notifications():
	base_path = frappe.get_app_path("hrms", "hr", "doctype")

	# Leave Application
	response = frappe.read_file(
		os.path.join(base_path, "leave_application/leave_application_email_template.html")
	)
	records = [
		{
			"doctype": "Email Template",
			"name": _("Leave Approval Notification"),
			"response": response,
			"subject": _("Leave Approval Notification"),
			"owner": frappe.session.user,
		}
	]
	records += [
		{
			"doctype": "Email Template",
			"name": _("Leave Status Notification"),
			"response": response,
			"subject": _("Leave Status Notification"),
			"owner": frappe.session.user,
		}
	]

	# Interview
	response = frappe.read_file(
		os.path.join(base_path, "interview/interview_reminder_notification_template.html")
	)
	records += [
		{
			"doctype": "Email Template",
			"name": _("Interview Reminder"),
			"response": response,
			"subject": _("Interview Reminder"),
			"owner": frappe.session.user,
		}
	]
	response = frappe.read_file(
		os.path.join(base_path, "interview/interview_feedback_reminder_template.html")
	)
	records += [
		{
			"doctype": "Email Template",
			"name": _("Interview Feedback Reminder"),
			"response": response,
			"subject": _("Interview Feedback Reminder"),
			"owner": frappe.session.user,
		}
	]

	# Exit Interview
	response = frappe.read_file(
		os.path.join(base_path, "exit_interview/exit_questionnaire_notification_template.html")
	)
	records += [
		{
			"doctype": "Email Template",
			"name": _("Exit Questionnaire Notification"),
			"response": response,
			"subject": _("Exit Questionnaire Notification"),
			"owner": frappe.session.user,
		}
	]

	make_records(records)


def update_hr_defaults():
	hr_settings = frappe.get_doc("HR Settings")
	hr_settings.emp_created_by = "Naming Series"
	hr_settings.leave_approval_notification_template = _("Leave Approval Notification")
	hr_settings.leave_status_notification_template = _("Leave Status Notification")

	hr_settings.send_interview_reminder = 1
	hr_settings.interview_reminder_template = _("Interview Reminder")
	hr_settings.remind_before = "00:15:00"

	hr_settings.send_interview_feedback_reminder = 1
	hr_settings.feedback_reminder_notification_template = _("Interview Feedback Reminder")

	hr_settings.exit_questionnaire_notification_template = _("Exit Questionnaire Notification")
	hr_settings.save()


def add_non_standard_user_types():
	user_types = get_user_types_data()

	user_type_limit = {}
	for user_type, data in user_types.items():
		user_type_limit.setdefault(frappe.scrub(user_type), 20)

	update_site_config("user_type_doctype_limit", user_type_limit)

	for user_type, data in user_types.items():
		create_custom_role(data)
		create_user_type(user_type, data)


def get_user_types_data():
	return {
		"Employee Self Service": {
			"role": "Employee Self Service",
			"apply_user_permission_on": "Employee",
			"user_id_field": "user_id",
			"doctypes": {
				# masters
				"Holiday List": ["read"],
				"Employee": ["read", "write"],
				# payroll
				"Salary Slip": ["read"],
				"Employee Benefit Application": ["read", "write", "create", "delete"],
				# expenses
				"Expense Claim": ["read", "write", "create", "delete"],
				"Employee Advance": ["read", "write", "create", "delete"],
				# leave and attendance
				"Leave Application": ["read", "write", "create", "delete"],
				"Attendance Request": ["read", "write", "create", "delete"],
				"Compensatory Leave Request": ["read", "write", "create", "delete"],
				# tax
				"Employee Tax Exemption Declaration": ["read", "write", "create", "delete"],
				"Employee Tax Exemption Proof Submission": ["read", "write", "create", "delete"],
				# projects
				"Timesheet": ["read", "write", "create", "delete", "submit", "cancel", "amend"],
				# trainings
				"Training Program": ["read"],
				"Training Feedback": ["read", "write", "create", "delete", "submit", "cancel", "amend"],
				# shifts
				"Shift Request": ["read", "write", "create", "delete", "submit", "cancel", "amend"],
				# misc
				"Employee Grievance": ["read", "write", "create", "delete"],
				"Employee Referral": ["read", "write", "create", "delete"],
				"Travel Request": ["read", "write", "create", "delete"],
			},
		}
	}


def create_custom_role(data):
	if data.get("role") and not frappe.db.exists("Role", data.get("role")):
		frappe.get_doc(
			{"doctype": "Role", "role_name": data.get("role"), "desk_access": 1, "is_custom": 1}
		).insert(ignore_permissions=True)


def create_user_type(user_type, data):
	if frappe.db.exists("User Type", user_type):
		doc = frappe.get_cached_doc("User Type", user_type)
		doc.user_doctypes = []
	else:
		doc = frappe.new_doc("User Type")
		doc.update(
			{
				"name": user_type,
				"role": data.get("role"),
				"user_id_field": data.get("user_id_field"),
				"apply_user_permission_on": data.get("apply_user_permission_on"),
			}
		)

	create_role_permissions_for_doctype(doc, data)
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)


def create_role_permissions_for_doctype(doc, data):
	for doctype, perms in data.get("doctypes").items():
		args = {"document_type": doctype}
		for perm in perms:
			args[perm] = 1

		doc.append("user_doctypes", args)


def update_select_perm_after_install():
	if not frappe.flags.update_select_perm_after_migrate:
		return

	frappe.flags.ignore_select_perm = False
	for row in frappe.get_all("User Type", filters={"is_standard": 0}):
		print("Updating user type :- ", row.name)
		doc = frappe.get_doc("User Type", row.name)
		doc.flags.ignore_links = True
		doc.save()

	frappe.flags.update_select_perm_after_migrate = False


def set_single_defaults():
	for dt in ("HR Settings", "Payroll Settings"):
		default_values = frappe.db.sql(
			"""
			select fieldname, `default` from `tabDocField`
			where parent=%s""",
			dt,
		)
		if default_values:
			try:
				doc = frappe.get_doc(dt, dt)
				for fieldname, value in default_values:
					doc.set(fieldname, value)
				doc.flags.ignore_mandatory = True
				doc.save()
			except frappe.ValidationError:
				pass

	frappe.db.set_default("date_format", "dd-mm-yyyy")


def get_post_install_patches():
	return (
		"erpnext.patches.v10_0.rename_offer_letter_to_job_offer",
		"erpnext.patches.v10_0.migrate_daily_work_summary_settings_to_daily_work_summary_group",
		"erpnext.patches.v11_0.move_leave_approvers_from_employee",
		"erpnext.patches.v11_0.rename_field_max_days_allowed",
		"erpnext.patches.v11_0.set_department_for_doctypes",
		"erpnext.patches.v11_0.add_expense_claim_default_account",
		"erpnext.patches.v11_0.drop_column_max_days_allowed",
		"erpnext.patches.v11_0.rename_additional_salary_component_additional_salary",
		"erpnext.patches.v11_1.set_salary_details_submittable",
		"erpnext.patches.v11_1.rename_depends_on_lwp",
		"erpnext.patches.v12_0.generate_leave_ledger_entries",
		"erpnext.patches.v12_0.remove_denied_leaves_from_leave_ledger",
		"erpnext.patches.v12_0.set_employee_preferred_emails",
		"erpnext.patches.v12_0.set_job_offer_applicant_email",
		"erpnext.patches.v13_0.move_tax_slabs_from_payroll_period_to_income_tax_slab",
		"erpnext.patches.v12_0.remove_duplicate_leave_ledger_entries",
		"erpnext.patches.v12_0.move_due_advance_amount_to_pending_amount",
		"erpnext.patches.v13_0.move_doctype_reports_and_notification_from_hr_to_payroll",
		"erpnext.patches.v13_0.move_payroll_setting_separately_from_hr_settings",
		"erpnext.patches.v13_0.update_start_end_date_for_old_shift_assignment",
		"erpnext.patches.v13_0.updates_for_multi_currency_payroll",
		"erpnext.patches.v13_0.update_reason_for_resignation_in_employee",
		"erpnext.patches.v13_0.set_company_in_leave_ledger_entry",
		"erpnext.patches.v13_0.rename_stop_to_send_birthday_reminders",
		"erpnext.patches.v13_0.set_training_event_attendance",
		"erpnext.patches.v14_0.set_payroll_cost_centers",
		"erpnext.patches.v13_0.update_employee_advance_status",
		"erpnext.patches.v13_0.update_expense_claim_status_for_paid_advances",
		"erpnext.patches.v14_0.delete_employee_transfer_property_doctype",
		"erpnext.patches.v13_0.set_payroll_entry_status",
		# HRMS
		"create_country_fixtures",
	)


def run_post_install_patches():
	print("\nPatching Existing Data...")

	POST_INSTALL_PATCHES = get_post_install_patches()
	frappe.flags.in_patch = True

	try:
		for patch in POST_INSTALL_PATCHES:
			# patch has not run on the site before
			if not frappe.db.exists("Patch Log", {"patch": ("like", f"%{patch}%")}):
				patch_name = patch.split(".")[-1]
				frappe.get_attr(f"hrms.patches.post_install.{patch_name}.execute")()
	finally:
		frappe.flags.in_patch = False
