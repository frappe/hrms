# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, add_months, get_first_day, get_last_day, nowdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.employee_tax_exemption_declaration.test_employee_tax_exemption_declaration import (
	create_payroll_period,
)
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from hrms.payroll.doctype.salary_structure.test_salary_structure import (
	create_salary_structure_assignment,
	get_payable_account,
	make_salary_structure,
)
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
	get_employee_currency,
)
from hrms.tests.utils import HRMSTestSuite


def _make_component(name, abbr, comp_type="Earning", **flags):
	if frappe.db.exists("Salary Component", name):
		frappe.delete_doc("Salary Component", name, force=True)
	doc = frappe.new_doc("Salary Component")
	doc.update({"salary_component": name, "salary_component_abbr": abbr, "type": comp_type})
	doc.update(flags)
	return doc.insert()


def _make_slip_custom_field(fieldname, fieldtype="Float", default=None):
	if frappe.db.exists("Custom Field", {"dt": "Salary Slip", "fieldname": fieldname}):
		return
	return frappe.get_doc(
		doctype="Custom Field",
		dt="Salary Slip",
		fieldname=fieldname,
		label=fieldname.replace("_", " ").title(),
		fieldtype=fieldtype,
		default=default,
		insert_after="net_pay",
	).insert()


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

	def test_regional_ctc_hook_reaches_ctc_but_not_gross(self):
		emp = make_employee("ssa_regional_ctc@test.com", company="_Test Company")

		_make_component("SSA Test Basic", "SSATB", "Earning", amount_based_on_formula=1, formula="base")
		_make_component("SSA Test Regional Employer", "SSATRE", "Employer Contribution")

		make_salary_structure(
			"SSA Test Regional CTC Structure",
			"Monthly",
			employee=emp,
			company="_Test Company",
			base=50000,
			earnings=[
				{
					"salary_component": "SSA Test Basic",
					"abbr": "SSATB",
					"amount_based_on_formula": 1,
					"formula": "base",
				}
			],
			deductions=[],
		)
		ssa = frappe.get_last_doc("Salary Structure Assignment", filters={"employee": emp})

		def inject(rows_by_type, data):
			rows_by_type["employer_contributions"].append(
				frappe._dict(
					salary_component="SSA Test Regional Employer",
					abbr="SSATRE",
					default_amount=2700,
					statistical_component=0,
					do_not_include_in_total=0,
				)
			)

		ssa.apply_regional_ctc_components = inject
		ssa.calculate_ctc_and_gross()

		self.assertEqual(ssa.annual_gross_earning, 50000 * 12)
		self.assertEqual(ssa.ctc, (50000 + 2700) * 12)

	def test_ctc_for_fixed_amount_structure_without_base(self):
		emp = make_employee("ssa_ctc_nobase@test.com", company="_Test Company")
		_make_component("SSA Test Fixed Basic", "SSATFB", "Earning")
		make_salary_structure(
			"SSA Test No Base Structure",
			"Monthly",
			company="_Test Company",
			earnings=[{"salary_component": "SSA Test Fixed Basic", "abbr": "SSATFB", "amount": 30000}],
			deductions=[],
		)
		ssa = frappe.new_doc("Salary Structure Assignment")
		ssa.employee = emp
		ssa.salary_structure = "SSA Test No Base Structure"
		ssa.company = "_Test Company"
		ssa.from_date = get_first_day(nowdate())
		ssa.base = 0
		ssa.calculate_ctc_and_gross()
		self.assertEqual(ssa.ctc, 30000 * 12)
		self.assertEqual(ssa.annual_gross_earning, 30000 * 12)

		ssa.salary_structure = None
		ssa.calculate_ctc_and_gross()
		self.assertEqual(ssa.ctc, 0)

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

	def test_get_evaluated_components_resolves_salary_slip_fields(self):
		"""A component formula may reference any salary slip field (e.g. start_date),
		since the slip evaluates formulas against its own as_dict. SSA evaluation has
		no slip, so it must mirror a full-cycle preview slip's field set; otherwise the
		formula raises a NameError on the missing slip field."""
		emp = make_employee("ssa_slip_field@test.com", company="_Test Company")

		# formula references start_date -- a salary-slip field, absent from the SSA itself
		formula = "base * getdate(start_date).month"
		_make_component(
			"SSA Test Period Bonus", "SSATPB", "Earning", amount_based_on_formula=1, formula=formula
		)
		earnings = [
			{
				"salary_component": "SSA Test Period Bonus",
				"abbr": "SSATPB",
				"amount_based_on_formula": 1,
				"formula": formula,
			},
		]

		make_salary_structure(
			"SSA Test Slip Field Structure",
			"Monthly",
			employee=emp,
			company="_Test Company",
			base=1000,
			earnings=earnings,
			deductions=[],
		)
		ssa = frappe.get_last_doc("Salary Structure Assignment", filters={"employee": emp})

		# full-cycle start_date is the first of the SSA's from_date month, so the
		# component resolves to base * that month (proving start_date was seeded correctly)
		expected = 1000 * get_first_day(ssa.from_date).month
		components = {r.salary_component: r.default_amount for r in ssa.get_evaluated_components().earnings}
		self.assertEqual(components["SSA Test Period Bonus"], expected)

	def test_get_evaluated_components_resolves_uncovered_slip_fields(self):
		emp = make_employee("ssa_uncovered_field@test.com", company="_Test Company")

		condition = "gross_year_to_date < 74600"
		formula = "base + gross_year_to_date + month_to_date + year_to_date + unmarked_days"
		_make_component(
			"SSA Test Basic YTD", "SSATBYTD", "Earning", amount_based_on_formula=1, formula="base"
		)
		_make_component(
			"SSA Test YTD Guard", "SSATYG", "Deduction", amount_based_on_formula=1, formula=formula
		)

		earnings = [
			{
				"salary_component": "SSA Test Basic YTD",
				"abbr": "SSATBYTD",
				"amount_based_on_formula": 1,
				"formula": "base",
			},
		]
		deductions = [
			{
				"salary_component": "SSA Test YTD Guard",
				"abbr": "SSATYG",
				"amount_based_on_formula": 1,
				"formula": formula,
				"condition": condition,
			},
		]

		make_salary_structure(
			"SSA Test Uncovered Field Structure",
			"Monthly",
			employee=emp,
			company="_Test Company",
			base=50000,
			earnings=earnings,
			deductions=deductions,
		)
		ssa = frappe.get_last_doc("Salary Structure Assignment", filters={"employee": emp})

		components = {r.salary_component: r.default_amount for r in ssa.get_evaluated_components().deductions}
		self.assertEqual(components["SSA Test YTD Guard"], 50000)

	def test_get_evaluated_components_resolves_salary_slip_custom_field(self):
		"""A formula referencing a Custom Field on Salary Slip must not raise NameError
		when the assignment evaluates it without a slip (#5141)."""
		emp = make_employee("ssa_custom_field@test.com", company="_Test Company")
		_make_slip_custom_field("custom_shift_allowance_rate")

		formula = "base + custom_shift_allowance_rate"
		_make_component(
			"SSA Test Shift Allowance", "SSATSA", "Earning", amount_based_on_formula=1, formula=formula
		)
		earnings = [
			{
				"salary_component": "SSA Test Shift Allowance",
				"abbr": "SSATSA",
				"amount_based_on_formula": 1,
				"formula": formula,
			},
		]

		make_salary_structure(
			"SSA Test Custom Field Structure",
			"Monthly",
			employee=emp,
			company="_Test Company",
			base=50000,
			earnings=earnings,
			deductions=[],
		)
		ssa = frappe.get_last_doc("Salary Structure Assignment", filters={"employee": emp})

		components = {r.salary_component: r.default_amount for r in ssa.get_evaluated_components().earnings}
		self.assertEqual(components["SSA Test Shift Allowance"], 50000)

	def test_get_evaluated_components_uses_declared_field_defaults(self):
		"""A slip field's declared default must reach the formula. exchange_rate
		defaults to 1.0, so seeding a bare 0 would zero out any formula using it."""
		emp = make_employee("ssa_field_default@test.com", company="_Test Company")
		_make_slip_custom_field("custom_shift_multiplier", fieldtype="Float", default="2")

		formula = "base * exchange_rate * custom_shift_multiplier"
		_make_component(
			"SSA Test Shift Multiplier", "SSATSM", "Earning", amount_based_on_formula=1, formula=formula
		)
		earnings = [
			{
				"salary_component": "SSA Test Shift Multiplier",
				"abbr": "SSATSM",
				"amount_based_on_formula": 1,
				"formula": formula,
			},
		]

		make_salary_structure(
			"SSA Test Field Default Structure",
			"Monthly",
			employee=emp,
			company="_Test Company",
			base=1000,
			earnings=earnings,
			deductions=[],
		)
		ssa = frappe.get_last_doc("Salary Structure Assignment", filters={"employee": emp})

		components = {r.salary_component: r.default_amount for r in ssa.get_evaluated_components().earnings}
		self.assertEqual(components["SSA Test Shift Multiplier"], 2000)

	def test_get_evaluated_components_seeds_posting_date(self):
		"""A full cycle seeds posting_date to the cycle end date."""
		emp = make_employee("ssa_posting_date@test.com", company="_Test Company")

		formula = "base * getdate(posting_date).day"
		_make_component(
			"SSA Test Posting Bonus", "SSATPOB", "Earning", amount_based_on_formula=1, formula=formula
		)
		earnings = [
			{
				"salary_component": "SSA Test Posting Bonus",
				"abbr": "SSATPOB",
				"amount_based_on_formula": 1,
				"formula": formula,
			},
		]

		make_salary_structure(
			"SSA Test Posting Date Structure",
			"Monthly",
			employee=emp,
			company="_Test Company",
			base=1000,
			earnings=earnings,
			deductions=[],
		)
		ssa = frappe.get_last_doc("Salary Structure Assignment", filters={"employee": emp})

		expected = 1000 * get_last_day(ssa.from_date).day
		components = {r.salary_component: r.default_amount for r in ssa.get_evaluated_components().earnings}
		self.assertEqual(components["SSA Test Posting Bonus"], expected)

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

	def test_assignment_dated_before_any_fiscal_year(self):
		"""Long-running assignments can predate the oldest fiscal year. Evaluating their
		components (on submit and for every salary slip) must not require a fiscal year
		covering from_date."""
		formula = "getdate(start_date).day * 100 + getdate(end_date).day"
		_make_component(
			"SSA Test Cycle Days", "SSATCD", "Earning", amount_based_on_formula=1, formula=formula
		)
		earnings = [
			{
				"salary_component": "SSA Test Cycle Days",
				"abbr": "SSATCD",
				"amount_based_on_formula": 1,
				"formula": formula,
			},
		]

		# expected = start day * 100 + end day of the full cycle containing from_date
		cases = (
			("Monthly", "2005-04-10", 130),  # 01-30 April
			("Bimonthly", "2005-04-10", 115),  # 01-15 April
			("Bimonthly", "2004-02-20", 1629),  # 16-29 February, leap year
		)
		for idx, (frequency, from_date, expected) in enumerate(cases):
			with self.subTest(frequency=frequency, from_date=from_date):
				self.assertFalse(
					frappe.db.exists(
						"Fiscal Year",
						{"year_start_date": ("<=", from_date), "year_end_date": (">=", from_date)},
					)
				)
				emp = make_employee(
					f"ssa_old_assignment_{idx}@test.com",
					company="_Test Company",
					date_of_joining="2004-01-01",
				)
				structure = make_salary_structure(
					f"SSA Test Old Assignment {idx}",
					frequency,
					employee=emp,
					from_date=from_date,
					company="_Test Company",
					base=1000,
					earnings=earnings,
					deductions=[],
				)
				ssa = frappe.get_last_doc("Salary Structure Assignment", filters={"employee": emp})
				self.assertEqual(ssa.docstatus, 1)

				components = {
					r.salary_component: r.default_amount for r in ssa.get_evaluated_components().earnings
				}
				self.assertEqual(components["SSA Test Cycle Days"], expected)

				slip = make_salary_slip(structure.name, employee=emp)
				self.assertIn("SSA Test Cycle Days", [r.salary_component for r in slip.earnings])

	def _new_assignment(self, emp, structure, **kwargs):
		ssa = frappe.new_doc("Salary Structure Assignment")
		ssa.update(
			{
				"employee": emp,
				"salary_structure": structure,
				"company": "_Test Company",
				"currency": "INR",
				"from_date": get_first_day(nowdate()),
				"base": 50000,
				"payroll_payable_account": get_payable_account("_Test Company"),
			}
		)
		ssa.update(kwargs)
		return ssa

	def _fixed_structure(self, name, **kwargs):
		_make_component("SSA Test Fixed Basic", "SSATFB", "Earning")
		return make_salary_structure(
			name,
			"Monthly",
			company="_Test Company",
			earnings=[{"salary_component": "SSA Test Fixed Basic", "abbr": "SSATFB", "amount": 30000}],
			deductions=[],
			**kwargs,
		)

	def test_opening_entries_only_for_first_assignment_in_period(self):
		payroll_period = create_payroll_period(company="_Test Company")
		structure = make_salary_structure(
			"SSA Test Opening Structure", "Monthly", company="_Test Company", test_tax=True
		)
		first_from = add_months(payroll_period.start_date, 2)
		emp = make_employee(
			"ssa_opening_revision@test.com", company="_Test Company", date_of_joining=first_from
		)

		first = self._new_assignment(emp, structure.name, from_date=first_from)
		self.assertTrue(first.are_opening_entries_required())

		create_salary_structure_assignment(
			emp, structure.name, from_date=first_from, payroll_period=payroll_period
		)
		revision = self._new_assignment(
			emp, structure.name, from_date=add_months(payroll_period.start_date, 6)
		)
		self.assertFalse(revision.are_opening_entries_required())

	def test_opening_entries_rejected_when_already_set_in_period(self):
		payroll_period = create_payroll_period(company="_Test Company")
		structure = make_salary_structure(
			"SSA Test Opening Structure", "Monthly", company="_Test Company", test_tax=True
		)
		first_from = add_months(payroll_period.start_date, 2)
		emp = make_employee(
			"ssa_opening_duplicate@test.com", company="_Test Company", date_of_joining=first_from
		)
		create_salary_structure_assignment(
			emp, structure.name, from_date=first_from, payroll_period=payroll_period
		)
		first = frappe.get_last_doc("Salary Structure Assignment", {"employee": emp})
		first.db_set({"taxable_earnings_till_date": 300000, "tax_deducted_till_date": 10000})

		revision_from = add_months(payroll_period.start_date, 6)
		income_tax_slab = first.income_tax_slab
		for opening in ({"taxable_earnings_till_date": 300000}, {"tax_deducted_till_date": 5000}):
			revision = self._new_assignment(
				emp, structure.name, from_date=revision_from, income_tax_slab=income_tax_slab, **opening
			)
			self.assertRaises(frappe.ValidationError, revision.insert)

		self._new_assignment(
			emp, structure.name, from_date=revision_from, income_tax_slab=income_tax_slab
		).insert()

	def test_structure_and_tax_slab_must_be_submitted(self):
		emp = make_employee("ssa_draft_links@test.com", company="_Test Company")
		draft_structure = self._fixed_structure("SSA Test Draft Structure", dont_submit=True)
		self.assertRaises(frappe.ValidationError, self._new_assignment(emp, draft_structure.name).insert)

		structure = self._fixed_structure("SSA Test Submitted Structure")
		if frappe.db.exists("Income Tax Slab", "_Test SSA Draft Slab"):
			frappe.delete_doc("Income Tax Slab", "_Test SSA Draft Slab", force=True)
		draft_slab = frappe.get_doc(
			{
				"doctype": "Income Tax Slab",
				"name": "_Test SSA Draft Slab",
				"effective_from": get_first_day(nowdate()),
				"currency": "INR",
				"slabs": [{"from_amount": 0, "to_amount": 0, "percent_deduction": 10}],
			}
		).insert()
		self.assertRaises(
			frappe.ValidationError,
			self._new_assignment(emp, structure.name, income_tax_slab=draft_slab.name).insert,
		)

	def test_cost_center_percentages_summing_to_100(self):
		emp = make_employee("ssa_cost_centers@test.com", company="_Test Company")
		structure = self._fixed_structure("SSA Test Cost Center Structure")
		parent = frappe.db.get_value("Cost Center", {"company": "_Test Company", "is_group": 1})
		cost_centers = []
		for i in range(3):
			name = frappe.db.get_value("Cost Center", {"cost_center_name": f"_Test SSA CC {i}"})
			if not name:
				name = (
					frappe.get_doc(
						{
							"doctype": "Cost Center",
							"cost_center_name": f"_Test SSA CC {i}",
							"company": "_Test Company",
							"parent_cost_center": parent,
						}
					)
					.insert()
					.name
				)
			cost_centers.append(name)

		ssa = self._new_assignment(emp, structure.name)
		for cost_center, percentage in zip(cost_centers, (28.57, 44.44, 26.99), strict=True):
			ssa.append("payroll_cost_centers", {"cost_center": cost_center, "percentage": percentage})
		ssa.validate_cost_centers()

	def test_payroll_payable_account_of_other_company_rejected(self):
		emp = make_employee("ssa_payable_account@test.com", company="_Test Company")
		structure = self._fixed_structure("SSA Test Payable Structure")
		other_account = frappe.db.get_value(
			"Account", {"company": "_Test Company 1", "root_type": "Liability", "is_group": 0}
		)
		ssa = self._new_assignment(emp, structure.name, payroll_payable_account=other_account)
		self.assertRaises(frappe.ValidationError, ssa.validate_payroll_payable_account)

	def test_employee_currency_from_submitted_assignment(self):
		emp = make_employee("ssa_employee_currency@test.com", company="_Test Company")
		inr_structure = self._fixed_structure("SSA Test Currency INR")
		self._new_assignment(emp, inr_structure.name, from_date=add_days(nowdate(), -30)).submit()
		usd_structure = self._fixed_structure("SSA Test Currency USD", currency="USD")
		self._new_assignment(
			emp, usd_structure.name, currency="USD", from_date=add_days(nowdate(), -10)
		).insert()

		self.assertEqual(get_employee_currency(emp), "INR")
