# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, getdate

from hrms.hr.utils import update_employee_work_history, validate_employee_active_on


class EmployeeTransfer(Document):
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
		create_new_employee_id: DF.Check
		department: DF.Link | None
		employee: DF.Link
		employee_name: DF.Data | None
		new_company: DF.Link | None
		new_employee_id: DF.Link | None
		reallocate_leaves: DF.Check
		transfer_date: DF.Date
		transfer_details: DF.Table[EmployeePropertyHistory]
	# end: auto-generated types

	def validate(self):
		validate_employee_active_on(self.employee, self.transfer_date)

	def before_submit(self):
		if getdate(self.transfer_date) > getdate():
			frappe.throw(
				_("Employee Transfer cannot be submitted before Transfer Date"),
				frappe.DocstatusTransitionError,
			)
		self.add_implicit_property_changes()

	def add_implicit_property_changes(self):
		self.transfer_details = [
			d
			for d in self.transfer_details
			if d.fieldname != "date_of_joining" and not (d.fieldname == "user_id" and d.current == d.new)
		]
		employee = frappe.db.get_value(
			"Employee", self.employee, ["date_of_joining", "user_id"], as_dict=True
		)

		if self.create_new_employee_id:
			if employee.user_id and not self.validate_user_in_details():
				self.append_property_change(_("User ID"), "user_id", employee.user_id, employee.user_id)
		elif self.new_company and self.company != self.new_company:
			self.append_property_change(
				_("Date of Joining"), "date_of_joining", employee.date_of_joining, self.transfer_date
			)

		for idx, d in enumerate(self.transfer_details, 1):
			d.idx = idx

	def append_property_change(self, label, fieldname, current, new):
		self.append(
			"transfer_details",
			{"property": label, "fieldname": fieldname, "current": cstr(current), "new": cstr(new)},
		)

	def on_submit(self):
		employee = frappe.get_doc("Employee", self.employee)
		if self.create_new_employee_id:
			new_employee = frappe.copy_doc(employee)
			new_employee.name = None
			new_employee.employee_number = None
			new_employee = update_employee_work_history(
				new_employee, self.transfer_details, date=self.transfer_date
			)
			if self.new_company and self.company != self.new_company:
				new_employee.internal_work_history = []
				new_employee.date_of_joining = self.transfer_date
				new_employee.company = self.new_company
			# move user_id to new employee before insert
			if employee.user_id and not self.validate_user_in_details():
				new_employee.user_id = employee.user_id
				employee.db_set("user_id", "")
			new_employee.insert()
			self.db_set("new_employee_id", new_employee.name)
			# relieve the old employee
			employee.db_set("relieving_date", self.transfer_date)
			employee.db_set("status", "Left")
		else:
			employee = update_employee_work_history(employee, self.transfer_details, date=self.transfer_date)
			if self.new_company and self.company != self.new_company:
				employee.company = self.new_company
				employee.date_of_joining = self.transfer_date
			employee.save()

	def on_cancel(self):
		employee = frappe.get_doc("Employee", self.employee)
		if self.create_new_employee_id:
			if self.new_employee_id:
				frappe.throw(
					_("Please delete the Employee {0} to cancel this document").format(
						f"<a href='/app/Form/Employee/{self.new_employee_id}'>{self.new_employee_id}</a>"
					)
				)
			# mark the employee as active
			employee.status = "Active"
			employee.relieving_date = ""
			self.restore_user_id(employee)
		else:
			employee = update_employee_work_history(
				employee, self.transfer_details, date=self.transfer_date, cancel=True
			)
		if self.new_company != self.company:
			employee.company = self.company
		employee.save()

	def restore_user_id(self, employee):
		if employee.user_id or self.validate_user_in_details():
			return

		user_id = next((d.current for d in self.transfer_details if d.fieldname == "user_id"), None)
		if user_id and not frappe.db.exists("Employee", {"user_id": user_id}):
			employee.user_id = user_id

	def validate_user_in_details(self):
		for item in self.transfer_details:
			if item.fieldname == "user_id" and item.new != item.current:
				return True
		return False
