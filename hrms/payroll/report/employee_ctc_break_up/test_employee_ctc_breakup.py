import frappe
from frappe.utils import add_months, flt, get_year_start, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.employee_tax_exemption_declaration.test_employee_tax_exemption_declaration import (
	create_payroll_period,
)
from hrms.payroll.doctype.salary_structure.test_salary_structure import (
	create_salary_structure_assignment,
	make_salary_structure,
)
from hrms.payroll.report.employee_ctc_break_up.employee_ctc_break_up import SalaryBreakupReport
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeCTCBreakup(HRMSTestSuite):
	"""
	`make_salary_structure` has the following setup
	    Earning Components:
	        - Basic (base set in salary structure assignment)
	        - HRA (fixed 3000)
	        - Special Allowance (base/2)
	    Deduction Components:
	        - Professional Tax (fixed 200)
	    Income Tax Details (only applicable if test_tax is set to True in salary structure):
	        - Slabs
	            - 0 to 250000: 0%
	            - 250000 to 500000: 5% if annual taxable income exceeds 50000 else 0%
	            - 500000 to 1000000: 20%
	            - Above 1000000: 30%
	        - Tax exemption of 50000
	        - 4% cess
	"""

	def test_ctc_summary_cards(self):
		test_data = {
			"Monthly": {
				# if
				"ctc": 1116000,
				"base": 60000,
				"currency": "INR",
				# test
				"annual_ctc": "₹ 1,116,000.00",
				"per_cycle_ctc": 93000,
				"gross_pay": 93000,
				"net_pay": 92800,  # gross pay - professional tax
			},
			"Fortnightly": {
				# if
				"ctc": 648000,
				"base": 16000,
				"currency": "USD",
				# test
				"annual_ctc": "$ 648,000.00",
				"per_cycle_ctc": 27000,
				"gross_pay": 27000,
				"net_pay": 26800,  # gross pay - professional tax
			},
		}

		for payroll_frequency, data in test_data.items():
			employee = make_employee(f"test_ctc{payroll_frequency}@example.com", company="_Test Company")
			salary_structure = make_salary_structure(
				"Test CTC Breakup", payroll_frequency=payroll_frequency, currency=data.get("currency")
			)
			salary_structure_assignment = create_salary_structure_assignment(
				employee, salary_structure.name, base=data.get("base"), currency=data.get("currency")
			)
			salary_structure_assignment.ctc = data.get("ctc")
			salary_structure_assignment.save()

			ctc_breakup = SalaryBreakupReport(employee, salary_structure_assignment.name)

			self.assertEqual(ctc_breakup.format_currency(ctc_breakup.ctc), data["annual_ctc"])
			self.assertEqual(ctc_breakup.get_per_cycle_ctc(), data["per_cycle_ctc"])
			self.assertEqual(ctc_breakup.gross_pay, data["gross_pay"])
			self.assertEqual(ctc_breakup.net_pay, data["net_pay"])

	def test_income_tax_net_pay_calculation_at_the_start_of_payroll_period(self):
		employee = make_employee("test_ctc@example.com", company="_Test Company")
		salary_structure = make_salary_structure(
			"Test CTC Breakup with Tax", payroll_frequency="Monthly", currency="INR", test_tax=True
		)
		salary_structure_assignment = create_salary_structure_assignment(
			employee, salary_structure.name, base=60000, currency="INR", from_date=get_year_start(getdate())
		)
		salary_structure_assignment.ctc = 1116000
		salary_structure_assignment.save()

		"""With the given setup, the annual tax will be,
            taxable_income = 1116000 (total earnings) - 2400 (Professional Tax) - 50000 (Tax Exemption) = 1063600
            Tax amount = 12500 (5% of 250000) + 100000 (20% of 500000) + 19080(30% of 63600) = 131580
            Cess = 4% of tax = 5263.2
            Total tax amount = 136843.2
            Monthly tax = flt(136843.25 / 12) = 11404
            Monthly net pay = Gross pay - Professional Tax - Monthly tax = 93000 - 200 - 11404 = 81396
        """
		monthly_income_tax = 11404
		annual_tax = flt(monthly_income_tax * 12, 2)
		frappe.flags.posting_date = get_year_start(getdate())
		ctc_breakup = SalaryBreakupReport(employee, salary_structure_assignment.name)
		self.assertEqual(ctc_breakup.net_pay, 81396)
		income_tax_row = ctc_breakup.get_data()[-3]
		self.assertEqual(income_tax_row.get("per_cycle"), monthly_income_tax)
		self.assertEqual(income_tax_row.get("annual"), annual_tax)

	def test_income_tax_net_pay_calculation_at_the_end_of_payroll_period(self):
		employee = make_employee("test_ctc@example.com", company="_Test Company")
		salary_structure = make_salary_structure(
			"Test CTC Breakup with Tax", payroll_frequency="Monthly", currency="INR", test_tax=True
		)
		salary_structure_assignment = create_salary_structure_assignment(
			employee, salary_structure.name, base=60000, currency="INR", from_date=get_year_start(getdate())
		)
		salary_structure_assignment.ctc = 1116000
		salary_structure_assignment.save()

		"""With the given setup, the annual tax will be for last two months,
            taxable_income = 186000 (total earnings) - 400 (Professional Tax) - 50000 (Tax Exemption) = 135600
            Tax amount = 0 (taxable earning < 250000)
            Monthly net pay = Gross pay - Professional Tax - Monthly tax = 93000 - 200 - 11404 = 81396
        """
		monthly_income_tax = annual_tax = 0

		frappe.flags.posting_date = add_months(get_year_start(getdate()), 10)
		ctc_breakup = SalaryBreakupReport(employee, salary_structure_assignment.name)
		self.assertEqual(ctc_breakup.net_pay, 92800)
		income_tax_row = ctc_breakup.get_data()[-3]
		self.assertEqual(income_tax_row.get("per_cycle"), monthly_income_tax)
		self.assertEqual(income_tax_row.get("annual"), annual_tax)

	def test_report(self):
		employee = make_employee("test_ctc@example.com", company="_Test Company")
		salary_structure = make_salary_structure(
			"Test CTC Breakup with Tax", payroll_frequency="Monthly", currency="INR", test_tax=True
		)
		salary_structure_assignment = create_salary_structure_assignment(
			employee, salary_structure.name, base=60000, currency="INR", from_date=get_year_start(getdate())
		)
		salary_structure_assignment.ctc = 1116000
		salary_structure_assignment.save()
		frappe.flags.posting_date = get_year_start(getdate())
		ctc_breakup = SalaryBreakupReport(employee, salary_structure_assignment.name)
		data = ctc_breakup.get_data()
		self.assertEqual(len(data), 11)

		earning_components = ctc_breakup.earning_components
		deduction_components = ctc_breakup.deduction_components
		tax_components = ctc_breakup.tax_components
		net_pay_row = ctc_breakup.total_net_earnings
		gross_pay_row = ctc_breakup.total_gross_earnings

		earning_components_totals = earning_components[0]
		self.assertEqual(earning_components_totals.get("salary_component"), "Earnings")
		self.assertEqual(earning_components_totals.get("type"), "")
		self.assertEqual(earning_components_totals.get("formula"), "")
		self.assertEqual(earning_components_totals.get("per_cycle"), 93000)
		self.assertEqual(earning_components_totals.get("annual"), 1116000)
		self.assertEqual(earning_components_totals.get("percent_of_ctc"), 100)

		basic_earning_component = earning_components[1]
		self.assertEqual(basic_earning_component.get("salary_component"), "Basic Salary")
		self.assertEqual(basic_earning_component.get("type"), "Formula")
		self.assertEqual(basic_earning_component.get("formula"), "base")
		self.assertEqual(basic_earning_component.get("per_cycle"), 60000)
		self.assertEqual(basic_earning_component.get("annual"), 720000)
		self.assertEqual(basic_earning_component.get("percent_of_ctc"), 64.52)

		hra_earning_component = earning_components[2]
		self.assertEqual(hra_earning_component.get("salary_component"), "HRA")
		self.assertEqual(hra_earning_component.get("type"), "Fixed")
		self.assertEqual(hra_earning_component.get("formula"), 3000)
		self.assertEqual(hra_earning_component.get("per_cycle"), 3000)
		self.assertEqual(hra_earning_component.get("annual"), 36000)
		self.assertEqual(hra_earning_component.get("percent_of_ctc"), 3.23)

		special_allowance_earning_component = earning_components[3]
		self.assertEqual(special_allowance_earning_component.get("salary_component"), "Special Allowance")
		self.assertEqual(special_allowance_earning_component.get("type"), "Formula")
		self.assertEqual(special_allowance_earning_component.get("formula"), "BS\n*.5")
		self.assertEqual(special_allowance_earning_component.get("per_cycle"), 30000)
		self.assertEqual(special_allowance_earning_component.get("annual"), 360000)
		self.assertEqual(special_allowance_earning_component.get("percent_of_ctc"), 32.26)

		deduction_components_totals = deduction_components[0]
		self.assertEqual(deduction_components_totals.get("salary_component"), "Deductions")
		self.assertEqual(deduction_components_totals.get("type"), "")
		self.assertEqual(deduction_components_totals.get("formula"), "")
		self.assertEqual(deduction_components_totals.get("per_cycle"), 200)
		self.assertEqual(deduction_components_totals.get("annual"), 2400)
		self.assertEqual(deduction_components_totals.get("percent_of_ctc"), 0.22)

		professional_tax_deduction_component = deduction_components[1]
		self.assertEqual(professional_tax_deduction_component.get("salary_component"), "Professional Tax")
		self.assertEqual(professional_tax_deduction_component.get("type"), "Fixed")
		self.assertEqual(professional_tax_deduction_component.get("formula"), 200)
		self.assertEqual(professional_tax_deduction_component.get("per_cycle"), 200)
		self.assertEqual(professional_tax_deduction_component.get("annual"), 2400)
		self.assertEqual(professional_tax_deduction_component.get("percent_of_ctc"), 0.22)

		tax_components_totals = tax_components[0]
		self.assertEqual(tax_components_totals.get("salary_component"), "Tax Deductions")
		self.assertEqual(tax_components_totals.get("type"), "")
		self.assertEqual(tax_components_totals.get("formula"), "")
		self.assertEqual(tax_components_totals.get("per_cycle"), 11404)
		self.assertEqual(tax_components_totals.get("annual"), 136848)
		self.assertEqual(tax_components_totals.get("percent_of_ctc"), 12.26)

		self.assertEqual(net_pay_row[0].get("salary_component"), "Total Net Earnings")
		self.assertEqual(net_pay_row[0].get("per_cycle"), 81396)
		self.assertEqual(net_pay_row[0].get("annual"), 976752)
		self.assertEqual(net_pay_row[0].get("percent_of_ctc"), 87.52)

		self.assertEqual(gross_pay_row[0].get("salary_component"), "Total Gross Earnings")
		self.assertEqual(gross_pay_row[0].get("per_cycle"), 93000)
		self.assertEqual(gross_pay_row[0].get("annual"), 1116000)
		self.assertEqual(gross_pay_row[0].get("percent_of_ctc"), 100)

		self.assertEqual(
			flt(
				basic_earning_component.get("percent_of_ctc")
				+ hra_earning_component.get("percent_of_ctc")
				+ special_allowance_earning_component.get("percent_of_ctc"),
				0,
			),
			earning_components_totals.get("percent_of_ctc"),
		)
		self.assertEqual(
			professional_tax_deduction_component.get("percent_of_ctc"),
			deduction_components_totals.get("percent_of_ctc"),
		)
		self.assertEqual(
			net_pay_row[0].get("percent_of_ctc")
			+ tax_components_totals.get("percent_of_ctc")
			+ deduction_components_totals.get("percent_of_ctc"),
			earning_components_totals.get("percent_of_ctc"),
		)

	def test_ctc_validation(self):
		employee = make_employee("test_ctc@example.com", company="_Test Company")
		salary_structure = make_salary_structure(
			"Test CTC Breakup with Tax", payroll_frequency="Monthly", currency="INR", test_tax=True
		)
		salary_structure_assignment = create_salary_structure_assignment(
			employee, salary_structure.name, base=60000, currency="INR", from_date=get_year_start(getdate())
		)
		self.assertRaises(
			frappe.ValidationError, SalaryBreakupReport, employee, salary_structure_assignment.name
		)
		salary_structure_assignment.ctc = 1116000
		salary_structure_assignment.save()
		ctc_breakup = SalaryBreakupReport(employee, salary_structure_assignment.name)
		self.assertEqual(ctc_breakup.ctc, 1116000)
