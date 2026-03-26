import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	custom_fields = {
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
	}

	if frappe.db.exists("Company", {"country": "India"}):
		custom_fields["Employee"].extend(
			[
				{
					"fieldname": "bank_cb",
					"fieldtype": "Column Break",
					"insert_after": "bank_ac_no",
				},
				{
					"fieldname": "ifsc_code",
					"label": "IFSC Code",
					"fieldtype": "Data",
					"insert_after": "bank_cb",
					"print_hide": 1,
					"depends_on": 'eval:doc.salary_mode == "Bank"',
					"translatable": 0,
				},
				{
					"fieldname": "pan_number",
					"label": "PAN Number",
					"fieldtype": "Data",
					"insert_after": "payroll_cost_center",
					"print_hide": 1,
					"translatable": 0,
				},
				{
					"fieldname": "micr_code",
					"label": "MICR Code",
					"fieldtype": "Data",
					"insert_after": "ifsc_code",
					"print_hide": 1,
					"depends_on": 'eval:doc.salary_mode == "Bank"',
					"translatable": 0,
				},
				{
					"fieldname": "provident_fund_account",
					"label": "Provident Fund Account",
					"fieldtype": "Data",
					"insert_after": "pan_number",
					"translatable": 0,
				},
			]
		)

	create_custom_fields(custom_fields)
