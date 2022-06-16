import frappe
from frappe import _

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
	create_custom_fields(get_custom_fields())


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
				"insert_after": "employee_name",
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
				"insert_after": "column_break_31",
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
				"insert_after": "bank_ac_no",
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
	}
