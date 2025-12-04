# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_years, cstr, date_diff, get_first_day, nowdate
from frappe.utils.make_random import get_random

import erpnext
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.employee_tax_exemption_declaration.test_employee_tax_exemption_declaration import (
	create_payroll_period,
)
from hrms.payroll.doctype.salary_slip.test_salary_slip import (
	create_tax_slab,
	make_deduction_salary_component,
	make_earning_salary_component,
	make_employee_benefit_earning_components,
	make_employee_salary_slip,
)
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from hrms.tests.test_utils import create_employee_grade

test_dependencies = ["Fiscal Year"]


class TestSalaryStructure(IntegrationTestCase):
	def setUp(self):
		for dt in ["Salary Slip", "Salary Structure", "Salary Structure Assignment"]:
			frappe.db.sql("delete from `tab%s`" % dt)

		self.make_holiday_list()
		frappe.db.set_value(
			"Company",
			erpnext.get_default_company(),
			"default_holiday_list",
			"Salary Structure Test Holiday List",
		)
		make_employee("test_employee@salary.com")
		make_employee("test_employee_2@salary.com")

	def make_holiday_list(self):
		if not frappe.db.get_value("Holiday List", "Salary Structure Test Holiday List"):
			holiday_list = frappe.get_doc(
				{
					"doctype": "Holiday List",
					"holiday_list_name": "Salary Structure Test Holiday List",
					"from_date": nowdate(),
					"to_date": add_years(nowdate(), 1),
					"weekly_off": "Sunday",
				}
			).insert()
			holiday_list.get_weekly_off_dates()
			holiday_list.save()

	def test_salary_structure_deduction_based_on_gross_pay(self):
		emp = make_employee("test_employee_3@salary.com")

		sal_struct = make_salary_structure("Salary Structure 2", "Monthly", dont_submit=True)

		sal_struct.earnings = [sal_struct.earnings[0]]
		sal_struct.earnings[0].amount_based_on_formula = 1
		sal_struct.earnings[0].formula = "base"

		sal_struct.deductions = [sal_struct.deductions[0]]

		sal_struct.deductions[0].amount_based_on_formula = 1
		sal_struct.deductions[0].condition = "gross_pay > 100"
		sal_struct.deductions[0].formula = "gross_pay * 0.2"

		sal_struct.submit()

		assignment = create_salary_structure_assignment(emp, "Salary Structure 2")
		ss = make_salary_slip(sal_struct.name, employee=emp)

		self.assertEqual(assignment.base * 0.2, ss.deductions[0].amount)

	def test_amount_totals(self):
		frappe.db.set_single_value("Payroll Settings", "include_holidays_in_total_working_days", 0)
		emp_id = make_employee("test_employee_2@salary.com")
		salary_slip = frappe.get_value("Salary Slip", {"employee": emp_id})

		if not salary_slip:
			salary_slip = make_employee_salary_slip(emp_id, "Monthly", "Salary Structure Sample")
			self.assertEqual(salary_slip.get("salary_structure"), "Salary Structure Sample")
			self.assertEqual(salary_slip.get("earnings")[0].amount, 50000)
			self.assertEqual(salary_slip.get("earnings")[1].amount, 3000)
			self.assertEqual(salary_slip.get("earnings")[2].amount, 25000)
			self.assertEqual(salary_slip.get("gross_pay"), 78000)
			self.assertEqual(salary_slip.get("deductions")[0].amount, 200)
			self.assertEqual(salary_slip.get("net_pay"), 78000 - salary_slip.get("total_deduction"))

	def test_whitespaces_in_formula_conditions_fields(self):
		def add_whitespaces(row):
			row.formula = "\n%s\n\n" % row.formula
			row.condition = "\n%s\n\n" % row.condition

		salary_structure = make_salary_structure("Salary Structure Sample", "Monthly", dont_submit=True)
		for table in ("earnings", "deductions"):
			for row in salary_structure.get(table):
				add_whitespaces(row)

		# sanitized before validate and reset to original state to maintain readability
		salary_structure.sanitize_condition_and_formula_fields()

		for row in salary_structure.earnings:
			self.assertFalse("\n" in cstr(row.formula) or "\n" in cstr(row.condition))

		for row in salary_structure.deductions:
			self.assertFalse("\n" in cstr(row.formula) or "\n" in cstr(row.condition))

	def test_salary_structures_assignment(self):
		company_currency = erpnext.get_default_currency()
		salary_structure = make_salary_structure(
			"Salary Structure Sample", "Monthly", currency=company_currency
		)
		employee = "test_assign_structure@salary.com"
		employee_doc_name = make_employee(employee)
		# clear the already assigned structures
		frappe.db.sql(
			"""delete from `tabSalary Structure Assignment` where employee=%s and salary_structure=%s """,
			("test_assign_structure@salary.com", salary_structure.name),
		)
		# test structure_assignment
		salary_structure.assign_salary_structure(
			employee=employee_doc_name, from_date="2013-01-01", base=5000, variable=200
		)
		salary_structure_assignment = frappe.get_doc(
			"Salary Structure Assignment", {"employee": employee_doc_name, "from_date": "2013-01-01"}
		)
		self.assertEqual(salary_structure_assignment.docstatus, 1)
		self.assertEqual(salary_structure_assignment.base, 5000)
		self.assertEqual(salary_structure_assignment.variable, 200)

	def test_employee_grade_defaults(self):
		salary_structure = make_salary_structure(
			"Salary Structure - Lead", "Monthly", currency="INR", company="_Test Company"
		)
		create_employee_grade("Lead", salary_structure.name)
		employee = make_employee("test_employee_grade@salary.com", company="_Test Company", grade="Lead")

		# structure assignment should have the default salary structure and base pay
		salary_structure.assign_salary_structure(employee=employee, from_date=nowdate())
		structure, base = frappe.db.get_value(
			"Salary Structure Assignment",
			{"employee": employee, "salary_structure": salary_structure.name, "from_date": nowdate()},
			["salary_structure", "base"],
		)
		self.assertEqual(structure, salary_structure.name)
		self.assertEqual(base, 50000)

	def test_multi_currency_salary_structure(self):
		make_employee("test_muti_currency_employee@salary.com")
		sal_struct = make_salary_structure("Salary Structure Multi Currency", "Monthly", currency="USD")
		self.assertEqual(sal_struct.currency, "USD")


