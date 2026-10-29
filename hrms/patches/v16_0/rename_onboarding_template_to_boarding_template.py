import frappe

RENAMES = {
	"DocType": [("Employee Onboarding Template", "Employee Boarding Template")],
	"Onboarding Step": [("Create Employee Onboarding Template", "Create Employee Boarding Template")],
}


def execute():
	for doctype, pairs in RENAMES.items():
		for old, new in pairs:
			if frappe.db.exists(doctype, old) and not frappe.db.exists(doctype, new):
				frappe.rename_doc(doctype, old, new, force=True)
