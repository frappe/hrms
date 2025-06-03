import frappe


def execute():
	"""Set half day attendance status to present for existing half day attendance records."""
	if not frappe.db.has_column("Attendance", "half_day_status"):
		return

	# Update existing half day attendance records
	Attendance = frappe.qb.DocType("Attendance")
	(
		frappe.qb.update(Attendance)
		.set(Attendance.half_day_status, "Present")
		.where((Attendance.status == "Half Day") & (Attendance.leave_application.isnotnull()))
	).run()
