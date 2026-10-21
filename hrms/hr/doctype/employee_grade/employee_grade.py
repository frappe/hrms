# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class EmployeeGrade(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		currency: DF.Link | None
		default_base_pay: DF.Currency
		default_salary_structure: DF.Link | None
	# end: auto-generated types

	def validate(self):
		self.validate_default_salary_structure()

	def validate_default_salary_structure(self):
		if not self.default_salary_structure:
			return

		structure = frappe.db.get_value(
			"Salary Structure", self.default_salary_structure, ["docstatus", "is_active"], as_dict=True
		)
		if structure.docstatus != 1 or structure.is_active != "Yes":
			frappe.throw(
				_("Default Salary Structure {0} must be submitted and active").format(
					frappe.bold(self.default_salary_structure)
				)
			)
