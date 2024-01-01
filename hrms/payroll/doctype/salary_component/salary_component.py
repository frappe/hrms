# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists


class SalaryComponent(Document):
	def validate(self):
		self.validate_abbr()

	def after_insert(self):
		if not (self.statistical_component or (self.accounts and all(d.account for d in self.accounts))):
			frappe.msgprint(
				title=_("Warning"),
				msg=_("Accounts not set for Salary Component {0}").format(self.name),
				indicator="orange",
			)

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

	@frappe.whitelist()
	def update_salary_structures(self, field, value):
		SalaryDetail = frappe.qb.DocType("Salary Detail")
		SalaryStructure = frappe.qb.DocType("Salary Structure")
		frappe.qb.update(SalaryDetail).inner_join(SalaryStructure).on(
			SalaryDetail.parent == SalaryStructure.name
		).set(SalaryDetail[field], value).where(
			(SalaryDetail.salary_component == self.name) & (SalaryStructure.docstatus == 1)
		).run()
