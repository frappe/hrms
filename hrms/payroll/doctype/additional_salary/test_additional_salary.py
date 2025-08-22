# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, add_months, nowdate

import erpnext
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.salary_component.test_salary_component import create_salary_component
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_employee_salary_slip, setup_test
from hrms.payroll.doctype.salary_structure.test_salary_structure import (
	make_salary_slip,
	make_salary_structure,
)


class TestAdditionalSalary(IntegrationTestCase):
	def setUp(self):
		setup_test()

	def test_recurring_additional_salary(self):
		amount = 0
		salary_component = None
		emp_id = make_employee("test_additional@salary.com")
		frappe.db.set_value("Employee", emp_id, "relieving_date", add_days(nowdate(), 1800))
		salary_structure = make_salary_structure(
			"Test Salary Structure Additional Salary", "Monthly", employee=emp_id
		)
		add_sal = get_additional_salary(emp_id)

		ss = make_employee_salary_slip(emp_id, "Monthly", salary_structure=salary_structure.name)
		for earning in ss.earnings:
			if earning.salary_component == "Recurring Salary Component":
				amount = earning.amount
				salary_component = earning.salary_component
				break

		self.assertEqual(amount, add_sal.amount)
		self.assertEqual(salary_component, add_sal.salary_component)

	def test_disabled_recurring_additional_salary(self):
		emp_id = make_employee("test_additional@salary.com")

		salary_structure = make_salary_structure(
			"Test Salary Structure Additional Salary", "Monthly", employee=emp_id
		)
		add_sal = get_additional_salary(emp_id)
		ss = make_employee_salary_slip(emp_id, "Monthly", salary_structure=salary_structure.name)
		salary_componets = [earning.salary_component for earning in ss.earnings]
		self.assertIn("Recurring Salary Component", salary_componets)

		# Test disabling recurring additional salary
		posting_date = add_months(ss.posting_date, 1)
		frappe.db.set_value("Additional Salary", add_sal.name, "disabled", 1)

		ss = make_salary_slip(salary_structure.name, employee=emp_id, posting_date=posting_date)

		salary_components = [earning.salary_component for earning in ss.earnings]
		self.assertNotIn("Recurring Salary Component", salary_components)

	def test_non_recurring_additional_salary(self):
		amount = 0
		salary_component = None
		date = nowdate()

		emp_id = make_employee("test_additional@salary.com")
		frappe.db.set_value("Employee", emp_id, "relieving_date", add_days(date, 1800))
		salary_structure = make_salary_structure(
			"Test Salary Structure Additional Salary", "Monthly", employee=emp_id
		)
		add_sal = get_additional_salary(emp_id, recurring=False, payroll_date=date)

		ss = make_employee_salary_slip(emp_id, "Monthly", salary_structure=salary_structure.name)

		amount, salary_component = None, None
		for earning in ss.earnings:
			if earning.salary_component == "Recurring Salary Component":
				amount = earning.amount
				salary_component = earning.salary_component
				break

		self.assertEqual(amount, add_sal.amount)
		self.assertEqual(salary_component, add_sal.salary_component)

		# should not show up in next months
		ss.posting_date = add_months(date, 1)
		ss.start_date = ss.end_date = None
		ss.earnings = []
		ss.deductions = []
		ss.save()

		amount, salary_component = None, None
		for earning in ss.earnings:
			if earning.salary_component == "Recurring Salary Component":
				amount = earning.amount
				salary_component = earning.salary_component
				break

		self.assertIsNone(amount)
		self.assertIsNone(salary_component)

	def test_overwrite_salary_structure_amount(self):
		emp_id = make_employee("test_additional@salary.com")

		# Salary Structure created with HRA Salary Component amount as 3000
		salary_structure = make_salary_structure(
			"Test Salary Structure Additional Salary", "Monthly", employee=emp_id
		)
		self.assertEqual(salary_structure.earnings[1].amount, 3000)

		date = nowdate()

		# this will overwrite HRA Salary Component amount as 5000
		get_additional_salary(
			emp_id, recurring=False, payroll_date=date, salary_component="HRA", overwrite_salary_structure=1
		)
		salary_slip = make_salary_slip(salary_structure.name, employee=emp_id, posting_date=date)
		self.assertEqual(salary_slip.earnings[1].amount, 5000)

	def test_overwrite_tax_component(self):
		def _get_tds_component(doc) -> dict:
			return next(
				(d for d in salary_slip.get("deductions") if d.salary_component == "TDS"), frappe._dict()
			)

		emp_id = make_employee("test_additional@salary.com")
		salary_structure = make_salary_structure(
			"Test Salary Structure Additional Salary", "Monthly", employee=emp_id, test_tax=True
		)
		date = nowdate()

		# Overwrites TDS Salary Component amount as 5000
		additional_salary = get_additional_salary(
			emp_id, recurring=False, payroll_date=date, salary_component="TDS", overwrite_salary_structure=1
		)
		salary_slip = make_salary_slip(salary_structure.name, employee=emp_id, posting_date=date)
		tds_component = _get_tds_component(salary_slip)
		self.assertEqual(tds_component.additional_salary, additional_salary.name)
		self.assertEqual(tds_component.amount, 5000)

		# Calculates TDS as per tax slabs
		additional_salary.cancel()
		salary_slip = make_salary_slip(salary_structure.name, employee=emp_id, posting_date=date)
		tds_component = _get_tds_component(salary_slip)
		self.assertIsNone(tds_component.additional_salary)
		self.assertNotEqual(tds_component.amount, 5000)

	def test_validate_duplicate_or_overlapping_additional_salary(self):
		emp_id = make_employee("test_additional@salary.com")
		make_salary_structure("Test Salary Structure Additional Salary", "Monthly", employee=emp_id)
		date = nowdate()
		get_additional_salary(emp_id, overwrite_salary_structure=1)
		additional_salary_doc = frappe.get_doc(
			{
				"doctype": "Additional Salary",
				"employee": emp_id,
				"salary_component": "Recurring Salary Component",
				"payroll_date": date,
				"amount": 5000,
				"overwrite_salary_structure_amount": 1,
			}
		)
		with self.assertRaises(frappe.ValidationError):
			additional_salary_doc.save()


def get_additional_salary(
	emp_id, recurring=True, payroll_date=None, salary_component=None, overwrite_salary_structure=0
):
	create_salary_component("Recurring Salary Component")
	add_sal = frappe.new_doc("Additional Salary")
	add_sal.employee = emp_id
	add_sal.salary_component = salary_component or "Recurring Salary Component"

	add_sal.is_recurring = 1 if recurring else 0
	add_sal.from_date = add_days(nowdate(), -50)
	add_sal.to_date = add_days(nowdate(), 180)
	add_sal.payroll_date = payroll_date
	add_sal.overwrite_salary_structure_amount = overwrite_salary_structure

	add_sal.amount = 5000
	add_sal.currency = erpnext.get_default_currency()
	add_sal.save()
	add_sal.submit()

	return add_sal
