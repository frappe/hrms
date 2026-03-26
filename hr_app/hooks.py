app_name = "hr_app"
app_title = "HortiHub HR"
app_publisher = "Frappe Technologies Pvt. Ltd."
app_description = "Modern HR and Payroll Software"
app_email = "contact@frappe.io"
app_license = "GNU General Public License (v3)"
required_apps = ["frappe/erpnext"]
source_link = "http://github.com/frappe/hrms"
app_logo_url = "/assets/hr_app/images/frappe-hr-logo.svg"
app_home = "/desk/people"

add_to_apps_screen = [
	{
		"name": "hr_app",
		"logo": "/assets/hr_app/images/frappe-hr-logo.svg",
		"title": "HortiHub HR",
		"route": "/desk/people",
		"has_permission": "hr_app.hr.utils.check_app_permission",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/hr_app/css/hrms.css"
app_include_js = [
	"hr_app.bundle.js",
]
app_include_css = "hr_app.bundle.css"

# website

# include js, css files in header of web template
# web_include_css = "/assets/hr_app/css/hrms.css"
# web_include_js = "/assets/hr_app/js/hrms.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "hrms/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Employee": "public/js/erpnext/employee.js",
	"Company": "public/js/erpnext/company.js",
	"Department": "public/js/erpnext/department.js",
	"Timesheet": "public/js/erpnext/timesheet.js",
	"Payment Entry": "public/js/erpnext/payment_entry.js",
	"Journal Entry": "public/js/erpnext/journal_entry.js",
	"Delivery Trip": "public/js/erpnext/delivery_trip.js",
	"Bank Transaction": "public/js/erpnext/bank_transaction.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

calendars = ["Leave Application"]

# Generators
# ----------

# automatically create page for each record of this doctype
website_generators = ["Job Opening"]

website_route_rules = [
	{"from_route": "/hr-app/<path:app_path>", "to_route": "hr_app"},
	{"from_route": "/hr/<path:app_path>", "to_route": "roster"},
]
# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
	"methods": [
		"hr_app.utils.get_country",
	],
}

# Installation
# ------------

# before_install = "hr_app.install.before_install"
after_install = "hr_app.install.after_install"
before_migrate = "hr_app.setup.make_people_workspace_standard"
after_migrate = "hr_app.setup.update_select_perm_after_install"

setup_wizard_complete = "hr_app.subscription_utils.update_erpnext_access"

# Uninstallation
# ------------

before_uninstall = "hr_app.uninstall.before_uninstall"
# after_uninstall = "hr_app.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "hr_app.utils.before_app_install"
after_app_install = "hr_app.setup.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

before_app_uninstall = "hr_app.setup.before_app_uninstall"
# after_app_uninstall = "hr_app.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "hr_app.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

has_upload_permission = {"Employee": "erpnext.setup.doctype.employee.employee.has_upload_permission"}

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Employee": "hr_app.overrides.employee_master.EmployeeMaster",
	"Timesheet": "hr_app.overrides.employee_timesheet.EmployeeTimesheet",
	"Payment Entry": "hr_app.overrides.employee_payment_entry.EmployeePaymentEntry",
	"Project": "hr_app.overrides.employee_project.EmployeeProject",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"User": {
		"validate": [
			"erpnext.setup.doctype.employee.employee.validate_employee_role",
			"hr_app.overrides.employee_master.update_approver_user_roles",
		],
	},
	"Company": {
		"validate": "hr_app.overrides.company.validate_default_accounts",
		"on_update": [
			"hr_app.overrides.company.make_company_fixtures",
			"hr_app.overrides.company.set_default_hr_accounts",
		],
		"on_trash": "hr_app.overrides.company.handle_linked_docs",
	},
	"Holiday List": {
		"on_update": "hr_app.utils.holiday_list.invalidate_cache",
		"on_trash": "hr_app.utils.holiday_list.invalidate_cache",
	},
	"Timesheet": {"validate": "hr_app.hr.utils.validate_active_employee"},
	"Payment Entry": {
		"on_submit": "hr_app.hr.doctype.expense_claim.expense_claim.update_payment_for_expense_claim",
		"on_cancel": "hr_app.hr.doctype.expense_claim.expense_claim.update_payment_for_expense_claim",
		"on_update_after_submit": "hr_app.hr.doctype.expense_claim.expense_claim.update_payment_for_expense_claim",
	},
	"Unreconcile Payment": {
		"on_submit": "hr_app.hr.doctype.expense_claim.expense_claim.update_payment_for_expense_claim",
	},
	"Journal Entry": {
		"validate": "hr_app.hr.doctype.expense_claim.expense_claim.validate_expense_claim_in_jv",
		"on_submit": [
			"hr_app.hr.doctype.expense_claim.expense_claim.update_payment_for_expense_claim",
			"hr_app.hr.doctype.full_and_final_statement.full_and_final_statement.update_full_and_final_statement_status",
			"hr_app.payroll.doctype.salary_withholding.salary_withholding.update_salary_withholding_payment_status",
		],
		"on_update_after_submit": "hr_app.hr.doctype.expense_claim.expense_claim.update_payment_for_expense_claim",
		"on_cancel": [
			"hr_app.hr.doctype.expense_claim.expense_claim.update_payment_for_expense_claim",
			"hr_app.payroll.doctype.salary_slip.salary_slip.unlink_ref_doc_from_salary_slip",
			"hr_app.hr.doctype.full_and_final_statement.full_and_final_statement.update_full_and_final_statement_status",
			"hr_app.payroll.doctype.salary_withholding.salary_withholding.update_salary_withholding_payment_status",
		],
	},
	"Loan": {"validate": "hr_app.hr.utils.validate_loan_repay_from_salary"},
	"Employee": {
		"validate": "hr_app.overrides.employee_master.validate_onboarding_process",
		"on_update": [
			"hr_app.overrides.employee_master.update_approver_role",
			"hr_app.overrides.employee_master.publish_update",
		],
		"after_insert": "hr_app.overrides.employee_master.update_job_applicant_and_offer",
		"on_trash": "hr_app.overrides.employee_master.update_employee_transfer",
		"after_delete": "hr_app.overrides.employee_master.publish_update",
	},
	"Project": {"validate": "hr_app.controllers.employee_boarding_controller.update_employee_boarding_status"},
	"Task": {"on_update": "hr_app.controllers.employee_boarding_controller.update_task"},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"all": [
		"hr_app.hr.doctype.interview.interview.send_interview_reminder",
	],
	"hourly": [
		"hr_app.hr.doctype.daily_work_summary_group.daily_work_summary_group.trigger_emails",
	],
	"hourly_long": [
		"hr_app.hr.doctype.shift_type.shift_type.update_last_sync_of_checkin",
		"hr_app.hr.doctype.shift_type.shift_type.process_auto_attendance_for_all_shifts",
		"hr_app.hr.doctype.shift_schedule_assignment.shift_schedule_assignment.process_auto_shift_creation",
	],
	"daily": [
		"hr_app.controllers.employee_reminders.send_birthday_reminders",
		"hr_app.controllers.employee_reminders.send_work_anniversary_reminders",
		"hr_app.hr.doctype.daily_work_summary_group.daily_work_summary_group.send_summary",
		"hr_app.hr.doctype.interview.interview.send_daily_feedback_reminder",
		"hr_app.hr.doctype.job_opening.job_opening.close_expired_job_openings",
	],
	"daily_long": [
		"hr_app.hr.doctype.leave_ledger_entry.leave_ledger_entry.process_expired_allocation",
		"hr_app.hr.utils.generate_leave_encashment",
		"hr_app.hr.utils.allocate_earned_leaves",
	],
	"weekly": ["hr_app.controllers.employee_reminders.send_reminders_in_advance_weekly"],
	"monthly": ["hr_app.controllers.employee_reminders.send_reminders_in_advance_monthly"],
}

