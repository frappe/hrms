import frappe

from hrms.hr.doctype.employee_onboarding_activity.employee_onboarding_activity import (
	create_standard_activities,
)


def execute():
	create_standard_activities()

	for name in frappe.get_all("Employee Onboarding", {"docstatus": 0}, pluck="name"):
		onboarding = frappe.get_doc("Employee Onboarding", name)
		onboarding.flags.ignore_mandatory = True
		onboarding.flags.ignore_links = True
		onboarding.save(ignore_permissions=True)
