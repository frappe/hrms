# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase, change_settings
from frappe.utils import add_days, add_months, floor, flt, get_datetime, get_first_day, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee
from erpnext.setup.doctype.holiday_list.test_holiday_list import set_holiday_list

from hrms.hr.doctype.attendance.attendance import mark_attendance
from hrms.hr.doctype.expense_claim.test_expense_claim import get_payable_account
from hrms.payroll.doctype.gratuity.gratuity import get_last_salary_slip
from hrms.payroll.doctype.salary_slip.test_salary_slip import (
	make_deduction_salary_component,
	make_earning_salary_component,
	make_employee_salary_slip,
	make_holiday_list,
)
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

test_dependencies = ["Salary Component", "Salary Slip", "Account"]


class TestGratuity(IntegrationTestCase):
	def setUp(self):
		for dt in ["Gratuity", "Salary Slip", "Additional Salary"]:
			frappe.db.delete(dt)

		self.date_of_joining = add_days(getdate(), -(6 * 365))
		self.relieving_date = getdate()
		self.employee = make_employee(
			"test_employee_gratuity@salary.com",
			company="_Test Company",
			date_of_joining=self.date_of_joining,
			relieving_date=self.relieving_date,
		)

		make_earning_salary_component(
			setup=True, test_tax=True, company_list=["_Test Company"], include_flexi_benefits=True
		)
		make_deduction_salary_component(setup=True, test_tax=True, company_list=["_Test Company"])
		make_holiday_list()

	@set_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_gratuity_based_on_current_slab_via_additional_salary(self):
		"""
		Range	|	Fraction
		5-0		|	1
		"""
		sal_slip = create_salary_slip(self.employee)

		rule = setup_gratuity_rule("Rule Under Unlimited Contract on termination (UAE)")
		gratuity = create_gratuity(pay_via_salary_slip=1, employee=self.employee, rule=rule.name)

		# work experience calculation
		employee_total_workings_days = (
			get_datetime(self.relieving_date) - get_datetime(self.date_of_joining)
		).days
		experience = floor(employee_total_workings_days / rule.total_working_days_per_year)
		self.assertEqual(gratuity.current_work_experience, experience)

		# amount calculation
		component_amount = frappe.get_all(
			"Salary Detail",
			filters={
				"docstatus": 1,
				"parent": sal_slip.name,
				"parentfield": "earnings",
				"salary_component": "Basic Salary",
			},
			fields=["amount"],
			limit=1,
		)
		gratuity_amount = component_amount[0].amount * experience
		self.assertEqual(flt(gratuity_amount, 2), flt(gratuity.amount, 2))

		# additional salary creation (Pay via salary slip)
		self.assertTrue(frappe.db.exists("Additional Salary", {"ref_docname": gratuity.name}))

		# gratuity should be marked "Paid" on the next salary slip submission
		salary_slip = make_salary_slip("Test Gratuity", employee=self.employee)
		salary_slip.posting_date = getdate()
		salary_slip.insert()
		salary_slip.submit()

		gratuity.reload()
		self.assertEqual(gratuity.status, "Paid")

	@set_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_gratuity_based_on_all_previous_slabs_via_payment_entry(self):
		"""
		Range   |   Fraction
		0-3     |   0.5
		3-6     |   1.0
		6-9		|	1.5
		"""
		from hrms.overrides.employee_payment_entry import get_payment_entry_for_employee

		sal_slip = create_salary_slip(self.employee)

		rule = setup_gratuity_rule("Rule Under Limited Contract (UAE)")
		rule.gratuity_rule_slabs = []
		for slab in [
			{"from_year": 0, "to_year": 3, "fraction_of_applicable_earnings": 0.5},
			{"from_year": 3, "to_year": 6, "fraction_of_applicable_earnings": 1.0},
			{"from_year": 6, "to_year": 9, "fraction_of_applicable_earnings": 1.5},
		]:
			new_slab = frappe.get_doc(
				{
					"doctype": "Gratuity Rule Slab",
					"from_year": slab["from_year"],
					"to_year": slab["to_year"],
					"fraction_of_applicable_earnings": slab["fraction_of_applicable_earnings"],
					"parent": rule.name,
					"parentfield": "gratuity_rule_slabs",
					"parenttype": "Gratuity Rule",
				}
			)
			rule.append("gratuity_rule_slabs", new_slab)
		rule.save()
		rule.reload()

		set_mode_of_payment_account()

		gratuity = create_gratuity(
			expense_account="Payment Account - _TC",
			mode_of_payment="Cash",
			employee=self.employee,
			rule=rule.name,
		)

		# work experience calculation
		employee_total_workings_days = (
			get_datetime(self.relieving_date) - get_datetime(self.date_of_joining)
		).days
		experience = floor(employee_total_workings_days / rule.total_working_days_per_year)
		self.assertEqual(gratuity.current_work_experience, experience)

		# amount calculation
		component_amount = frappe.get_all(
			"Salary Detail",
			filters={
				"docstatus": 1,
				"parent": sal_slip.name,
				"parentfield": "earnings",
				"salary_component": "Basic Salary",
			},
			fields=["amount"],
			limit=1,
		)

		gratuity_amount = ((3 * 0.5) + (3 * 1.0)) * component_amount[0].amount
		self.assertEqual(flt(gratuity_amount, 2), flt(gratuity.amount, 2))
		self.assertEqual(gratuity.status, "Unpaid")

		pe = get_payment_entry_for_employee("Gratuity", gratuity.name)
		pe.reference_no = "123467"
		pe.reference_date = getdate()
		pe.submit()

		gratuity.reload()
		self.assertEqual(gratuity.status, "Paid")
		self.assertEqual(flt(gratuity.paid_amount, 2), flt(gratuity.amount, 2))

		pe.cancel()
		gratuity.reload()
		self.assertEqual(gratuity.status, "Unpaid")
		self.assertEqual(gratuity.paid_amount, 0)

	@change_settings(
		"Payroll Settings",
		{
			"payroll_based_on": "Attendance",
			"consider_unmarked_attendance_as": "Present",
			"include_holidays_in_total_working_days": True,
		},
	)
	def test_gratuity_amount_consistent_irrespective_of_payment_days(self):
		date = getdate("2024-01-01")
		create_salary_slip(self.employee, date)

		setup_gratuity_rule("Rule Under Limited Contract (UAE)")
		set_mode_of_payment_account()

		gratuity = create_gratuity(
			expense_account="Payment Account - _TC", mode_of_payment="Cash", employee=self.employee
		)
		self.assertEqual(gratuity.amount, 190000.0)

		# gratuity amount should be unaffected inspite of marking the employee absent for a day
		frappe.db.delete("Gratuity", gratuity.name)
		mark_attendance(self.employee, date, "Absent")
		gratuity = create_gratuity(
			expense_account="Payment Account - _TC", mode_of_payment="Cash", employee=self.employee
		)
		self.assertEqual(gratuity.amount, 190000.0)

	@set_holiday_list("Salary Slip Test Holiday List", "_Test Company")
	def test_settle_gratuity_via_fnf_statement(self):
		from hrms.hr.doctype.full_and_final_statement.test_full_and_final_statement import (
			create_full_and_final_statement,
		)

		create_salary_slip(self.employee)
		setup_gratuity_rule("Rule Under Limited Contract (UAE)")
		set_mode_of_payment_account()

		# create gratuity
		gratuity = create_gratuity(
			expense_account="Payment Account - _TC", mode_of_payment="Cash", employee=self.employee
		)
		gratuity.reload()

		# create Full and Final Statement and add gratuity as Payables
		fnf = create_full_and_final_statement(self.employee)
		fnf.payables = []
		fnf.receivables = []
		fnf.append(
			"payables",
			{
				"component": "Gratuity",
				"reference_document_type": "Gratuity",
				"reference_document": gratuity.name,
				"amount": gratuity.amount,
				"account": gratuity.payable_account,
				"status": "Settled",
			},
		)
		fnf.submit()

		jv = fnf.create_journal_entry()
		jv.accounts[1].account = frappe.get_cached_value("Company", "_Test Company", "default_bank_account")
		jv.cheque_no = "123456"
		jv.cheque_date = getdate()
		jv.save()
		jv.submit()

		gratuity.reload()
		self.assertEqual(gratuity.status, "Paid")

		jv.cancel()
		gratuity.reload()
		self.assertEqual(gratuity.status, "Unpaid")


