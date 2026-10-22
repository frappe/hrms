import frappe

RENAMES = {
	"DocType": [
		("Employee Onboarding Document", "Employee Preboarding Document"),
		("Employee Onboarding", "Employee Preboarding"),
	],
	"Role": [("Employee Onboarding Candidate", "Employee Preboarding Candidate")],
	"Number Card": [("Onboardings (This Month)", "Preboardings (This Month)")],
	"Onboarding Step": [("Create Employee Onboarding", "Create Employee Preboarding")],
}


def execute():
	for doctype, pairs in RENAMES.items():
		for old, new in pairs:
			if frappe.db.exists(doctype, old) and not frappe.db.exists(doctype, new):
				frappe.rename_doc(doctype, old, new, force=True)
