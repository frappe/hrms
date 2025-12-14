# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, bold
from frappe.query_builder.functions import Abs, Sum
from frappe.utils import cstr, flt, get_datetime, get_link_to_form

from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController


class Gratuity(AccountsController):
	def validate(self):
		data = self.calculate_work_experience_and_amount()
		self.current_work_experience = data["current_work_experience"]
		self.amount = data["amount"]
		self.set_status()

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
		self.create_gl_entries(cancel=True)
		self.set_status(update=True)

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
			work_experience = round(work_experience)
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
		if payroll_based_on == "Leave":
			total_lwp = self.get_non_working_days(relieving_date, "On Leave")
			total_working_days -= total_lwp
		elif payroll_based_on == "Attendance":
			total_absent = self.get_non_working_days(relieving_date, "Absent")
			total_working_days -= total_absent

		return total_working_days

	def get_non_working_days(self, relieving_date: str, status: str) -> float:
		filters = {
			"docstatus": 1,
			"status": status,
			"employee": self.employee,
			"attendance_date": ("<=", get_datetime(relieving_date)),
		}

		if status == "On Leave":
			lwp_leave_types = frappe.get_all("Leave Type", filters={"is_lwp": 1}, pluck="name")
			filters["leave_type"] = ("IN", lwp_leave_types)

		record = frappe.get_all("Attendance", filters=filters, fields=[{"COUNT": "*", "as": "total_lwp"}])
		return record[0].total_lwp if len(record) else 0

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

		# consider full payment days for calculation as last month's salary slip
		# might have less payment days as per attendance, making it non-deterministic
		salary_slip.payment_days = salary_slip.total_working_days
		salary_slip.calculate_net_pay()

		total_amount = 0
		component_found = False
		for row in salary_slip.earnings:
			if row.salary_component in applicable_earning_components:
				total_amount += flt(row.amount)
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