def make_salary_structure(
	salary_structure,
	payroll_frequency,
	employee=None,
	from_date=None,
	dont_submit=False,
	other_details=None,
	test_tax=False,
	company=None,
	currency=None,
	payroll_period=None,
	include_flexi_benefits=False,
	base=None,
	test_accrual_component=False,
	test_arrear=False,
	test_salary_structure_arrear=False,
):
	if not currency:
		currency = erpnext.get_default_currency()

	if frappe.db.exists("Salary Structure", salary_structure):
		frappe.db.delete("Salary Structure", salary_structure)

	employee_benefits = []
	if include_flexi_benefits:
		employee_benefits = make_employee_benefit_earning_components(
			setup=True,
			company_list=["_Test Company"],
			test_arrear=test_arrear,
		)

	details = {
		"doctype": "Salary Structure",
		"name": salary_structure,
		"company": company or erpnext.get_default_company(),
		"earnings": make_earning_salary_component(
			setup=True,
			test_tax=test_tax,
			company_list=["_Test Company"],
			test_accrual_component=test_accrual_component,
			test_arrear=test_arrear,
		),
		"deductions": make_deduction_salary_component(
			setup=True,
			test_tax=test_tax,
			company_list=["_Test Company"],
			test_salary_structure_arrear=test_salary_structure_arrear,
		),
		"employee_benefits": employee_benefits,
		"payroll_frequency": payroll_frequency,
		"payment_account": get_random("Account", filters={"account_currency": currency}),
		"currency": currency,
	}
	if other_details and isinstance(other_details, dict):
		details.update(other_details)
	salary_structure_doc = frappe.get_doc(details)
	salary_structure_doc.insert()
	if not dont_submit:
		salary_structure_doc.submit()

	filters = {"employee": employee, "docstatus": 1}
	if not from_date and payroll_period:
		from_date = payroll_period.start_date

	if from_date:
		filters["from_date"] = from_date

	if (
		employee
		and not frappe.db.get_value("Salary Structure Assignment", filters)
		and salary_structure_doc.docstatus == 1
	):
		create_salary_structure_assignment(
			employee,
			salary_structure,
			from_date=from_date,
			company=company,
			currency=currency,
			payroll_period=payroll_period,
			base=base,
			include_flexi_benefits=include_flexi_benefits,
		)

	return salary_structure_doc


def create_salary_structure_assignment(
	employee,
	salary_structure,
	from_date=None,
	company=None,
	currency=None,
	payroll_period=None,
	base=None,
	allow_duplicate=False,
	include_flexi_benefits=False,
):
	if not currency:
		currency = erpnext.get_default_currency()

	if not allow_duplicate and frappe.db.exists("Salary Structure Assignment", {"employee": employee}):
		frappe.db.sql("""delete from `tabSalary Structure Assignment` where employee=%s""", (employee))

	if not payroll_period:
		payroll_period = create_payroll_period(company="_Test Company")

	income_tax_slab = frappe.db.get_value("Income Tax Slab", {"currency": currency, "docstatus": 1})

	if not income_tax_slab:
		income_tax_slab = create_tax_slab(payroll_period, allow_tax_exemption=True, currency=currency)

	employee_benefits = []
	if include_flexi_benefits:
		employee_benefits = make_employee_benefit_earning_components()

	salary_structure_assignment = frappe.new_doc("Salary Structure Assignment")
	salary_structure_assignment.employee = employee
	salary_structure_assignment.base = base or 50000
	salary_structure_assignment.variable = 5000

	if not from_date:
		from_date = get_first_day(nowdate())
		joining_date = frappe.get_cached_value("Employee", employee, "date_of_joining")
		if date_diff(joining_date, from_date) > 0:
			from_date = joining_date

	salary_structure_assignment.from_date = from_date
	salary_structure_assignment.salary_structure = salary_structure
	salary_structure_assignment.currency = currency
	salary_structure_assignment.payroll_payable_account = get_payable_account(company)
	salary_structure_assignment.company = company or erpnext.get_default_company()
	salary_structure_assignment.income_tax_slab = income_tax_slab
	for benefit in employee_benefits:
		salary_structure_assignment.append("employee_benefits", benefit)
	salary_structure_assignment.save(ignore_permissions=True)
	salary_structure_assignment.submit()
	return salary_structure_assignment


def get_payable_account(company=None):
	if not company:
		company = erpnext.get_default_company()
	return frappe.db.get_value("Company", company, "default_payroll_payable_account")
