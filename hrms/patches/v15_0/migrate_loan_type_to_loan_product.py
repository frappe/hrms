from frappe.model.utils.rename_field import rename_field


def execute():
	try:
		rename_field("Salary Slip Loan", "loan_type", "loan_product")

	except Exception as e:
		if e.args[0] != 1054:
			raise
