# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import copy

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists

from hrms.payroll.utils import sanitize_expression


class SalaryComponent(Document):
	def before_validate(self):
		self._condition, self.condition = self.condition, sanitize_expression(self.condition)
		self._formula, self.formula = self.formula, sanitize_expression(self.formula)

	def validate(self):
		self.validate_abbr()
		self.validate_accounts()

	def on_update(self):
		# set old values (allowing multiline strings for better readability in the doctype form)
		if self._condition != self.condition:
			self.db_set("condition", self._condition)
		if self._formula != self.formula:
			self.db_set("formula", self._formula)

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

	def validate_accounts(self):
		if not (self.statistical_component or (self.accounts and all(d.account for d in self.accounts))):
			frappe.msgprint(
				title=_("Warning"),
				msg=_("Accounts not set for Salary Component {0}").format(self.name),
				indicator="orange",
			)

	@frappe.whitelist()
	def get_structures_to_be_updated(self):
		SalaryStructure = frappe.qb.DocType("Salary Structure")
		SalaryDetail = frappe.qb.DocType("Salary Detail")
		return (
			frappe.qb.from_(SalaryStructure)
			.inner_join(SalaryDetail)
			.on(SalaryStructure.name == SalaryDetail.parent)
			.select(SalaryStructure.name)
			.where((SalaryDetail.salary_component == self.name) & (SalaryStructure.docstatus != 2))
			.run(pluck=True)
		)

	@frappe.whitelist()
	def update_salary_structures(self, structures, field, value):
		for structure in structures:
			salary_detail = frappe.get_last_doc(
				"Salary Detail", filters={"parent": structure, "salary_component": self.name}
			)
			salary_detail._doc_before_save = copy.deepcopy(salary_detail)
			salary_detail.db_set(field, value)
			salary_detail.db_update()
			salary_detail.save_version()
