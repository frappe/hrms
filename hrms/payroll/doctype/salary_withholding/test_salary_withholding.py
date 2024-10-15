# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import get_first_day, get_year_start, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.payroll_entry.payroll_entry import get_start_end_dates
from hrms.payroll.doctype.payroll_entry.test_payroll_entry import make_payroll_entry
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure


class TestSalaryWithholding(IntegrationTestCase):
	def setUp(self):
		for dt in [
			"Salary Withholding",
			"Salary Withholding Cycle",
			"Salary Slip",
			"Payroll Entry",
			"Salary Structure",
			"Salary Structure Assignment",
			"Payroll Employee Detail",
			"Journal Entry",
		]:
			frappe.db.delete(dt)

		self.company = frappe.get_doc("Company", "_Test Company")
		self.employee1 = make_employee("employee1@example.com", company=self.company, designation="Engineer")
		self.employee2 = make_employee("employee2@example.com", company=self.company, designation="Engineer")

		self.today = getdate()
		year_start = get_year_start(self.today)
		make_salary_structure("Test Withholding", "Monthly", employee=self.employee1, from_date=year_start)
		make_salary_structure("Test Withholding", "Monthly", employee=self.employee2, from_date=year_start)

	def test_set_withholding_cycles_and_to_date(self):
		from_date = getdate("2024-06-01")
		to_date = getdate("2024-07-31")
		withholding = create_salary_withholding(self.employee1, from_date, 2)

		self.assertEqual(withholding.to_date, to_date)
		self.assertEqual(withholding.cycles[0].from_date, from_date)
		self.assertEqual(withholding.cycles[0].to_date, getdate("2024-06-30"))
		self.assertEqual(withholding.cycles[1].from_date, getdate("2024-07-01"))
		self.assertEqual(withholding.cycles[1].to_date, to_date)

	def test_salary_withholding(self):
		withholding = create_salary_withholding(self.employee1, get_first_day(self.today), 2)
		withholding.submit()
		payroll_entry = self._make_payroll_entry()

		payroll_employee = self._get_payroll_employee_row(payroll_entry)
		self.assertEqual(payroll_employee.is_salary_withheld, 1)

		salary_slip = get_salary_slip_details(payroll_entry.name, self.employee1)
		self.assertEqual(salary_slip.salary_withholding, withholding.name)
		self.assertEqual(salary_slip.salary_withholding_cycle, withholding.cycles[0].name)
		self.assertEqual(salary_slip.status, "Withheld")
		self.assertEqual(withholding.status, "Withheld")

	def test_release_withheld_salaries(self):
		withholding = create_salary_withholding(self.employee1, get_first_day(self.today), 2)
		withholding.submit()

		def test_run_payroll_for_cycle(withholding_cycle):
			# bank entry should skip withheld salaries
			payroll_entry = self._make_payroll_entry(withholding_cycle.from_date)
			bank_entry = payroll_entry.make_bank_entry()
			self._submit_bank_entry(bank_entry)
			has_withheld_salary = any(row.party == self.employee1 for row in bank_entry.accounts)
			self.assertFalse(has_withheld_salary)

			# separate bank entry for withheld salaries
			# test Bank Entry linking
			bank_entry_for_withheld_salaries = payroll_entry.make_bank_entry(for_withheld_salaries=1)
			withholding_cycle.reload()
			self.assertEqual(withholding_cycle.journal_entry, bank_entry_for_withheld_salaries.name)

			# test released salary on bank entry submission
			self._submit_bank_entry(bank_entry_for_withheld_salaries)
			withholding_cycle.reload()
			self.assertEqual(withholding_cycle.is_salary_released, 1)
			salary_slip = get_salary_slip_details(payroll_entry.name, self.employee1)
			self.assertEqual(salary_slip.status, "Submitted")
			payroll_employee = self._get_payroll_employee_row(payroll_entry)
			self.assertEqual(payroll_employee.is_salary_withheld, 0)

			return payroll_entry, bank_entry_for_withheld_salaries

		# run payroll for each withholding cycle
		for cycle in withholding.cycles:
			payroll_entry, bank_entry = test_run_payroll_for_cycle(cycle)
		withholding.reload()
		self.assertEqual(withholding.status, "Released")

		# test payment cancellation for withheld salaries
		bank_entry.cancel()
		withholding.reload()

		self.assertEqual(withholding.cycles[-1].is_salary_released, 0)
		salary_slip = get_salary_slip_details(payroll_entry.name, self.employee1)
		self.assertEqual(salary_slip.status, "Withheld")
		payroll_employee = self._get_payroll_employee_row(payroll_entry)
		self.assertEqual(payroll_employee.is_salary_withheld, 1)

	def _make_payroll_entry(self, date: str | None = None):
		dates = get_start_end_dates("Monthly", date or self.today)
		return make_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=self.company.default_payroll_payable_account,
			currency=self.company.default_currency,
			company=self.company.name,
		)

	def _submit_bank_entry(self, bank_entry: dict):
		bank_entry.cheque_no = "123456"
		bank_entry.cheque_date = self.today
		bank_entry.submit()

	def _get_payroll_employee_row(self, payroll_entry: dict) -> dict | None:
		payroll_entry.reload()
		return next(employee for employee in payroll_entry.employees if employee.employee == self.employee1)


def create_salary_withholding(employee: str, from_date: str, number_of_withholding_cycles: int = 0):
	doc = frappe.new_doc("Salary Withholding")
	doc.update(
		{
			"employee": employee,
			"from_date": from_date,
			"number_of_withholding_cycles": number_of_withholding_cycles,
		}
	)
	doc.insert()

	return doc


def get_salary_slip_details(payroll_entry: str, employee: str) -> dict:
	return frappe.db.get_value(
		"Salary Slip",
		{"payroll_entry": payroll_entry, "employee": employee},
		["status", "salary_withholding", "salary_withholding_cycle"],
		as_dict=1,
	)
