# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import calendar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from hrms.payroll.doctype.employee_benefit_ledger.employee_benefit_ledger import (
	delete_employee_benefit_ledger_entry,
)


class PayrollCorrection(Document):
	def validate(self):
		if self.days_to_reverse <= 0:
			frappe.throw(_("Days to Reverse must be greater than zero."))
		self.validate_days()
		self.populate_breakup_table()

	def on_submit(self):
		self.validate_arrear_details()
		self.create_additional_salary()
		self.create_benefit_ledger_entry()

	def validate_days(self):
		if self.days_to_reverse and self.salary_slip_reference:
			salary_slip = frappe.get_doc("Salary Slip", self.salary_slip_reference)
			self.working_days = salary_slip.total_working_days
			self.payment_days = salary_slip.payment_days
			self.lwp_days = max((salary_slip.total_working_days - salary_slip.payment_days), 0)
			payroll_corrections = frappe.get_all(
				"Payroll Correction",
				filters={
					"docstatus": 1,
					"payroll_period": self.payroll_period,
					"salary_slip_reference": self.salary_slip_reference,
					"employee": self.employee,
					"name": ["!=", self.name],
				},
				fields=["days_to_reverse"],
			)
			total_days_reversed = sum(entry["days_to_reverse"] for entry in payroll_corrections) or 0
			if total_days_reversed + self.days_to_reverse > self.lwp_days:
				frappe.throw(
					_(
						"You cannot reverse more than the total LWP days {0}. You have already reversed {1} days for this employee."
					).format(self.lwp_days, total_days_reversed)
				)

	def on_cancel(self):
		delete_employee_benefit_ledger_entry("reference_document", self.name)

	@frappe.whitelist()
	def fetch_salary_slip_details(self):
		# Fetch salary slip details with LWP for the employee in the payroll period
		if not (self.employee and self.payroll_period and self.company):
			return {"months": [], "slip_details": []}

		slips = frappe.get_all(
			"Salary Slip",
			filters={
				"employee": self.employee,
				"docstatus": 1,
				"current_payroll_period": self.payroll_period,
				"company": self.company,
				"leave_without_pay": [">", 0],
			},
			fields=[
				"name",
				"payment_days",
				"start_date",
				"total_working_days",
			],
		)

		if not slips:
			frappe.msgprint(
				_("No Salary Slips with {0} found for employee {1} for payroll period {2}.").format(
					frappe.bold("Leave Without Pay"), self.employee, self.payroll_period
				)
			)
			return

		slip_details = []
		month_set = set()

		for slip in slips:
			start_date = slip.get("start_date")
			month_name = calendar.month_name[start_date.month]
			month_set.add(month_name)

			slip_details.append(
				{
					"salary_slip_reference": slip.get("name"),
					"absent_days": slip.get("absent_days"),
					"leave_without_pay": slip.get("leave_without_pay"),
					"month_name": month_name,
					"working_days": slip.get("total_working_days"),
					"payment_days": slip.get("payment_days"),
					"start_date": slip.get("start_date"),
				}
			)

		sorted_months = sorted(list(month_set))

		return {"months": sorted_months, "slip_details": slip_details}

	def populate_breakup_table(self):
		# Get arrear salary components from salary slip that are not additional salary and add amounts to the breakup table
		salary_slip = frappe.get_doc("Salary Slip", self.salary_slip_reference)

		precision = (
			salary_slip.precision("gross_pay")
			or frappe.db.get_single_value("System Settings", "currency_precision")
			or 2
		)
		if not salary_slip:
			frappe.throw(_("Salary Slip not found."))

		self.set("earning_arrears", [])
		self.set("deduction_arrears", [])
		self.set("accrual_arrears", [])

		salary_slip_components = {}
		arrear_components = []
		for section in ["earnings", "deductions"]:
			for item in getattr(salary_slip, section, []):
				if not item.additional_salary:
					salary_slip_components[item.salary_component] = {
						"default_amount": item.default_amount or 0,
						"section": "earning_arrears" if section == "earnings" else "deduction_arrears",
					}

		for item in getattr(salary_slip, "accrued_benefits", []):
			salary_slip_components[item.salary_component] = {
				"default_amount": item.amount or 0,
				"section": "accrual_arrears",
				"accrual_component": True,
			}

		# Fetch arrear components that exist in the salary slip
		if salary_slip_components:
			arrear_components = frappe.db.get_list(
				"Salary Component",
				filters={
					"arrear_component": 1,
					"name": ["in", salary_slip_components.keys()],
					"variable_based_on_taxable_salary": 0,
					"disabled": 0,
				},
				fields=["name"],
				pluck="name",
			)

		if not arrear_components:
			frappe.msgprint(
				_(
					"No arrear components found in the salary slip. Ensure Arrear Component is checked in the Salary Component master."
				)
			)
			return

		for component in arrear_components:
			component_data = salary_slip_components[component]

			if component_data.get("accrual_component"):
				total_working_days = salary_slip.get(
					"payment_days", 1
				)  # since accruals do not have default_amount field
			else:
				total_working_days = salary_slip.get("total_working_days", 1)

			per_day_amount = flt(component_data["default_amount"] / total_working_days)
			arrear_amount = flt(per_day_amount * self.days_to_reverse)

			self.append(
				component_data["section"],
				{"salary_component": component, "amount": flt(arrear_amount, precision)},
			)

	def validate_arrear_details(self):
		# Ensure that there are arrear details to process
		if not (self.earning_arrears or self.deduction_arrears or self.accrual_arrears):
			frappe.throw(_("No arrear details found"))

	def create_additional_salary(self):
		for component in (self.earning_arrears or []) + (self.deduction_arrears or []):
			additional_salary = frappe.get_doc(
				{
					"doctype": "Additional Salary",
					"employee": self.employee,
					"company": self.company,
					"payroll_date": self.payroll_date,
					"salary_component": component.salary_component,
					"currency": self.currency,
					"amount": component.amount,
					"ref_doctype": "Payroll Correction",
					"ref_docname": self.name,
					"overwrite_salary_structure_amount": 0,
				}
			)
			additional_salary.insert()
			additional_salary.submit()

	def create_benefit_ledger_entry(self):
		for component in self.accrual_arrears or []:
			if not component.salary_component or not component.amount:
				continue

			is_flexible_benefit = frappe.db.get_value(
				"Salary Component", component.salary_component, "is_flexible_benefit"
			)

			frappe.get_doc(
				{
					"doctype": "Employee Benefit Ledger",
					"employee": self.employee,
					"employee_name": self.employee_name,
					"company": self.company,
					"payroll_period": self.payroll_period,
					"salary_component": component.salary_component,
					"transaction_type": "Accrual",
					"amount": component.amount,
					"reference_doctype": "Payroll Correction",
					"reference_document": self.name,
					"remarks": "Accrual via Payroll Correction",
					"salary_slip": self.salary_slip_reference,
					"flexible_benefit": is_flexible_benefit,
				}
			).insert()
