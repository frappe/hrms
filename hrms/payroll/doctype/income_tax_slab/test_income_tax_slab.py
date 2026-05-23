# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.employee_tax_exemption_declaration.test_employee_tax_exemption_declaration import (
	create_payroll_period,
)
from hrms.payroll.doctype.income_tax_slab.income_tax_slab import (
	calculate_base_tax_from_tax_slabs,
	calculate_other_charges,
	calculate_tax_by_tax_slab,
)
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from hrms.tests.utils import HRMSTestSuite

SIMPLE_SLABS = [
	{"from_amount": 0, "to_amount": 300000, "percent_deduction": 0, "condition": ""},
	{"from_amount": 300000, "to_amount": 700000, "percent_deduction": 5, "condition": ""},
	{"from_amount": 700000, "to_amount": 1000000, "percent_deduction": 10, "condition": ""},
	{"from_amount": 1000000, "to_amount": 0, "percent_deduction": 30, "condition": ""},
]


def make_slab(slabs, other_taxes_and_charges=None, tax_relief_limit=0):
	return frappe._dict(
		slabs=[frappe._dict(**s) for s in slabs],
		surcharge_slabs=[],
		other_taxes_and_charges=[frappe._dict(**c) for c in (other_taxes_and_charges or [])],
		tax_relief_limit=tax_relief_limit,
	)


SIMPLE_SLABS = [
	{"from_amount": 0, "to_amount": 300000, "percent_deduction": 0, "condition": ""},
	{"from_amount": 300000, "to_amount": 700000, "percent_deduction": 5, "condition": ""},
	{"from_amount": 700000, "to_amount": 1000000, "percent_deduction": 10, "condition": ""},
	{"from_amount": 1000000, "to_amount": 0, "percent_deduction": 30, "condition": ""},
]


