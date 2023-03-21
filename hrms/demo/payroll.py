import random

import frappe
from frappe.utils import get_year_ending, get_year_start, getdate

# from hrms.demo.utils import Batch


class DemoPayrollPeriod:
	def __init__(self, start_date: str = None, end_date: str = None):
		self.start_date = start_date or get_year_start(getdate())
		self.end_date = end_date or get_year_ending(getdate())

	def create_payroll_period(self):
		try:
			payroll_period = frappe.get_doc(
				{
					"doctype": "Payroll Period",
					"__newname": f"{self.start_date} - {self.end_date}",
					"start_date": self.start_date,
					"end_date": self.end_date,
					"company": frappe.db.get_single_value("Global Defaults", "default_company"),
				}
			).insert()
		except frappe.DuplicateEntryError:
			payroll_period = frappe.get_doc("Payroll Period", f"{self.start_date} - {self.end_date}")

		return payroll_period


class DemoIncomeTaxSlab:
	def __init__(self, tax_slab_name: str = None, tax_slabs: list = None):
		self.tax_slab_name = tax_slab_name or "Demo Income Tax Slab"
		self.tax_slabs = tax_slabs or [
			{
				"from_amount": 250000,
				"to_amount": 500000,
				"percent_deduction": 5,
				"condition": "annual_taxable_earning > 500000",
			},
			{"from_amount": 500001, "to_amount": 1000000, "percent_deduction": 20},
			{"from_amount": 1000001, "percent_deduction": 30},
		]

	def create_income_tax_slab(self):
		try:
			tax_slab = frappe.get_doc(
				{
					"doctype": "Income Tax Slab",
					"__newname": self.tax_slab_name,
					"slabs": self.tax_slabs,
					"company": frappe.db.get_single_value("Global Defaults", "default_company"),
					"currency": "INR",
					"effective_from": get_year_start(getdate()),
					"standard_tax_exemption_amount": 50000,
				}
			).insert()
			tax_slab.submit()

		except frappe.DuplicateEntryError:
			tax_slab = frappe.get_doc("Income Tax Slab", self.tax_slab_name)

		return tax_slab


class DemoSalaryStructure:
	def __init__(self):
		self._earnings = []
		self._deductions = []

	@property
	def earnings(self):
		if not self._earnings:
			self._earnings = frappe.get_all("Salary Component", {"type": "Earning"}, "*")

		return self._earnings

	@property
	def deductions(self):
		if not self._deductions:
			self._deductions = frappe.get_all("Salary Component", {"type": "Deduction"}, "*")

		return self._deductions

	def create_salary_structure(self, struct_id):
		doc = frappe.new_doc("Salary Structure")

		doc.update(
			{
				"__newname": f"Sal Struct {struct_id}",
				"company": frappe.db.get_single_value("Global Defaults", "default_company"),
				"earnings": self.set_earning_components(),
				"deductions": self.set_deduction_components(),
			}
		)

		doc.save(ignore_permissions=True)

	def set_earning_components(self):
		earnings = []
		for earning in self.earnings:
			row = {"salary_component": earning.salary_component, "amount": random.randint(30000, 60000)}
			earnings.append(row)

		return earnings

	def set_deduction_components(self):
		deductions = []
		for deduction in self.deductions:
			row = {"salary_component": deduction.salary_component, "amount": random.randint(500, 5000)}
			deductions.append(row)

		return deductions


class DemoSalaryStructureAssignment:
	pass


class DemoPayrollEntry:
	pass


class DemoAdditionalSalary:
	pass


class DemoPayroll:
	pass