def setup_gratuity_rule(name: str) -> dict:
	from hrms.regional.united_arab_emirates.setup import setup

	if not frappe.db.exists("Gratuity Rule", name):
		setup()

	rule = frappe.get_doc("Gratuity Rule", name)
	rule.applicable_earnings_component = []
	rule.append("applicable_earnings_component", {"salary_component": "Basic Salary"})
	rule.save()

	return rule


def create_gratuity(**args):
	if args:
		args = frappe._dict(args)
	gratuity = frappe.new_doc("Gratuity")
	gratuity.employee = args.employee
	gratuity.posting_date = getdate()
	gratuity.gratuity_rule = args.rule or "Rule Under Limited Contract (UAE)"
	gratuity.pay_via_salary_slip = args.pay_via_salary_slip or 0
	if gratuity.pay_via_salary_slip:
		gratuity.payroll_date = getdate()
		gratuity.salary_component = "Performance Bonus"
	else:
		gratuity.expense_account = args.expense_account or "Payment Account - _TC"
		gratuity.payable_account = args.payable_account or get_payable_account("_Test Company")
		gratuity.mode_of_payment = args.mode_of_payment or "Cash"
		gratuity.cost_center = args.cost_center or "Main - _TC"

	gratuity.save()
	gratuity.submit()

	return gratuity


def set_mode_of_payment_account():
	if not frappe.db.exists("Account", "Payment Account - _TC"):
		mode_of_payment = create_account()

	mode_of_payment = frappe.get_doc("Mode of Payment", "Cash")

	mode_of_payment.accounts = []
	mode_of_payment.append("accounts", {"company": "_Test Company", "default_account": "_Test Bank - _TC"})
	mode_of_payment.save()


def create_account():
	return frappe.get_doc(
		{
			"doctype": "Account",
			"company": "_Test Company",
			"account_name": "Payment Account",
			"root_type": "Asset",
			"report_type": "Balance Sheet",
			"currency": "INR",
			"parent_account": "Bank Accounts - _TC",
			"account_type": "Bank",
		}
	).insert()


def create_salary_slip(employee, posting_date=None):
	posting_date = posting_date or get_first_day(add_months(getdate(), -1))
	salary_slip = make_employee_salary_slip(employee, "Monthly", "Test Gratuity", posting_date=posting_date)
	salary_slip.start_date = posting_date
	salary_slip.end_date = None
	salary_slip.submit()

	return salary_slip
