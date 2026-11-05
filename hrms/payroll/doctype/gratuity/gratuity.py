# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import math

import frappe
from frappe import _, bold
from frappe.query_builder.functions import Abs, Sum
from frappe.utils import cstr, flt, get_datetime, get_link_to_form

from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController

from hrms.hr.doctype.full_and_final_statement.full_and_final_statement import (
	get_amount_paid_via_full_and_final_statement,
)


class Gratuity(AccountsController):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		amount: DF.Currency
		company: DF.Link
		cost_center: DF.Link | None
		current_work_experience: DF.Float
		department: DF.Link | None
		designation: DF.Data | None
		employee: DF.Link
		employee_name: DF.Data | None
		expense_account: DF.Link | None
		gratuity_rule: DF.Link
		mode_of_payment: DF.Link | None
		paid_amount: DF.Currency
		pay_via_salary_slip: DF.Check
		payable_account: DF.Link | None
		payroll_date: DF.Date | None
		posting_date: DF.Date
		salary_component: DF.Link | None
		status: DF.Literal["Draft", "Unpaid", "Paid", "Submitted", "Cancelled"]
	# end: auto-generated types

	def validate(self):
		self.validate_duplicate()
		data = self.calculate_work_experience_and_amount()
		self.current_work_experience = data["current_work_experience"]
		self.amount = data["amount"]
		self.set_status()

	def validate_duplicate(self):
		if existing := frappe.db.exists(
			"Gratuity", {"employee": self.employee, "docstatus": ("<", 2), "name": ("!=", self.name or "")}
		):
			frappe.throw(
				_("Gratuity {0} already exists for employee {1}").format(
					get_link_to_form("Gratuity", existing), bold(self.employee)
				),
				title=_("Duplicate Gratuity"),
			)

	@property
	def gratuity_settings(self):
		if not hasattr(self, "_gratuity_settings"):
			self._gratuity_settings = frappe.db.get_value(
				"Gratuity Rule",
				self.gratuity_rule,
				[
					"work_experience_calculation_function as method",
					"total_working_days_per_year",
					"minimum_year_for_gratuity",
					"calculate_gratuity_amount_based_on",
				],
				as_dict=True,
			)

		return self._gratuity_settings

	def set_status(self, update=False):
		status = {"0": "Draft", "1": "Submitted", "2": "Cancelled"}[cstr(self.docstatus or 0)]

		if self.docstatus == 1:
			precision = self.precision("paid_amount")
			if flt(self.paid_amount) > 0 and flt(self.amount, precision) == flt(self.paid_amount, precision):
				status = "Paid"
			else:
				status = "Unpaid"

		if update and self.status != status:
			self.db_set("status", status)
		else:
			self.status = status

	def on_submit(self):
		if self.pay_via_salary_slip:
			self.create_additional_salary()
		else:
			self.create_gl_entries()

	def on_cancel(self):
		self.ignore_linked_doctypes = ["GL Entry", "Payment Ledger Entry", "Advance Payment Ledger Entry"]
		if self.pay_via_salary_slip:
			self.cancel_additional_salary()
		else:
			self.create_gl_entries(cancel=True)
		self.set_status(update=True)

	def cancel_additional_salary(self):
		additional_salary = frappe.db.get_value(
			"Additional Salary", {"ref_doctype": self.doctype, "ref_docname": self.name, "docstatus": 1}
		)
		if additional_salary:
			frappe.get_doc("Additional Salary", additional_salary).cancel()

	def create_gl_entries(self, cancel=False):
		gl_entries = self.get_gl_entries()
		make_gl_entries(gl_entries, cancel)

	def get_gl_entries(self):
		gl_entry = []
		# payable entry
		if self.amount:
			gl_entry.append(
				self.get_gl_dict(
					{
						"account": self.payable_account,
						"credit": self.amount,
						"credit_in_account_currency": self.amount,
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

			# expense entries
			gl_entry.append(
				self.get_gl_dict(
					{
						"account": self.expense_account,
						"debit": self.amount,
						"debit_in_account_currency": self.amount,
						"against": self.payable_account,
						"cost_center": self.cost_center,
					},
					item=self,
				)
			)
		else:
			frappe.throw(_("Total Amount cannot be zero"))

		return gl_entry

	def create_additional_salary(self):
		if self.pay_via_salary_slip:
			additional_salary = frappe.new_doc("Additional Salary")
			additional_salary.employee = self.employee
			additional_salary.salary_component = self.salary_component
			additional_salary.overwrite_salary_structure_amount = 0
			additional_salary.amount = self.amount
			additional_salary.payroll_date = self.payroll_date
			additional_salary.company = self.company
			additional_salary.ref_doctype = self.doctype
			additional_salary.ref_docname = self.name
			additional_salary.submit()

	def set_total_advance_paid(self):
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
		paid_amount = flt(paid_amount) + get_amount_paid_via_full_and_final_statement(self.doctype, self.name)

		if flt(paid_amount) > self.amount:
			frappe.throw(_("Row {0}# Paid Amount cannot be greater than Total amount"))

		self.db_set("paid_amount", paid_amount)
		self.set_status(update=True)

	@frappe.whitelist()
	def calculate_work_experience_and_amount(self) -> dict:
		if self.gratuity_settings.method == "Manual":
			current_work_experience = flt(self.current_work_experience)
		else:
			current_work_experience = self.get_work_experience()

		gratuity_amount = self.get_gratuity_amount(current_work_experience)

		return {"current_work_experience": current_work_experience, "amount": gratuity_amount}

	def get_work_experience(self) -> float:
		total_working_days = self.get_total_working_days()
		rule = self.gratuity_settings
		work_experience = total_working_days / (rule.total_working_days_per_year or 1)

		if rule.method == "Round off Work Experience":
			work_experience = math.floor(work_experience + 0.5)
		else:
			work_experience = flt(work_experience, self.precision("current_work_experience"))

		if work_experience < rule.minimum_year_for_gratuity:
			frappe.throw(
				_("Employee: {0} have to complete minimum {1} years for gratuity").format(
					bold(self.employee), rule.minimum_year_for_gratuity
				)
			)
		return work_experience or 0

	def get_total_working_days(self) -> float:
		date_of_joining, relieving_date = frappe.db.get_value(
			"Employee", self.employee, ["date_of_joining", "relieving_date"]
		)
		if not relieving_date:
			frappe.throw(
				_("Please set Relieving Date for employee: {0}").format(
					bold(get_link_to_form("Employee", self.employee))
				)
			)

		total_working_days = (get_datetime(relieving_date) - get_datetime(date_of_joining)).days

		payroll_based_on = frappe.db.get_single_value("Payroll Settings", "payroll_based_on") or "Leave"
		total_working_days -= self.get_non_working_days(relieving_date, payroll_based_on == "Attendance")

		return total_working_days

	def get_non_working_days(self, relieving_date: str, include_absence: bool) -> float:
		attendance = frappe.get_all(
			"Attendance",
			filters={
				"docstatus": 1,
				"status": ("in", ["On Leave", "Half Day", "Absent"]),
				"employee": self.employee,
				"attendance_date": ("<=", get_datetime(relieving_date)),
			},
			fields=["status", "leave_type", "half_day_status"],
		)
		leave_types = {
			d.name: d
			for d in frappe.get_all(
				"Leave Type",
				filters={"name": ("in", list({d.leave_type for d in attendance if d.leave_type}))},
				fields=["name", "is_lwp", "is_ppl", "fraction_of_daily_salary_per_leave"],
			)
		}

		non_working_days = 0
		for d in attendance:
			if d.status == "Absent":
				non_working_days += 1 if include_absence else 0
				continue

			day_fraction = 0.5 if d.status == "Half Day" else 1
			leave_type = leave_types.get(d.leave_type)
			if leave_type and leave_type.is_lwp:
				non_working_days += day_fraction
			elif leave_type and leave_type.is_ppl:
				non_working_days += day_fraction * (1 - flt(leave_type.fraction_of_daily_salary_per_leave))

			if include_absence and d.status == "Half Day" and d.half_day_status == "Absent":
				non_working_days += 0.5

		return non_working_days

	def get_gratuity_amount(self, experience: float) -> float:
		total_component_amount = self.get_total_component_amount()
		calculate_amount_based_on = self.gratuity_settings.calculate_gratuity_amount_based_on

		gratuity_amount = 0
		slabs = self.get_gratuity_rule_slabs()
		slab_found = False
		years_left = experience

		for slab in slabs:
			if calculate_amount_based_on == "Current Slab":
				if self._is_experience_within_slab(slab, experience):
					gratuity_amount = (
						total_component_amount * experience * slab.fraction_of_applicable_earnings
					)
					if slab.fraction_of_applicable_earnings:
						slab_found = True

				if slab_found:
					break

			elif calculate_amount_based_on == "Sum of all previous slabs":
				# no slabs, fraction applicable for all years
				if slab.to_year == 0 and slab.from_year == 0:
					gratuity_amount += (
						years_left * total_component_amount * slab.fraction_of_applicable_earnings
					)
					slab_found = True
					break

				# completed more years than the current slab, so consider fraction for current slab too
				if self._is_experience_beyond_slab(slab, experience):
					gratuity_amount += (
						(slab.to_year - slab.from_year)
						* total_component_amount
						* slab.fraction_of_applicable_earnings
					)
					years_left -= slab.to_year - slab.from_year
					slab_found = True

				elif self._is_experience_within_slab(slab, experience):
					gratuity_amount += (
						years_left * total_component_amount * slab.fraction_of_applicable_earnings
					)
					slab_found = True
					break

		if not slab_found:
			frappe.throw(
				_(
					"No applicable slab found for the calculation of gratuity amount as per the Gratuity Rule: {0}"
				).format(bold(self.gratuity_rule))
			)

		return flt(gratuity_amount, self.precision("amount"))

	def get_total_component_amount(self) -> float:
		applicable_earning_components = self.get_applicable_components()
		salary_slip = get_last_salary_slip(self.employee)
		if not salary_slip:
			frappe.throw(_("No Salary Slip found for Employee: {0}").format(bold(self.employee)))

		total_amount = 0
		component_found = False
		for row in salary_slip.earnings:
			if row.salary_component in applicable_earning_components:
				total_amount += flt(row.default_amount)
				component_found = True

		if not component_found:
			frappe.throw(
				_("No applicable Earning component found in last salary slip for Gratuity Rule: {0}").format(
					bold(get_link_to_form("Gratuity Rule", self.gratuity_rule))
				)
			)

		return total_amount

	def get_applicable_components(self) -> list[str]:
		applicable_earning_components = frappe.get_all(
			"Gratuity Applicable Component", filters={"parent": self.gratuity_rule}, pluck="salary_component"
		)
		if not applicable_earning_components:
			frappe.throw(
				_("No applicable Earning components found for Gratuity Rule: {0}").format(
					bold(get_link_to_form("Gratuity Rule", self.gratuity_rule))
				)
			)

		return applicable_earning_components

	def get_gratuity_rule_slabs(self) -> list[dict]:
		return frappe.get_all(
			"Gratuity Rule Slab",
			filters={"parent": self.gratuity_rule},
			fields=["from_year", "to_year", "fraction_of_applicable_earnings"],
			order_by="idx",
		)

	def _is_experience_within_slab(self, slab: dict, experience: float) -> bool:
		return bool(slab.from_year <= experience and (experience <= slab.to_year or slab.to_year == 0))

	def _is_experience_beyond_slab(self, slab: dict, experience: float) -> bool:
		return bool(slab.from_year < experience and (slab.to_year < experience and slab.to_year != 0))

	def on_discard(self):
		self.db_set("status", "Cancelled")


def get_last_salary_slip(employee: str) -> dict | None:
	salary_slip = frappe.db.get_value(
		"Salary Slip", {"employee": employee, "docstatus": 1}, order_by="start_date desc"
	)
	if salary_slip:
		return frappe.get_doc("Salary Slip", salary_slip)
