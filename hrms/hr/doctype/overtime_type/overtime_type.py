# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class OvertimeType(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.overtime_salary_component.overtime_salary_component import (
			OvertimeSalaryComponent,
		)

		applicable_for_public_holiday: DF.Check
		applicable_for_weekend: DF.Check
		applicable_salary_component: DF.TableMultiSelect[OvertimeSalaryComponent]
		hourly_rate: DF.Currency
		maximum_overtime_hours_allowed: DF.Float
		overtime_calculation_method: DF.Literal["Salary Component Based", "Fixed Hourly Rate"]
		overtime_salary_component: DF.Link
		public_holiday_multiplier: DF.Float
		standard_multiplier: DF.Float
		weekend_multiplier: DF.Float
	# end: auto-generated types

	def validate(self):
		if self.overtime_calculation_method == "Salary Component Based":
			self.validate_applicable_components()
		self.validate_rates()

	def validate_rates(self):
		fields = ["standard_multiplier"]
		if self.applicable_for_weekend:
			fields.append("weekend_multiplier")
		if self.applicable_for_public_holiday:
			fields.append("public_holiday_multiplier")
		if self.overtime_calculation_method == "Fixed Hourly Rate":
			fields.append("hourly_rate")

		for fieldname in fields:
			if flt(self.get(fieldname)) <= 0:
				frappe.throw(_("{0} must be greater than zero").format(_(self.meta.get_label(fieldname))))

	def validate_applicable_components(self):
		if not len(self.applicable_salary_component):
			frappe.throw(_("Select Applicable Components for Overtime Type"))
