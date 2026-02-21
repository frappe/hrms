import frappe


def execute():
	usertype = frappe.get_all("User Type", filters={"name": "Employee Self Service"})
	if not usertype:
		return

	doc = frappe.get_doc("User Type", "Employee Self Service")

	existing = {d.document_type for d in doc.user_doctypes}

	if "Leave Type" not in existing:
		doc.append(
			"user_doctypes",
			{
				"document_type": "Leave Type",
				"read": 1,
			},
		)
		doc.flags.ignore_links = True
		doc.save()
