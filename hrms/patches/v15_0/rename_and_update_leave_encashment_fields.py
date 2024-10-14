import frappe
from frappe.model.utils.rename_field import rename_field


def execute():
	try:
		rename_field("Leave Type", "encashment_threshold_days", "non_encashable_leaves")

	except Exception as e:
		if e.args[0] != 1054:
			raise

	if not frappe.db.has_column("Leave Encashment", "encashable_days"):
		return

	# set new field values
	LeaveEncashment = frappe.qb.DocType("Leave Encashment")
	(
		frappe.qb.update(LeaveEncashment)
		.set(LeaveEncashment.encashment_days, LeaveEncashment.encashable_days)
		.where(LeaveEncashment.encashment_days.isnull())
	).run()

	(
		frappe.qb.update(LeaveEncashment)
		.set(LeaveEncashment.actual_encashable_days, LeaveEncashment.encashable_days)
		.where(LeaveEncashment.actual_encashable_days.isnull())
	).run()
