import frappe
from frappe.model.utils.rename_field import rename_field


def execute():
	try:
		if frappe.db.has_column("Employee Benefit Claim", "claim_date"):
			rename_field("Employee Benefit Claim", "claim_date", "payroll_date")

	except Exception as e:
		if e.args[0] != 1054:
			raise
