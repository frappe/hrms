# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class EmployeeOtherIncome(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		amount: DF.Currency
		company: DF.Link
		employee: DF.Link
		employee_name: DF.Data | None
		payroll_period: DF.Link
		source: DF.Data | None
	# end: auto-generated types

	def validate(self):
		for doctype, name in (("Employee", self.employee), ("Payroll Period", self.payroll_period)):
			company = frappe.db.get_value(doctype, name, "company")
			if company != self.company:
				frappe.throw(
					_("{0} {1} belongs to company {2}, not {3}").format(
						_(doctype), frappe.bold(name), frappe.bold(company), frappe.bold(self.company)
					),
					title=_("Company Mismatch"),
				)
