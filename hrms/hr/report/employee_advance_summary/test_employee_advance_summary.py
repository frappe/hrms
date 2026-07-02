# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.employee_advance.test_employee_advance import make_employee_advance
from hrms.hr.report.employee_advance_summary.employee_advance_summary import execute
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeAdvanceSummary(HRMSTestSuite):
	def setUp(self):
		frappe.db.delete("Employee Advance")
		frappe.set_user("Administrator")
		frappe.db.set_value("Account", "_Test Employee Advance - _TC", "account_type", "Receivable")

		self.employee = make_employee("test_employee_advance_summary@example.com", "_Test Company")

	def test_employee_advance_summary(self):
		advance = make_employee_advance(self.employee)
		advance.reload()

		filters = frappe._dict(
			{
				"company": "_Test Company",
				"employee": self.employee,
			}
		)

		report = execute(filters)
		row = report[1][0]

		self.assertEqual(len(report[1]), 1)
		self.assertEqual(row.title, advance.name)
		self.assertEqual(row.employee, f"{self.employee}: test_employee_advance_summary@example.com")
		self.assertEqual(row.company, "_Test Company")
		self.assertEqual(row.posting_date, advance.posting_date)
		self.assertEqual(row.advance_amount, advance.advance_amount)
		self.assertEqual(row.paid_amount, advance.paid_amount)
		self.assertEqual(row.claimed_amount, advance.claimed_amount)
		self.assertEqual(row.return_amount, advance.return_amount)
		self.assertEqual(
			row.outstanding_amount, advance.paid_amount - advance.claimed_amount - advance.return_amount
		)
		self.assertEqual(row.status, advance.status)
		self.assertEqual(row.currency, advance.currency)

	def test_employee_advance_summary_grouped_by_employee(self):
		advance = make_employee_advance(self.employee)
		advance.reload()

		filters = frappe._dict(
			{
				"company": "_Test Company",
				"employee": self.employee,
				"group_by": "Employee",
			}
		)

		report = execute(filters)
		group_row, advance_row, total_row = report[1]

		self.assertEqual(report[5], 1)
		self.assertEqual(group_row.title, f"{self.employee}: test_employee_advance_summary@example.com")
		self.assertEqual(group_row.advance_amount, advance.advance_amount)
		self.assertEqual(group_row.paid_amount, advance.paid_amount)
		self.assertEqual(group_row.claimed_amount, advance.claimed_amount)
		self.assertEqual(group_row.return_amount, advance.return_amount)
		self.assertEqual(
			group_row.outstanding_amount, advance.paid_amount - advance.claimed_amount - advance.return_amount
		)
		self.assertEqual(group_row.currency, advance.currency)
		self.assertEqual(group_row.indent, 0)

		self.assertEqual(advance_row.title, advance.name)
		self.assertEqual(advance_row.employee, f"{self.employee}: test_employee_advance_summary@example.com")
		self.assertEqual(advance_row.advance_account, advance.advance_account)
		self.assertEqual(advance_row.company, "_Test Company")
		self.assertEqual(advance_row.posting_date, advance.posting_date)
		self.assertEqual(advance_row.advance_amount, advance.advance_amount)
		self.assertEqual(advance_row.paid_amount, advance.paid_amount)
		self.assertEqual(advance_row.claimed_amount, advance.claimed_amount)
		self.assertEqual(advance_row.return_amount, advance.return_amount)
		self.assertEqual(
			advance_row.outstanding_amount,
			advance.paid_amount - advance.claimed_amount - advance.return_amount,
		)
		self.assertEqual(advance_row.status, advance.status)
		self.assertEqual(advance_row.currency, advance.currency)
		self.assertEqual(advance_row.indent, 1)

		self.assertEqual(total_row.title, "Total")
		self.assertEqual(total_row.advance_amount, advance.advance_amount)
		self.assertEqual(total_row.paid_amount, advance.paid_amount)
		self.assertEqual(total_row.claimed_amount, advance.claimed_amount)
		self.assertEqual(total_row.return_amount, advance.return_amount)
		self.assertEqual(
			total_row.outstanding_amount, advance.paid_amount - advance.claimed_amount - advance.return_amount
		)
		self.assertEqual(total_row.currency, advance.currency)
		self.assertEqual(total_row.indent, 0)
