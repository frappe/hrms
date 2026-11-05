# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_months, add_years, get_first_day, getdate, nowdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.employee_benefit_ledger.employee_benefit_ledger import get_benefit_amount
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeBenefitClaim(HRMSTestSuite):
	def test_claim_limits_are_recomputed_server_side(self):
		employee, _, _ = setup_employee_with_benefits("test_benefit_claim_limits@claim.com")

		claim = make_benefit_claim(employee, "Leave Travel Allowance", 60000, max_amount_eligible=1000000)
		self.assertRaises(frappe.ValidationError, claim.insert)

		claim = make_benefit_claim(employee, "Basic Salary", 1000, max_amount_eligible=1000)
		self.assertRaises(frappe.ValidationError, claim.insert)

		claim = make_benefit_claim(employee, "Leave Travel Allowance", 50000, max_amount_eligible=1000000)
		claim.insert()
		self.assertEqual(claim.max_amount_eligible, 50000)
		claim.submit()

		# the submitted claim is not on a salary slip yet but still uses up the entitlement
		second_claim = make_benefit_claim(employee, "Leave Travel Allowance", 0)
		second_claim.get_benefit_details()
		self.assertEqual(second_claim.max_amount_eligible, 0)

		no_period_claim = make_benefit_claim(
			employee, "Leave Travel Allowance", 0, payroll_date=add_years(nowdate(), 10)
		)
		self.assertRaises(frappe.ValidationError, no_period_claim.get_benefit_details)

		claim.cancel()
		self.assertEqual(
			frappe.db.get_value("Additional Salary", {"ref_docname": claim.name}, "docstatus"), 2
		)

	def test_claim_of_current_month_accrual_does_not_cut_accruals(self):
		employee, salary_structure, payroll_period = setup_employee_with_benefits(
			"test_benefit_claim_accrual@claim.com"
		)
		make_benefit_ledger_entries(employee, "Mediclaim Allowance", payroll_period, 2000, months=3)

		claim = make_benefit_claim(employee, "Mediclaim Allowance", 0)
		current_month_accrual = claim._get_current_month_benefit_amount(
			frappe._dict(payout_method="Accrue per cycle, pay only on claim")
		)
		self.assertTrue(current_month_accrual)
		claim.get_benefit_details()
		self.assertEqual(claim.max_amount_eligible, 6000 + current_month_accrual)
		claim.claimed_amount = claim.max_amount_eligible
		claim.submit()

		salary_slip = make_salary_slip(salary_structure.name, employee=employee, posting_date=nowdate())
		accrual = sum(
			row.amount
			for row in salary_slip.accrued_benefits
			if row.salary_component == "Mediclaim Allowance"
		)
		self.assertEqual(accrual, current_month_accrual)

		salary_slip.submit()
		amounts = get_benefit_amount(employee, payroll_period.name, "Mediclaim Allowance")
		self.assertEqual(amounts["Accrual"], amounts["Payout"])


def setup_employee_with_benefits(user, **employee_args):
	from hrms.payroll.doctype.salary_slip.test_salary_slip import make_payroll_period
	from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

	frappe.db.set_value("Company", "_Test Company", "default_holiday_list", "_Test Holiday List")
	make_payroll_period(company="_Test Company")
	payroll_period = frappe.get_doc(
		"Payroll Period",
		{"company": "_Test Company", "start_date": ("<=", nowdate()), "end_date": (">=", nowdate())},
	)
	employee = make_employee(
		user, company="_Test Company", date_of_joining=employee_args.pop("date_of_joining", "2021-01-01")
	)
	if employee_args:
		frappe.db.set_value("Employee", employee, employee_args)

	salary_structure = make_salary_structure(
		"Test Employee Benefit Structure",
		"Monthly",
		company="_Test Company",
		employee=employee,
		payroll_period=payroll_period,
		from_date=payroll_period.start_date,
		base=65000,
		include_flexi_benefits=True,
	)
	return employee, salary_structure, payroll_period


def make_benefit_claim(employee, component, claimed_amount, payroll_date=None, **args):
	return frappe.get_doc(
		{
			"doctype": "Employee Benefit Claim",
			"employee": employee,
			"company": "_Test Company",
			"currency": "INR",
			"earning_component": component,
			"payroll_date": payroll_date or nowdate(),
			"claimed_amount": claimed_amount,
			**args,
		}
	)


def make_benefit_ledger_entries(employee, component, payroll_period, amount, months):
	start = get_first_day(nowdate())
	for i in range(months, 0, -1):
		posting_date = add_months(start, -i)
		if getdate(posting_date) < getdate(payroll_period.start_date):
			continue
		frappe.get_doc(
			{
				"doctype": "Employee Benefit Ledger",
				"employee": employee,
				"company": "_Test Company",
				"posting_date": posting_date,
				"payroll_period": payroll_period.name,
				"salary_component": component,
				"amount": amount,
				"transaction_type": "Accrual",
				"flexible_benefit": 1,
			}
		).insert()
