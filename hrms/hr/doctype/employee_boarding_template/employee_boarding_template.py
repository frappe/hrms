# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document

from hrms.hr.doctype.employee_preboarding.preboarding_activities import (
	STANDARD_ACTIVITIES,
	add_standard_activities,
	set_action_defaults,
	validate_unique_actions,
)


class EmployeeBoardingTemplate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.employee_boarding_activity.employee_boarding_activity import (
			EmployeeBoardingActivity,
		)

		company: DF.Link | None
		department: DF.Link | None
		designation: DF.Link | None
		employee_grade: DF.Link | None
		offboarding_activities: DF.Table[EmployeeBoardingActivity]
		onboarding_activities: DF.Table[EmployeeBoardingActivity]
		preboarding_activities: DF.Table[EmployeeBoardingActivity]
		title: DF.Data
	# end: auto-generated types

	def before_insert(self):
		if not self.flags.skip_standard_activities:
			add_standard_activities(self)

	def validate(self):
		for row in self.preboarding_activities:
			set_action_defaults(row)
		validate_unique_actions(self.preboarding_activities, _("this template"))
		for row in self.onboarding_activities + self.offboarding_activities:
			row.update({"action": "Manual", "reference_doctype": None, "depends_on_action": None})


@frappe.whitelist()
def get_standard_activities() -> list[dict]:
	frappe.has_permission("Employee Boarding Template", "create", throw=True)
	return [dict(activity) for activity in STANDARD_ACTIVITIES]


def create_default_template() -> None:
	"""Ship one template with the standard activities, for sites that have none yet."""
	if frappe.db.exists("Employee Boarding Template"):
		return

	template = frappe.new_doc("Employee Boarding Template")
	template.title = _("Standard")
	template.insert(ignore_permissions=True)