class TestIncomeTaxSlab(HRMSTestSuite):
	def setUp(self):
		self.slab = make_income_tax_slab(SIMPLE_SLABS)
		self.slab_with_cess = make_income_tax_slab(
			SIMPLE_SLABS,
			other_taxes_and_charges=[
				{"description": "cess", "percent": 4, "min_taxable_income": 0, "max_taxable_income": 0}
			],
		)

	# calculate_other_charges

	def test_other_charges_applied_as_flat_rate(self):
		"""Charges in other_taxes_and_charges are a flat percentage — no marginal relief logic."""
		base_tax = calculate_base_tax_from_tax_slabs(self.slab_with_cess, 1500000, None, {})

		_, cess = calculate_other_charges(self.slab_with_cess, 1500000, base_tax)

		self.assertEqual(cess, base_tax * 4 / 100)

	def test_other_charges_no_marginal_relief_at_threshold(self):
		"""A surcharge row in other_taxes_and_charges at an income where marginal relief
		would normally apply is still computed as a plain percentage — no relief reduction."""
		# Income just above 50L — where marginal relief would apply if using surcharge_slabs
		income = 5100000
		slab = make_income_tax_slab(
			SIMPLE_SLABS,
			other_taxes_and_charges=[
				{
					"description": "Surcharge 10%",
					"percent": 10,
					"min_taxable_income": 0,
					"max_taxable_income": 0,
				}
			],
		)
		base_tax = calculate_base_tax_from_tax_slabs(slab, income, None, {})

		_, surcharge = calculate_other_charges(slab, income, base_tax)

		self.assertEqual(surcharge, base_tax * 10 / 100)

	def test_other_charges_skipped_outside_income_range(self):
		"""Charges with min/max taxable income bounds are skipped when income is outside the range."""
		slab = make_income_tax_slab(
			SIMPLE_SLABS,
			other_taxes_and_charges=[
				{
					"description": "High income cess",
					"percent": 4,
					"min_taxable_income": 10000000,
					"max_taxable_income": 0,
				}
			],
		)
		base_tax = calculate_base_tax_from_tax_slabs(slab, 1500000, None, {})

		_, charge = calculate_other_charges(slab, 1500000, base_tax)

		self.assertEqual(charge, 0)

	# calculate_tax_by_tax_slab

	def test_zero_tax_below_relief_limit(self):
		"""Income at or below tax_relief_limit returns zero tax."""
		slab = make_income_tax_slab(SIMPLE_SLABS, tax_relief_limit=700000)

		tax, _ = calculate_tax_by_tax_slab(700000, slab, None, {})

		self.assertEqual(tax, 0)

	def test_tax_calculated_above_relief_limit(self):
		"""Income above tax_relief_limit produces non-zero tax."""
		slab = make_income_tax_slab(SIMPLE_SLABS, tax_relief_limit=700000)

		tax, _ = calculate_tax_by_tax_slab(800000, slab, None, {})

		self.assertGreater(tax, 0)

	def test_cess_computed_on_base_tax(self):
		"""other_taxes_and_charges (cess) is computed on the running tax total passed in."""
		base_tax = calculate_base_tax_from_tax_slabs(self.slab_with_cess, 1500000, None, {})
		total_tax, charges = calculate_tax_by_tax_slab(1500000, self.slab_with_cess, None, {})

		expected_cess = base_tax * 4 / 100
		self.assertEqual(charges, expected_cess)
		self.assertEqual(total_tax, base_tax + expected_cess)

	def test_surcharge_then_cess_reflected_in_salary_slip_tds(self):
		"""Integration: TDS on a salary slip equals (base_tax + 10% surcharge + 4% cess) / 12.
		Surcharge is applied first, so cess base is base_tax + surcharge — not base_tax alone."""
		income_tax_slab = frappe.get_doc(
			{
				"doctype": "Income Tax Slab",
				"name": "_Test Slab Surcharge Cess",
				"effective_from": "2024-04-01",
				"currency": "INR",
				"tax_relief_limit": 0,
				"slabs": [
					{"from_amount": 0, "to_amount": 300000, "percent_deduction": 0},
					{"from_amount": 300000, "to_amount": 700000, "percent_deduction": 5},
					{"from_amount": 700000, "to_amount": 1000000, "percent_deduction": 10},
					{"from_amount": 1000000, "to_amount": 0, "percent_deduction": 30},
				],
				"other_taxes_and_charges": [
					{
						"description": "Surcharge 10%",
						"percent": 10,
						"min_taxable_income": 5000000,
						"max_taxable_income": 0,
					},
					{
						"description": "Cess 4%",
						"percent": 4,
						"min_taxable_income": 0,
						"max_taxable_income": 0,
					},
				],
			}
		)
		income_tax_slab.insert(ignore_permissions=True)
		income_tax_slab.submit()

		payroll_period = create_payroll_period(
			name="_Test Payroll Period Surcharge Cess", company="_Test Company"
		)
		employee = make_employee("test_surcharge_cess@salary.slip", company="_Test Company")

		salary_structure = make_salary_structure(
			"Structure for Surcharge Cess Test",
			"Monthly",
			test_tax=True,
			employee=employee,
			payroll_period=payroll_period,
			company="_Test Company",
			base=600000,  # ₹7.2 M annual — in 10% surcharge band (min_taxable_income: 50L)
		)

		ssa_name = frappe.db.get_value("Salary Structure Assignment", {"employee": employee, "docstatus": 1})
		frappe.db.set_value("Salary Structure Assignment", ssa_name, "income_tax_slab", income_tax_slab.name)

		# Post on the first day of the payroll period → remaining_sub_periods = 12
		salary_slip = make_salary_slip(
			salary_structure.name,
			employee=employee,
			posting_date=payroll_period.start_date,
		)

		tds = next((d.amount for d in salary_slip.deductions if d.salary_component == "TDS"), 0)

		annual_income = salary_slip.annual_taxable_amount
		base_tax = calculate_base_tax_from_tax_slabs(income_tax_slab, annual_income, None, {})
		surcharge = base_tax * 10 / 100
		cess = (base_tax + surcharge) * 4 / 100
		expected_tds = round((base_tax + surcharge + cess) / 12)

		self.assertEqual(tds, expected_tds)


def make_income_tax_slab(slabs, other_taxes_and_charges=None, tax_relief_limit=0):
	return frappe._dict(
		slabs=[frappe._dict(**s) for s in slabs],
		surcharge_slabs=[],
		other_taxes_and_charges=[frappe._dict(**c) for c in (other_taxes_and_charges or [])],
		tax_relief_limit=tax_relief_limit,
	)
