# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists


class SalaryComponent(Document):
	def validate(self):
		self.validate_abbr()

	def clear_cache(self):
		from hrms.payroll.doctype.salary_slip.salary_slip import (
			SALARY_COMPONENT_VALUES,
			TAX_COMPONENTS_BY_COMPANY,
		)

		frappe.cache().delete_value(SALARY_COMPONENT_VALUES)
		frappe.cache().delete_value(TAX_COMPONENTS_BY_COMPANY)
		return super().clear_cache()

	def validate_abbr(self):
		if not self.salary_component_abbr:
			self.salary_component_abbr = "".join([c[0] for c in self.salary_component.split()]).upper()

		self.salary_component_abbr = self.salary_component_abbr.strip()
		self.salary_component_abbr = append_number_if_name_exists(
			"Salary Component",
			self.salary_component_abbr,
			"salary_component_abbr",
			separator="_",
			filters={"name": ["!=", self.name]},
		)
