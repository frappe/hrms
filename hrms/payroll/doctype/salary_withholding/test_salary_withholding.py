# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import flt, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.payroll_entry.payroll_entry import get_start_end_dates
from hrms.payroll.doctype.payroll_entry.test_payroll_entry import make_payroll_entry
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from hrms.tests.utils import HRMSTestSuite

COMPANY_NAME = "_Test Company"
MONTH_1_START = getdate("2024-01-01")
MONTH_1_END = getdate("2024-01-31")
MONTH_2_START = getdate("2024-02-01")
MONTH_2_END = getdate("2024-02-29")


class TestSalaryWithholding(HRMSTestSuite):
	def setUp(self):
		self.company = frappe.get_doc("Company", COMPANY_NAME)
		default_payroll_payble_account = frappe.get_value(
			"Company", self.company.name, "default_payroll_payable_account"
		)
		frappe.db.set_value("Account", default_payroll_payble_account, "account_type", "Payable")
		self.employee1 = make_employee("employee1@example.com", company=COMPANY_NAME, designation="Engineer")
		self.employee2 = make_employee("employee2@example.com", company=COMPANY_NAME, designation="Engineer")

		make_salary_structure(
			"Test Withholding",
			"Monthly",
			company=COMPANY_NAME,
			employee=self.employee1,
			from_date=MONTH_1_START,
		)
		make_salary_structure(
			"Test Withholding",
			"Monthly",
			company=COMPANY_NAME,
			employee=self.employee2,
			from_date=MONTH_1_START,
		)

	def test_set_withholding_cycles_and_to_date(self):
		withholding = create_salary_withholding(self.employee1, MONTH_1_START, 2)

		self.assertEqual(withholding.to_date, MONTH_2_END)
		self.assertEqual(withholding.cycles[0].from_date, MONTH_1_START)
		self.assertEqual(withholding.cycles[0].to_date, MONTH_1_END)
		self.assertEqual(withholding.cycles[1].from_date, MONTH_2_START)
		self.assertEqual(withholding.cycles[1].to_date, MONTH_2_END)

	def test_salary_withholding(self):
		withholding = create_salary_withholding(self.employee1, MONTH_1_START, 2)
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
		withholding = create_salary_withholding(self.employee1, MONTH_1_START, 2)
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

	def test_get_withheld_salaries(self):
		create_salary_withholding(self.employee1, MONTH_1_START, 1).submit()
		create_salary_withholding(self.employee2, MONTH_1_START, 1).submit()
		payroll_entry = self._make_payroll_entry()

		withheld_salaries = payroll_entry.get_withheld_salaries()

		self.assertEqual(
			[row["employee"] for row in withheld_salaries],
			sorted([self.employee1, self.employee2]),
		)
		for row in withheld_salaries:
			self.assertTrue(row["employee_name"])
			self.assertGreater(row["amount"], 0)

	def test_release_withheld_salary_for_selected_employee(self):
		create_salary_withholding(self.employee1, MONTH_1_START, 1).submit()
		create_salary_withholding(self.employee2, MONTH_1_START, 1).submit()
		payroll_entry = self._make_payroll_entry()

		withheld_salaries = {row["employee"]: row["amount"] for row in payroll_entry.get_withheld_salaries()}
		bank_entry = payroll_entry.make_bank_entry(for_withheld_salaries=1, employees=[self.employee1])

		self.assertEqual(flt(bank_entry.total_debit), flt(withheld_salaries[self.employee1]))
		self._submit_bank_entry(bank_entry)

		self.assertEqual(get_salary_slip_details(payroll_entry.name, self.employee1).status, "Submitted")
		self.assertEqual(get_salary_slip_details(payroll_entry.name, self.employee2).status, "Withheld")

		self.assertEqual([row["employee"] for row in payroll_entry.get_withheld_salaries()], [self.employee2])

	def test_release_without_selected_employees(self):
		create_salary_withholding(self.employee1, MONTH_1_START, 1).submit()
		create_salary_withholding(self.employee2, MONTH_1_START, 1).submit()
		payroll_entry = self._make_payroll_entry()

		self.assertIsNone(payroll_entry.make_bank_entry(for_withheld_salaries=1, employees=[]))

		for employee in (self.employee1, self.employee2):
			self.assertEqual(get_salary_slip_details(payroll_entry.name, employee).status, "Withheld")

	def test_withheld_salary_awaiting_release_is_not_paid_twice(self):
		create_salary_withholding(self.employee1, MONTH_1_START, 1).submit()
		payroll_entry = self._make_payroll_entry()

		bank_entry = payroll_entry.make_bank_entry(for_withheld_salaries=1)
		self.assertIsNotNone(bank_entry)

		self.assertEqual(payroll_entry.get_withheld_salaries(), [])
		self.assertIsNone(payroll_entry.make_bank_entry(for_withheld_salaries=1))

		self._submit_bank_entry(bank_entry)
		self.assertEqual(get_salary_slip_details(payroll_entry.name, self.employee1).status, "Submitted")

	def test_release_is_retried_after_the_release_entry_is_deleted(self):
		create_salary_withholding(self.employee1, MONTH_1_START, 1).submit()
		payroll_entry = self._make_payroll_entry()

		bank_entry = payroll_entry.make_bank_entry(for_withheld_salaries=1)
		frappe.delete_doc("Journal Entry", bank_entry.name, force=True)

		# the cycle still points at the deleted entry, but the salary is pending release again
		self.assertEqual([row["employee"] for row in payroll_entry.get_withheld_salaries()], [self.employee1])

		retried_entry = payroll_entry.make_bank_entry(for_withheld_salaries=1)
		self.assertIsNotNone(retried_entry)

		self._submit_bank_entry(retried_entry)
		self.assertEqual(get_salary_slip_details(payroll_entry.name, self.employee1).status, "Submitted")

	def _make_payroll_entry(self, date: str | None = None):
		dates = get_start_end_dates("Monthly", date or MONTH_1_START)

		return make_payroll_entry(
			start_date=dates.start_date,
			end_date=dates.end_date,
			payable_account=self.company.default_payroll_payable_account,
			currency=self.company.default_currency,
			company=self.company.name,
			cost_center="Main - _TC",
		)

	def _submit_bank_entry(self, bank_entry: dict):
		bank_entry.cheque_no = "123456"
		bank_entry.cheque_date = MONTH_1_START
		bank_entry.submit()

	def _get_payroll_employee_row(self, payroll_entry: dict) -> dict | None:
		payroll_entry.reload()
		return next(employee for employee in payroll_entry.employees if employee.employee == self.employee1)

	def test_status_on_discard(self):
		salary_withholding = create_salary_withholding(self.employee1, getdate())
		salary_withholding.discard()
		salary_withholding.reload()
		self.assertEqual(salary_withholding.status, "Cancelled")


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
