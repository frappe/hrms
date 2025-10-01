# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, rounded

from hrms.hr.utils import (
	validate_active_employee,
)
from hrms.payroll.doctype.employee_benefit_claim.employee_benefit_claim import get_salary_structure_assignment


class EmployeeBenefitApplication(Document):
	def validate(self):
		validate_active_employee(self.employee)
		self.validate_duplicate_on_payroll_period()
		if self.employee_benefits:
			self.validate_max_benefit()
		else:
			frappe.throw(_("As per your assigned Salary Structure you cannot apply for benefits"))

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
	def set_benefit_components_and_currency(self):
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
