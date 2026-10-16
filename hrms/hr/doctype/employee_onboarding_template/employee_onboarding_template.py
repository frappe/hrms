# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document

from hrms.hr.doctype.employee_onboarding.onboarding_activities import (
	STANDARD_ACTIVITIES,
	add_standard_activities,
	set_action_defaults,
	validate_unique_actions,
)


class EmployeeOnboardingTemplate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.employee_boarding_activity.employee_boarding_activity import (
			EmployeeBoardingActivity,
		)
		from hrms.hr.doctype.employee_onboarding_document.employee_onboarding_document import (
			EmployeeOnboardingDocument,
		)

		activities: DF.Table[EmployeeBoardingActivity]
		company: DF.Link | None
		department: DF.Link | None
		designation: DF.Link | None
		employee_grade: DF.Link | None
		is_default: DF.Check
		required_documents: DF.Table[EmployeeOnboardingDocument]
		title: DF.Data
	# end: auto-generated types

	def before_insert(self):
		add_standard_activities(self)

	def validate(self):
		for row in self.activities:
			set_action_defaults(row)
		validate_unique_actions(self.activities, _("this template"))

	def on_update(self):
		if self.is_default:
			frappe.db.set_value(
				"Employee Onboarding Template",
				{"is_default": 1, "name": ("!=", self.name)},
				"is_default",
				0,
			)


@frappe.whitelist()
def get_standard_activities() -> list[dict]:
	frappe.has_permission("Employee Onboarding Template", "create", throw=True)
	return [dict(activity) for activity in STANDARD_ACTIVITIES]


def create_default_template() -> None:
	if frappe.db.exists("Employee Onboarding Template", {"is_default": 1}):
		return

	template = frappe.new_doc("Employee Onboarding Template")
	template.title = _("Standard Onboarding")
	template.is_default = 1
	template.insert(ignore_permissions=True)
