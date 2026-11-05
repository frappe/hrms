# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from hrms.hr.utils import update_employee_work_history, validate_employee_active_on


class EmployeePromotion(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.employee_property_history.employee_property_history import (
			EmployeePropertyHistory,
		)

		amended_from: DF.Link | None
		company: DF.Link | None
		current_ctc: DF.Currency
		department: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data | None
		promotion_date: DF.Date
		promotion_details: DF.Table[EmployeePropertyHistory]
		revised_ctc: DF.Currency
		salary_currency: DF.Link | None
	# end: auto-generated types

	def validate(self):
		validate_employee_active_on(self.employee, self.promotion_date)

	def before_submit(self):
		if getdate(self.promotion_date) > getdate():
			frappe.throw(
				_("Employee Promotion cannot be submitted before Promotion Date"),
				frappe.DocstatusTransitionError,
			)

	def on_submit(self):
		employee = frappe.get_doc("Employee", self.employee)
		employee = update_employee_work_history(employee, self.promotion_details, date=self.promotion_date)

		if self.revised_ctc and not self.get_other_ctc_revision(">"):
			employee.ctc = self.revised_ctc

		employee.save()

	def on_cancel(self):
		employee = frappe.get_doc("Employee", self.employee)
		employee = update_employee_work_history(
			employee, self.promotion_details, date=self.promotion_date, cancel=True
		)

		if self.revised_ctc and not self.get_other_ctc_revision(">"):
			employee.ctc = self.get_other_ctc_revision("<") or self.current_ctc

		employee.save()

	def get_other_ctc_revision(self, operator):
		revision = frappe.get_all(
			"Employee Promotion",
			filters={
				"employee": self.employee,
				"docstatus": 1,
				"revised_ctc": (">", 0),
				"promotion_date": (operator, self.promotion_date),
				"name": ("!=", self.name),
			},
			pluck="revised_ctc",
			order_by="promotion_date desc",
			limit=1,
		)
		return revision[0] if revision else None
