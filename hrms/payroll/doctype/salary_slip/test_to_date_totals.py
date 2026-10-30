# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import random_string

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.tests.utils import HRMSTestSuite


class TestSalaryToDateTotals(HRMSTestSuite):
	def test_recalculation_excludes_future_slips_and_uses_historical_base_amounts(self):
		employee = make_employee("test_historical_ytd@example.com", company="_Test Company")
		previous = self.make_slip(employee, "2026-01-01", "2026-01-31", 100, 80)
		self.make_slip(employee, "2026-02-01", "2026-02-14", 200, 90)
		current = self.make_slip(employee, "2026-02-15", "2026-02-28", 300, 100)
		self.make_slip(employee, "2026-03-01", "2026-03-31", 900, 100)
		self.make_slip(employee, "2026-01-01", "2026-01-31", 900, 100, docstatus=0)
		self.make_slip(employee, "2026-01-01", "2026-01-31", 900, 100, docstatus=2)

		current.compute_year_to_date()
		current.compute_month_to_date()
		current.compute_component_wise_year_to_date()
		self.assertEqual(current.year_to_date, 600)
		self.assertEqual(current.gross_year_to_date, 900)
		self.assertEqual(current.base_year_to_date, 56000)
		self.assertEqual(current.base_gross_year_to_date, 84000)
		self.assertEqual(current.month_to_date, 500)
		self.assertEqual(current.base_month_to_date, 48000)
		self.assertEqual(current.earnings[0].year_to_date, 900)

		previous.compute_year_to_date()
		previous.compute_component_wise_year_to_date()
		self.assertEqual(previous.year_to_date, 100)
		self.assertEqual(previous.earnings[0].year_to_date, 150)

	def make_slip(self, employee, start, end, net, exchange_rate, docstatus=1):
		# Persist controlled accounting amounts to exercise the aggregation queries independently
		# of salary-structure and attendance calculation.
		slip = frappe.get_doc(
			{
				"doctype": "Salary Slip",
				"name": "TEST-YTD-" + random_string(10),
				"employee": employee,
				"company": "_Test Company",
				"start_date": start,
				"end_date": end,
				"docstatus": docstatus,
				"net_pay": net,
				"gross_pay": net * 1.5,
				"base_net_pay": net * exchange_rate,
				"base_gross_pay": net * 1.5 * exchange_rate,
				"currency": "USD",
				"exchange_rate": exchange_rate,
				"earnings": [{"salary_component": "Basic", "amount": net * 1.5}],
			}
		)
		slip.db_insert()
		for row in slip.earnings:
			row.db_insert()
		return slip
