import frappe
from frappe.permissions import add_permission


def execute():
	if frappe.db.exists("Custom DocPerm", {"parent": "Training Event"}) and not frappe.db.exists(
		"Custom DocPerm", {"parent": "Training Event", "role": "Employee", "permlevel": 0, "if_owner": 0}
	):
		add_permission("Training Event", "Employee")

	if not frappe.db.exists("User Type", "Employee Self Service"):
		return

	doc = frappe.get_doc("User Type", "Employee Self Service")
	if "Training Event" in {d.document_type for d in doc.user_doctypes}:
		return

	doc.append("user_doctypes", {"document_type": "Training Event", "read": 1})
	doc.flags.ignore_links = True
	doc.save()
