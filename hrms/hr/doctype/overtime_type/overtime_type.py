# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class OvertimeType(Document):
	def validate(self):
		if self.overtime_calculation_method == "Salary Component Based":
			self.validate_applicable_components()

	def validate_applicable_components(self):
		if not len(self.applicable_salary_component):
			frappe.throw(_("Select Applicable Components for Overtime Type"))
