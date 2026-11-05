# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class EmployeeSkillMap(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.employee_skill.employee_skill import EmployeeSkill
		from hrms.hr.doctype.employee_training.employee_training import EmployeeTraining

		designation: DF.ReadOnly | None
		employee: DF.Link
		employee_name: DF.ReadOnly | None
		employee_skills: DF.Table[EmployeeSkill]
		trainings: DF.Table[EmployeeTraining]
	# end: auto-generated types

	def validate(self):
		if not self.is_new() and self.has_value_changed("employee"):
			frappe.throw(_("Employee cannot be changed on an existing Employee Skill Map"))
