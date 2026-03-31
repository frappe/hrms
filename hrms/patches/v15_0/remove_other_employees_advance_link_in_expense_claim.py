import frappe

logger = frappe.logger("patch", allow_site=True, file_count=50)
logger.setLevel("INFO")


def execute():
	expense_claims = frappe.db.get_all("Expense Claim", pluck="name")
	for claim in expense_claims:
		claim_doc = frappe.get_doc("Expense Claim", claim)

		if not claim_doc.advances:
			continue

		for advance_row in claim_doc.advances:
			advance_employee = frappe.db.get_value(
				"Employee Advance",
				advance_row.employee_advance,
				"employee",
			)

			if advance_employee != claim_doc.employee:
				frappe.db.delete("Expense Claim Advance", {"name": advance_row.name})

				logger.info(
					"Deleted invalid advance %s link from claim %s",
					advance_row.employee_advance,
					claim_doc.name,
				)

		frappe.db.commit()
