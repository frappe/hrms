# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, add_months, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.salary_structure.salary_structure import (
	make_salary_slip,
)
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure


class TestArrear(IntegrationTestCase):
	def test_arrear_calculation(self):
		# Test arrear calculation when new salary structure is applied retroactively later in the payroll period after salary slip creation
		emp = make_employee(
			"test_salary_structure_arrear@salary.com",
			company="_Test Company",
			date_of_joining="2021-01-01",
		)
		current_payroll_period = frappe.get_last_doc("Payroll Period", filters={"company": "_Test Company"})

		# Create initial salary structure with lower salary
		old_salary_structure = make_salary_structure(
			"Test Old Salary Structure",
			"Monthly",
			company="_Test Company",
			employee=emp,
			payroll_period=current_payroll_period,
			test_arrear=True,
			base=50000,  # Lower base salary
		)

		# Create new payroll period for next year
		next_year_start = add_days(current_payroll_period.end_date, 1)
		next_year_end = add_months(current_payroll_period.end_date, 1)

		new_payroll_period = frappe.get_doc(
			{
				"doctype": "Payroll Period",
				"name": f"Test Payroll Period {getdate(next_year_start).year}",
				"company": "_Test Company",
				"start_date": next_year_start,
				"end_date": next_year_end,
			}
		)
		new_payroll_period.insert()

		# Create and submit salary slip for first month of new payroll period with old structure
		first_month_slip = make_salary_slip(
			old_salary_structure.name, employee=emp, posting_date=next_year_start
		)
		first_month_slip.save()
		first_month_slip.submit()

		# Create new salary structure with higher salary for same employee
		new_salary_structure = make_salary_structure(
			"Test New Arrear Salary Structure",
			"Monthly",
			employee=emp,
			from_date=next_year_start,
			company="_Test Company",
			payroll_period=new_payroll_period,
			base=75000,  # Higher base salary
			test_arrear=True,
			test_accrual_component=True,
			test_salary_structure_arrear=True,
		)

		previous_structure_arrear_components = {
			"earnings": {"Basic Salary": 50000, "Special Allowance": 25000},
			"deductions": {"Professional Tax": 200},
		}

		current_structure_arrear_components = {
			"earnings": {"Basic Salary": 75000, "Special Allowance": 37500},
			"deductions": {"Professional Tax": 300},
			"accruals": {"Accrued Earnings": 1000},
		}

		arrear_doc = frappe.get_doc(
			{
				"doctype": "Arrear",
				"employee": emp,
				"payroll_period": new_payroll_period.name,
				"salary_structure": new_salary_structure.name,
				"arrear_start_date": next_year_start,
				"payroll_date": add_months(next_year_start, 2),  # next month
				"company": "_Test Company",
			}
		)
		arrear_doc.save()

		earning_arrears = {row.salary_component: row.amount for row in arrear_doc.earning_arrears}
		deduction_arrears = {row.salary_component: row.amount for row in arrear_doc.deduction_arrears}
		accrual_arrears = {row.salary_component: row.amount for row in arrear_doc.accrual_arrears}

		# Earnings differences
		for comp, new_amt in current_structure_arrear_components["earnings"].items():
			old_amt = previous_structure_arrear_components["earnings"].get(comp, 0)
			diff = new_amt - old_amt
			self.assertIn(comp, earning_arrears)
			self.assertEqual(
				earning_arrears[comp],
				diff,
			)

		# Deductions differences
		for comp, new_amt in current_structure_arrear_components["deductions"].items():
			old_amt = previous_structure_arrear_components["deductions"].get(comp, 0)
			diff = new_amt - old_amt
			self.assertIn(comp, deduction_arrears)
			self.assertEqual(
				deduction_arrears[comp],
				diff,
			)
		# Accrual differences (new only, no previous)
		for comp, new_amt in current_structure_arrear_components["accruals"].items():
			old_amt = previous_structure_arrear_components["earnings"].get(comp, 0)
			diff = new_amt - old_amt
			self.assertIn(comp, accrual_arrears)
			self.assertEqual(
				accrual_arrears[comp],
				diff,
			)

		arrear_doc.submit()

		# Validate additional salary creation
		additional_salary_entries = frappe.get_all(
			"Additional Salary",
			filters={"ref_docname": arrear_doc.name, "employee": emp},
			fields=["salary_component", "type"],
		)
		self.assertTrue(additional_salary_entries, "Additional salary entries should be created")
		earning_components = [
			e["salary_component"] for e in additional_salary_entries if e["type"] == "Earning"
		]
		self.assertIn("Basic Salary", earning_components)
		self.assertIn("Special Allowance", earning_components)

		# Validate benefit ledger creation
		benefit_entries = frappe.get_all(
			"Employee Benefit Ledger",
			filters={"reference_document": arrear_doc.name, "employee": emp},
			fields=["salary_component"],
		)
		if benefit_entries:
			accrual_components = [e["salary_component"] for e in benefit_entries]
			self.assertIn("Accrued Earnings", accrual_components)

		frappe.db.rollback()
