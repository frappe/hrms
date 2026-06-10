# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import get_first_day, nowdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from hrms.tests.utils import HRMSTestSuite


def _make_component(name, abbr, comp_type="Earning", **flags):
	if frappe.db.exists("Salary Component", name):
		frappe.delete_doc("Salary Component", name, force=True)
	doc = frappe.new_doc("Salary Component")
	doc.update({"salary_component": name, "salary_component_abbr": abbr, "type": comp_type})
	doc.update(flags)
	return doc.insert()


class TestSalaryStructureAssignment(HRMSTestSuite):
	def test_ctc_and_annual_gross_exclude_statistical_and_include_employer(self):
		"""base=50000; gross = Basic (50000) only - statistical earning (1000) is
		excluded; CTC = gross + employer contribution (6000)."""
		emp = make_employee("ssa_ctc_calc@test.com", company="_Test Company")

		_make_component("SSA Test Basic", "SSATB", "Earning", amount_based_on_formula=1, formula="base")
		_make_component("SSA Test Statistical", "SSATS", "Earning", statistical_component=1)
		_make_component("SSA Test Employer PF", "SSATEPF", "Employer Contribution")

		earnings = [
			{
				"salary_component": "SSA Test Basic",
				"abbr": "SSATB",
				"amount_based_on_formula": 1,
				"formula": "base",
			},
			{
				"salary_component": "SSA Test Statistical",
				"abbr": "SSATS",
				"statistical_component": 1,
				"amount": 1000,
			},
		]
		employer_contributions = [
			{"salary_component": "SSA Test Employer PF", "abbr": "SSATEPF", "amount": 6000},
		]

		make_salary_structure(
			"SSA Test CTC Structure",
			"Monthly",
			employee=emp,
			company="_Test Company",
			base=50000,
			earnings=earnings,
			deductions=[],
			other_details={"employer_contributions": employer_contributions},
		)
		ssa = frappe.get_last_doc("Salary Structure Assignment", filters={"employee": emp})

		self.assertEqual(ssa.annual_gross_earning, 50000 * 12)
		self.assertEqual(ssa.ctc, (50000 + 6000) * 12)

	def test_ctc_reset_when_base_missing(self):
		emp = make_employee("ssa_ctc_nobase@test.com", company="_Test Company")
		make_salary_structure("SSA Test No Base Structure", "Monthly", company="_Test Company")
		ssa = frappe.new_doc("Salary Structure Assignment")
		ssa.employee = emp
		ssa.salary_structure = "SSA Test No Base Structure"
		ssa.company = "_Test Company"
		ssa.from_date = get_first_day(nowdate())
		ssa.base = 0
		ssa.calculate_ctc_and_gross()
		self.assertEqual(ssa.ctc, 0)
		self.assertEqual(ssa.annual_gross_earning, 0)

	def test_get_evaluated_components_does_not_mutate_cached_structure(self):
		emp = make_employee("ssa_cache@test.com", company="_Test Company")
		make_salary_structure(
			"SSA Test Cache Structure", "Monthly", employee=emp, company="_Test Company", base=50000
		)
		ssa = frappe.get_last_doc("Salary Structure Assignment", filters={"employee": emp})

		ssa.get_evaluated_components()
		# the cached Salary Structure doc's earning rows must not carry a stamped default_amount
		cached = frappe.get_cached_doc("Salary Structure", "SSA Test Cache Structure")
		self.assertTrue(all(not r.get("default_amount") for r in cached.earnings))

	def test_do_not_include_in_total_earning_is_in_ctc_but_not_gross(self):
		"""A 'Do Not Include in Total' earning is part of CTC but not payable - it
		must be excluded from annual_gross_earning yet included in ctc."""
		emp = make_employee("ssa_dniit@test.com", company="_Test Company")

		_make_component("SSA Test Basic Pay", "SSATBP", "Earning", amount_based_on_formula=1, formula="base")
		_make_component("SSA Test Company Car", "SSATCAR", "Earning", do_not_include_in_total=1)

		earnings = [
			{
				"salary_component": "SSA Test Basic Pay",
				"abbr": "SSATBP",
				"amount_based_on_formula": 1,
				"formula": "base",
			},
			{
				"salary_component": "SSA Test Company Car",
				"abbr": "SSATCAR",
				"amount": 2000,
				"do_not_include_in_total": 1,
			},
		]

		make_salary_structure(
			"SSA Test DNIIT Structure",
			"Monthly",
			employee=emp,
			company="_Test Company",
			base=50000,
			earnings=earnings,
			deductions=[],
		)
		ssa = frappe.get_last_doc("Salary Structure Assignment", filters={"employee": emp})

		self.assertEqual(ssa.annual_gross_earning, 50000 * 12)
		self.assertEqual(ssa.ctc, (50000 + 2000) * 12)

	def test_ctc_for_timesheet_structure_evaluates_base_driven_components(self):
		"""For a timesheet-based structure, only the wage component is paid as
		hour_rate * hours (variable, excluded from CTC). The rest of the structure
		(base-driven components) must still evaluate normally into gross / ctc."""
		emp = make_employee("ssa_ts_ctc@test.com", company="_Test Company")

		# wage component is the structure-level timesheet component, NOT an earning row
		_make_component("SSA TS Wage", "SSATSW", "Earning")
		_make_component("SSA TS Basic", "SSATSB", "Earning", amount_based_on_formula=1, formula="base")

		earnings = [
			{
				"salary_component": "SSA TS Basic",
				"abbr": "SSATSB",
				"amount_based_on_formula": 1,
				"formula": "base",
			},
		]

		make_salary_structure(
			"SSA Timesheet Structure",
			"Monthly",
			employee=emp,
			company="_Test Company",
			base=50000,
			earnings=earnings,
			deductions=[],
			other_details={
				"salary_slip_based_on_timesheet": 1,
				"hour_rate": 50,
				"salary_component": "SSA TS Wage",
			},
		)
		ssa = frappe.get_last_doc("Salary Structure Assignment", filters={"employee": emp})

		# base-driven earning evaluates normally; the variable hourly wage is excluded from CTC
		self.assertEqual(ssa.annual_gross_earning, 50000 * 12)
		self.assertEqual(ssa.ctc, 50000 * 12)

	def test_get_evaluated_components_excludes_timesheet_wage(self):
		"""SSA evaluation is period-independent: the timesheet wage (hour_rate * hours)
		is built by the salary slip, not SSA. get_evaluated_components must return only
		the structure's declared components, never an injected wage row."""
		emp = make_employee("ssa_ts_eval@test.com", company="_Test Company")

		_make_component("SSA TS2 Wage", "SSATS2W", "Earning")
		_make_component("SSA TS2 Basic", "SSATS2B", "Earning", amount_based_on_formula=1, formula="base")

		earnings = [
			{
				"salary_component": "SSA TS2 Basic",
				"abbr": "SSATS2B",
				"amount_based_on_formula": 1,
				"formula": "base",
			},
		]

		make_salary_structure(
			"SSA Timesheet Eval Structure",
			"Monthly",
			employee=emp,
			company="_Test Company",
			base=50000,
			earnings=earnings,
			deductions=[],
			other_details={
				"salary_slip_based_on_timesheet": 1,
				"hour_rate": 50,
				"salary_component": "SSA TS2 Wage",
			},
		)
		ssa = frappe.get_last_doc("Salary Structure Assignment", filters={"employee": emp})

		components = [r.salary_component for r in ssa.get_evaluated_components().earnings]
		self.assertNotIn("SSA TS2 Wage", components)
		self.assertIn("SSA TS2 Basic", components)
