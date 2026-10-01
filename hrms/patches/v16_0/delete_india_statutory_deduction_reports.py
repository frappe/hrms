import frappe


def execute():
	# Deprecated in favor of the Professional Tax Register and Employee Provident Fund
	# Register in the India Payroll app
	for report in ("Professional Tax Deductions", "Provident Fund Deductions"):
		frappe.delete_doc("Report", report, ignore_missing=True, force=True)
