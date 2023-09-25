from frappe.custom.doctype.custom_field.custom_field import create_custom_field

from hrms.payroll.doctype.salary_slip.salary_slip_loan_utils import if_lending_app_installed


@if_lending_app_installed
def execute():
	create_custom_field(
		"Loan Repayment",
		{
			"default": "0",
			"depends_on": 'eval:doc.applicant_type=="Employee"',
			"fieldname": "process_payroll_accounting_entry_based_on_employee",
			"hidden": 1,
			"fieldtype": "Check",
			"label": "Process Payroll Accounting Entry based on Employee",
			"insert_after": "repay_from_salary",
		},
	)
