from frappe.model.utils.rename_field import rename_field


def execute():
	rename_field("Appointment Letter", "employee_onboarding", "employee_preboarding")
