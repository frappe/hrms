import frappe
from frappe.utils import get_fullname


def execute():
	leave_applications = frappe.get_all(
		"Leave Application",
		filters={
			"leave_approver": ("is", "set"),
			"leave_approver_name": ("in", (None, "")),
		},
		fields=["name", "leave_approver"],
	)

	if not leave_applications:
		return

	updates = {
		entry.name: {"leave_approver_name": get_fullname(entry.leave_approver)}
		for entry in leave_applications
	}
	frappe.db.bulk_update("Leave Application", updates, update_modified=False)
