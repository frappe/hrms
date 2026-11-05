# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, formatdate, getdate, rounded

from hrms.hr.utils import (
	validate_active_employee,
)
from hrms.payroll.doctype.employee_benefit_claim.employee_benefit_claim import get_salary_structure_assignment


class EmployeeBenefitApplication(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.payroll.doctype.employee_benefit_application_detail.employee_benefit_application_detail import (
			EmployeeBenefitApplicationDetail,
		)

		amended_from: DF.Link | None
		company: DF.Link
		currency: DF.Link
		date: DF.Date
		department: DF.Link | None
		employee: DF.Link
		employee_benefits: DF.Table[EmployeeBenefitApplicationDetail]
		employee_name: DF.Data | None
		max_benefits: DF.Currency
		payroll_period: DF.Link
		remaining_benefit: DF.Currency
		total_amount: DF.Currency
	# end: auto-generated types

	def validate(self):
		validate_active_employee(self.employee)
		self.validate_payroll_period()
		self.validate_duplicate_on_payroll_period()
		if self.employee_benefits:
			self.set_benefit_limits()
			self.validate_max_benefit()
			self.set_totals()
		else:
			frappe.throw(_("As per your assigned Salary Structure you cannot apply for benefits"))

	def validate_payroll_period(self):
		start_date, end_date = frappe.db.get_value(
			"Payroll Period", self.payroll_period, ["start_date", "end_date"]
		)
		if not (getdate(start_date) <= getdate(self.date) <= getdate(end_date)):
			frappe.throw(
				_("Date {0} is not within Payroll Period {1}").format(
					formatdate(self.date), self.payroll_period
				)
			)

	def set_benefit_limits(self):
		salary_structure_assignment = get_salary_structure_assignment(self.employee, self.date)
		max_benefit_amounts = dict(
			frappe.get_all(
				"Employee Benefit Detail",
				filters={"parent": salary_structure_assignment, "parenttype": "Salary Structure Assignment"},
				fields=["salary_component", "amount"],
				as_list=True,
			)
		)
		self.max_benefits, self.currency = frappe.db.get_value(
			"Salary Structure Assignment", salary_structure_assignment, ["max_benefits", "currency"]
		)

		for benefit in self.employee_benefits:
			if benefit.salary_component not in max_benefit_amounts:
				frappe.throw(
					_("Row {0}: {1} is not a benefit in Salary Structure Assignment {2}").format(
						benefit.idx, benefit.salary_component, salary_structure_assignment
					)
				)
			benefit.max_benefit_amount = max_benefit_amounts[benefit.salary_component]

	def set_totals(self):
		self.total_amount = sum(flt(benefit.amount) for benefit in self.employee_benefits)
		self.remaining_benefit = flt(self.max_benefits) - self.total_amount

	def validate_max_benefit(self):
		total_benefit_amount = 0
		for benefit in self.employee_benefits:
			if not benefit.amount or benefit.amount <= 0:
				frappe.throw(
					_("Benefit amount of component {0} should be greater than 0").format(
						benefit.salary_component
					)
				)
			elif benefit.amount > benefit.max_benefit_amount:
				frappe.throw(
					_("Benefit amount of component {0} exceeds {1}").format(
						benefit.salary_component, benefit.max_benefit_amount
					)
				)
			total_benefit_amount += flt(benefit.amount)

		if rounded(total_benefit_amount, 2) > self.max_benefits:
			frappe.throw(
				_("Sum of benefit amounts {0} exceeds maximum limit of {1}").format(
					total_benefit_amount, self.max_benefits
				)
			)

	def validate_duplicate_on_payroll_period(self):
		application = frappe.db.exists(
			"Employee Benefit Application",
			{"employee": self.employee, "payroll_period": self.payroll_period, "docstatus": 1},
		)
		if application:
			frappe.throw(
				_("Employee {0} already submitted an application {1} for the payroll period {2}").format(
					self.employee, application, self.payroll_period
				)
			)

	@frappe.whitelist()
	def set_benefit_components_and_currency(self) -> None:
		# get employee benefits from salary structure assignment and populate the employee benefits table
		self.employee_benefits = []
		salary_structure_assignment = get_salary_structure_assignment(self.employee, self.date)

		if not salary_structure_assignment:
			frappe.throw(
				_("No Salary Structure Assignment found for employee {0} on date {1}").format(
					self.employee, cstr(self.date)
				)
			)

		EmployeeBenefitDetail = frappe.qb.DocType("Employee Benefit Detail")
		employee_benefits = (
			frappe.qb.from_(EmployeeBenefitDetail)
			.select(EmployeeBenefitDetail.salary_component, EmployeeBenefitDetail.amount)
			.where(EmployeeBenefitDetail.parent == salary_structure_assignment)
			.run(as_dict=True)
		)

		if employee_benefits:
			max_benefits, currency = frappe.db.get_value(
				"Salary Structure Assignment", salary_structure_assignment, ["max_benefits", "currency"]
			)
			self.max_benefits = max_benefits
			self.currency = currency

			for benefit in employee_benefits:
				self.append(
					"employee_benefits",
					{"salary_component": benefit.salary_component, "max_benefit_amount": benefit.amount},
				)
