# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _, bold
from frappe.model.document import Document
from frappe.utils import flt, format_date, get_link_to_form, getdate

from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController

from hrms.hr.doctype.leave_application.leave_application import get_leaves_for_period
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry
from hrms.hr.utils import set_employee_name, validate_active_employee
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
	get_assigned_salary_structure,
)


class LeaveEncashment(AccountsController):
	def validate(self):
		set_employee_name(self)
		validate_active_employee(self.employee)
		self.encashment_date = self.encashment_date or getdate()
		self.get_leave_details_for_encashment()
		self.set_status()

		if not self.pay_via_payment_entry:
			self.set_salary_structure()

	def set_salary_structure(self):
		self._salary_structure = get_assigned_salary_structure(self.employee, self.encashment_date)
		if not self._salary_structure:
			frappe.throw(
				_("No Salary Structure assigned to Employee {0} on the given date {1}").format(
					self.employee, frappe.bold(format_date(self.encashment_date))
				)
			)

	def before_submit(self):
		if not self.encashment_amount or self.encashment_amount <= 0:
			frappe.throw(_("You can only submit Leave Encashment for a valid encashment amount"))

	def on_submit(self):
		if not self.leave_allocation:
			self.db_set("leave_allocation", self.get_leave_allocation().get("name"))

		if self.pay_via_payment_entry:
			self.create_gl_entries()
		else:
			self.create_additional_salary()

		self.set_encashed_leaves_in_allocation()
		self.create_leave_ledger_entry()

	def on_cancel(self):
		if self.additional_salary:
			frappe.get_doc("Additional Salary", self.additional_salary).cancel()
			self.db_set("additional_salary", "")

		if self.leave_allocation:
			frappe.db.set_value(
				"Leave Allocation",
				self.leave_allocation,
				"total_leaves_encashed",
				frappe.db.get_value("Leave Allocation", self.leave_allocation, "total_leaves_encashed")
				- self.encashment_days,
			)

		if self.pay_via_payment_entry:
			self.create_gl_entries(cancel=True)

		self.create_leave_ledger_entry(submit=False)
		self.ignore_linked_doctypes = ["GL Entry", "Payment Ledger Entry", "Advance Payment Ledger Entry"]
		self.set_status(update=True)

	@frappe.whitelist()
	def get_leave_details_for_encashment(self):
		self.set_leave_balance()
		self.set_actual_encashable_days()
		self.set_encashment_days()
		self.set_encashment_amount()

	def get_encashment_settings(self):
		return frappe.get_cached_value(
			"Leave Type",
			self.leave_type,
			["allow_encashment", "non_encashable_leaves", "max_encashable_leaves"],
			as_dict=True,
		)

	def set_actual_encashable_days(self):
		encashment_settings = self.get_encashment_settings()
		if not encashment_settings.allow_encashment:
			frappe.throw(_("Leave Type {0} is not encashable").format(self.leave_type))

		self.actual_encashable_days = self.leave_balance
		leave_form_link = get_link_to_form("Leave Type", self.leave_type)

		# TODO: Remove this weird setting if possible. Retained for backward compatibility
		if encashment_settings.non_encashable_leaves:
			actual_encashable_days = self.leave_balance - encashment_settings.non_encashable_leaves
			self.actual_encashable_days = actual_encashable_days if actual_encashable_days > 0 else 0
			frappe.msgprint(
				_("Excluded {0} Non-Encashable Leaves for {1}").format(
					bold(encashment_settings.non_encashable_leaves),
					leave_form_link,
				),
			)

		if encashment_settings.max_encashable_leaves:
			self.actual_encashable_days = min(
				self.actual_encashable_days, encashment_settings.max_encashable_leaves
			)
			frappe.msgprint(
				_("Maximum encashable leaves for {0} are {1}").format(
					leave_form_link, bold(encashment_settings.max_encashable_leaves)
				),
				title=_("Encashment Limit Applied"),
			)

	def set_encashment_days(self):
		# allow overwriting encashment days
		if not self.encashment_days:
			self.encashment_days = self.actual_encashable_days

		if self.encashment_days > self.actual_encashable_days:
			frappe.throw(
				_("Encashment Days cannot exceed {0} {1} as per Leave Type settings").format(
					bold(_("Actual Encashable Days")),
					self.actual_encashable_days,
				)
			)

	def set_leave_balance(self):
		allocation = self.get_leave_allocation()
		if not allocation:
			frappe.throw(
				_("No Leaves Allocated to Employee: {0} for Leave Type: {1}").format(
					self.employee, self.leave_type
				)
			)

		self.leave_balance = (
			allocation.total_leaves_allocated
			- allocation.carry_forwarded_leaves_count
			# adding this because the function returns a -ve number
			+ get_leaves_for_period(
				self.employee, self.leave_type, allocation.from_date, self.encashment_date
			)
		)
		self.leave_allocation = allocation.name

	def create_additional_salary(self):
		additional_salary = frappe.new_doc("Additional Salary")
		additional_salary.company = frappe.get_value("Employee", self.employee, "company")
		additional_salary.employee = self.employee
		additional_salary.currency = self.currency
		earning_component = frappe.get_value("Leave Type", self.leave_type, "earning_component")
		if not earning_component:
			frappe.throw(_("Please set Earning Component for Leave type: {0}.").format(self.leave_type))
		additional_salary.salary_component = earning_component
		additional_salary.payroll_date = self.encashment_date
		additional_salary.amount = self.encashment_amount
		additional_salary.overwrite_salary_structure_amount = 0
		additional_salary.ref_doctype = self.doctype
		additional_salary.ref_docname = self.name
		additional_salary.submit()

	def set_encashed_leaves_in_allocation(self):
		frappe.db.set_value(
			"Leave Allocation",
			self.leave_allocation,
			"total_leaves_encashed",
			frappe.db.get_value("Leave Allocation", self.leave_allocation, "total_leaves_encashed")
			+ self.encashment_days,
		)

	def set_encashment_amount(self):
		if not hasattr(self, "_salary_structure"):
			self.set_salary_structure()

		per_day_encashment = frappe.get_value(
			"Salary Structure Assignment",
			filters={
				"employee": self.employee,
				"salary_structure": self._salary_structure,
				"docstatus": 1,
				"from_date": ["<=", self.encashment_date],
			},
			fieldname=["leave_encashment_amount_per_day"],
			order_by="from_date desc",
		)

		if not per_day_encashment:
			per_day_encashment = frappe.db.get_value(
				"Salary Structure",
				self._salary_structure,
				"leave_encashment_amount_per_day",
			)

		per_day_encashment = per_day_encashment or 0

		self.encashment_amount = self.encashment_days * per_day_encashment if per_day_encashment > 0 else 0

	def set_status(self, update=False):
		precision = self.precision("paid_amount")
		status = None

		if self.docstatus == 0:
			status = "Draft"
		elif self.docstatus == 1:
			if flt(self.encashment_amount) > flt(self.paid_amount, precision):
				status = "Unpaid"
			else:
				status = "Paid"
		elif self.docstatus == 2:
			status = "Cancelled"

		if update:
			self.db_set("status", status)
			self.notify_update()
		else:
			self.status = status

	def get_leave_allocation(self):
		date = self.encashment_date or getdate()

		LeaveAllocation = frappe.qb.DocType("Leave Allocation")
		leave_allocation = (
			frappe.qb.from_(LeaveAllocation)
			.select(
				LeaveAllocation.name,
				LeaveAllocation.from_date,
				LeaveAllocation.to_date,
				LeaveAllocation.total_leaves_allocated,
				LeaveAllocation.carry_forwarded_leaves_count,
			)
			.where(
				((LeaveAllocation.from_date <= date) & (date <= LeaveAllocation.to_date))
				& (LeaveAllocation.docstatus == 1)
				& (LeaveAllocation.leave_type == self.leave_type)
				& (LeaveAllocation.employee == self.employee)
			)
		).run(as_dict=True)

		return leave_allocation[0] if leave_allocation else None

	def create_leave_ledger_entry(self, submit=True):
		args = frappe._dict(
			leaves=self.encashment_days * -1,
			from_date=self.encashment_date,
			to_date=self.encashment_date,
			is_carry_forward=0,
		)
		create_leave_ledger_entry(self, args, submit)

		# create reverse entry for expired leaves
		leave_allocation = self.get_leave_allocation()
		if not leave_allocation:
			return

		to_date = leave_allocation.get("to_date")

		can_expire = not frappe.db.get_value("Leave Type", self.leave_type, "is_carry_forward")
		if to_date < getdate() and can_expire:
			args = frappe._dict(
				leaves=self.encashment_days, from_date=to_date, to_date=to_date, is_carry_forward=0
			)
			create_leave_ledger_entry(self, args, submit)

	def set_total_advance_paid(self):
		from frappe.query_builder.functions import Abs, Sum

		aple = frappe.qb.DocType("Advance Payment Ledger Entry")
		paid_amount = (
			frappe.qb.from_(aple)
			.select(Abs(Sum(aple.amount)).as_("paid_amount"))
			.where(
				(aple.company == self.company)
				& (aple.against_voucher_type == self.doctype)
				& (aple.against_voucher_no == self.name)
				& (aple.delinked == 0)
			)
		).run(as_dict=True)[0].paid_amount or 0
		if flt(paid_amount) > self.encashment_amount:
			frappe.throw(_("Row {0}# Paid Amount cannot be greater than Encashment amount"))

		self.db_set("paid_amount", paid_amount)
		self.set_status(update=True)

	def create_gl_entries(self, cancel=False):
		gl_entries = self.get_gl_entries()
		make_gl_entries(gl_entries, cancel)

	def get_gl_entries(self):
		gl_entry = []

		# payable entry
		gl_entry.append(
			self.get_gl_dict(
				{
					"account": self.payable_account,
					"credit": self.encashment_amount,
					"credit_in_account_currency": self.encashment_amount,
					"against": self.expense_account,
					"party_type": "Employee",
					"party": self.employee,
					"against_voucher_type": self.doctype,
					"against_voucher": self.name,
					"cost_center": self.cost_center,
				},
				item=self,
			)
		)

		# expense entry
		gl_entry.append(
			self.get_gl_dict(
				{
					"account": self.expense_account,
					"debit": self.encashment_amount,
					"debit_in_account_currency": self.encashment_amount,
					"against": self.payable_account,
					"cost_center": self.cost_center,
				},
				item=self,
			)
		)

		return gl_entry

	def on_discard(self):
		self.db_set("status", "Cancelled")


def create_leave_encashment(leave_allocation):
	"""Creates leave encashment for the given allocations"""
	for allocation in leave_allocation:
		if not get_assigned_salary_structure(allocation.employee, allocation.to_date):
			continue
		leave_encashment = frappe.get_doc(
			dict(
				doctype="Leave Encashment",
				leave_period=allocation.leave_period,
				employee=allocation.employee,
				leave_type=allocation.leave_type,
				encashment_date=allocation.to_date,
			)
		)
		leave_encashment.insert(ignore_permissions=True)
