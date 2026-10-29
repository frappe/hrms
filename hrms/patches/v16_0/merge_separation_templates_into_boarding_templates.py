import frappe
from frappe.model.utils.rename_field import rename_field

SEPARATION_TEMPLATE = "Employee Separation Template"
ROW_FIELDS = ["activity_name", "user", "role", "description", "task_weight", "begin_on", "duration"]


def execute():
	frappe.db.set_value(
		"Employee Boarding Activity",
		{"parenttype": "Employee Boarding Template", "parentfield": "activities"},
		"parentfield",
		"preboarding_activities",
		update_modified=False,
	)
	rename_field("Employee Preboarding", "employee_onboarding_template", "employee_boarding_template")

	if not frappe.db.exists("DocType", SEPARATION_TEMPLATE):
		return

	for old in frappe.get_all(
		SEPARATION_TEMPLATE,
		fields=["name", "title", "company", "department", "designation", "employee_grade"],
		order_by="creation",
	):
		template = frappe.new_doc("Employee Boarding Template")
		template.update(
			{key: old[key] for key in ("title", "company", "department", "designation", "employee_grade")}
		)
		for row in frappe.get_all(
			"Employee Boarding Activity",
			filters={"parenttype": SEPARATION_TEMPLATE, "parent": old.name},
			fields=ROW_FIELDS,
			order_by="idx",
		):
			template.append("offboarding_activities", row)
		template.flags.skip_standard_activities = True
		template.insert(ignore_permissions=True, ignore_mandatory=True)

		if frappe.db.has_column("Employee Separation", "employee_separation_template"):
			frappe.db.sql(
				"update `tabEmployee Separation` set employee_boarding_template=%s where employee_separation_template=%s",
				(template.name, old.name),
			)

	frappe.db.delete("Employee Boarding Activity", {"parenttype": SEPARATION_TEMPLATE})
	frappe.delete_doc("DocType", SEPARATION_TEMPLATE, ignore_missing=True, force=True)