advance_payment_payable_doctypes = ["Leave Encashment", "Gratuity", "Employee Advance"]

invoice_doctypes = ["Expense Claim"]

period_closing_doctypes = ["Payroll Entry"]

accounting_dimension_doctypes = [
	"Expense Claim",
	"Expense Claim Detail",
	"Expense Taxes and Charges",
	"Payroll Entry",
	"Leave Encashment",
]

bank_reconciliation_doctypes = ["Expense Claim"]

# Testing
# -------

before_tests = "hr_app.tests.test_utils.before_tests"

# Overriding Methods
# -----------------------------

# get matching queries for Bank Reconciliation
get_matching_queries = "hr_app.hr.utils.get_matching_queries"

regional_overrides = {
	"India": {
		"hr_app.hr.utils.calculate_annual_eligible_hra_exemption": "hr_app.regional.india.utils.calculate_annual_eligible_hra_exemption",
		"hr_app.hr.utils.calculate_hra_exemption_for_period": "hr_app.regional.india.utils.calculate_hra_exemption_for_period",
		"hr_app.hr.utils.calculate_tax_with_marginal_relief": "hr_app.regional.india.utils.calculate_tax_with_marginal_relief",
	},
}

# ERPNext doctypes for Global Search
global_search_doctypes = {
	"Default": [
		{"doctype": "Salary Slip", "index": 19},
		{"doctype": "Leave Application", "index": 20},
		{"doctype": "Expense Claim", "index": 21},
		{"doctype": "Employee Grade", "index": 37},
		{"doctype": "Job Opening", "index": 39},
		{"doctype": "Job Applicant", "index": 40},
		{"doctype": "Job Offer", "index": 41},
		{"doctype": "Salary Structure Assignment", "index": 42},
		{"doctype": "Appraisal", "index": 43},
	],
}

# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "hr_app.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {
	"Employee": "hr_app.overrides.dashboard_overrides.get_dashboard_for_employee",
	"Holiday List": "hr_app.overrides.dashboard_overrides.get_dashboard_for_holiday_list",
	"Task": "hr_app.overrides.dashboard_overrides.get_dashboard_for_project",
	"Project": "hr_app.overrides.dashboard_overrides.get_dashboard_for_project",
	"Timesheet": "hr_app.overrides.dashboard_overrides.get_dashboard_for_timesheet",
	"Bank Account": "hr_app.overrides.dashboard_overrides.get_dashboard_for_bank_account",
}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

ignore_links_on_delete = ["PWA Notification"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"hr_app.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# Recommended only for DocTypes which have limited documents with untranslated names
# For example: Role, Gender, etc.
# translated_search_doctypes = []

company_data_to_be_ignored = [
	"Salary Component Account",
	"Salary Structure",
	"Salary Structure Assignment",
	"Payroll Period",
	"Income Tax Slab",
	"Leave Period",
	"Leave Policy Assignment",
	"Employee Onboarding Template",
	"Employee Separation Template",
]

# List of apps whose translatable strings should be excluded from this app's translations.
ignore_translatable_strings_from = ["frappe", "erpnext"]
employee_holiday_list = ["hr_app.utils.holiday_list.get_holiday_list_for_employee"]
export_python_type_annotations = True
require_type_annotated_api_methods = True
