# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_link_to_form

STANDARD_ACTIVITIES = [
	{"title": "Create User", "action": "Create User"},
	{"title": "Create Employee", "action": "Create Employee"},
	{"title": "Appointment Letter", "action": "Appointment Letter"},
	{
		"title": "Assign Holiday List",
		"action": "Assign",
		"reference_doctype": "Holiday List Assignment",
		"depends_on_activity": "Create Employee",
	},
	{
		"title": "Assign Leave Policy",
		"action": "Assign",
		"reference_doctype": "Leave Policy Assignment",
		"depends_on_activity": "Create Employee",
	},
	{
		"title": "Assign Salary Structure",
		"action": "Assign",
		"reference_doctype": "Salary Structure Assignment",
		"depends_on_activity": "Create Employee",
	},
	{
		"title": "Assign Shift Type",
		"action": "Assign",
		"reference_doctype": "Shift Assignment",
		"depends_on_activity": "Create Employee",
	},
	{
		"title": "Assign Shift Schedule",
		"action": "Assign",
		"reference_doctype": "Shift Schedule Assignment",
		"depends_on_activity": "Create Employee",
	},
]


class EmployeeOnboardingActivity(Document):
	def validate(self):
		self.validate_standard_fields()
		self.validate_unique_action()

	def on_trash(self):
		if self.is_standard and not frappe.flags.in_uninstall:
			frappe.throw(_("Standard activities can be disabled, not deleted"))

	def validate_standard_fields(self):
		if self.is_new() or not self.is_standard:
			return

		before = self.get_doc_before_save()
		if (before.action, before.reference_doctype) != (self.action, self.reference_doctype):
			frappe.throw(_("The action of a standard activity cannot be changed"))

	def validate_unique_action(self):
		if self.action == "Manual":
			return

		filters = {"action": self.action, "name": ("!=", self.name)}
		if self.action == "Assign":
			filters["reference_doctype"] = self.reference_doctype

		duplicate = frappe.db.get_value("Employee Onboarding Activity", filters)
		if duplicate:
			frappe.throw(
				_("Activity {0} already does this").format(
					get_link_to_form("Employee Onboarding Activity", duplicate)
				)
			)


def create_standard_activities() -> None:
	for sequence, activity in enumerate(STANDARD_ACTIVITIES, start=1):
		if frappe.db.exists("Employee Onboarding Activity", activity["title"]):
			frappe.db.set_value("Employee Onboarding Activity", activity["title"], "sequence", sequence)
			continue

		frappe.get_doc(
			{
				"doctype": "Employee Onboarding Activity",
				**activity,
				"sequence": sequence,
				"is_standard": 1,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)


def get_standard_activities() -> list[dict]:
	return frappe.get_all(
		"Employee Onboarding Activity",
		filters={"is_standard": 1, "enabled": 1},
		fields=["name", "title", "action", "description", "user", "begin_on"],
		order_by="sequence asc",
	)
