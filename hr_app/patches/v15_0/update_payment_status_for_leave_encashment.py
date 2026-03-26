import frappe
from frappe.query_builder import DocType


def execute():
	"""
	Updates submitted Leave Encashment's status based on whether it was paid via a Salary Slip.
	"""

	AdditionalSalary = DocType("Additional Salary")
	SalarySlip = DocType("Salary Slip")
	SalaryDetail = DocType("Salary Detail")
	LeaveEncashment = DocType("Leave Encashment")

	# Fetch Leave Encashments that were paid via Salary Slips
	paid_encashments = (
		frappe.qb.from_(AdditionalSalary)
		.select(AdditionalSalary.ref_docname)
		.where(
			(AdditionalSalary.ref_doctype == "Leave Encashment")
			& (AdditionalSalary.docstatus == 1)
			& (
				AdditionalSalary.name.isin(
					frappe.qb.from_(SalaryDetail)
					.select(SalaryDetail.additional_salary)
					.where(
						(
							SalaryDetail.parent.isin(
								frappe.qb.from_(SalarySlip)
								.select(SalarySlip.name)
								.where(SalarySlip.docstatus == 1)
							)
						)
						& (SalaryDetail.additional_salary == AdditionalSalary.name)
					)
				)
			)
		)
	).run(pluck=True)

	if not paid_encashments:
		# If no encashments were marked as "Paid", set all submitted to "Unpaid"
		frappe.qb.update(LeaveEncashment).set(LeaveEncashment.status, "Unpaid").where(
			LeaveEncashment.docstatus == 1
		).run()
		return

	frappe.qb.update(LeaveEncashment).set(LeaveEncashment.status, "Paid").where(
		LeaveEncashment.name.isin(paid_encashments)
	).run()

	frappe.qb.update(LeaveEncashment).set(LeaveEncashment.status, "Unpaid").where(
		(LeaveEncashment.docstatus == 1) & (LeaveEncashment.name.notin(paid_encashments))
	).run()
