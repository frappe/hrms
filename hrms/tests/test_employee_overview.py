# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import add_days, flt, getdate, today

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.employee_advance.test_employee_advance import make_employee_advance
from hrms.hr.doctype.expense_claim.test_expense_claim import get_payable_account, make_expense_claim
from hrms.hr.doctype.leave_allocation.test_leave_allocation import create_leave_allocation
from hrms.overrides import employee_overview
from hrms.payroll.doctype.salary_slip.test_salary_slip import (
	make_employee_salary_slip,
	make_leave_application,
	mark_attendance,
)
from hrms.tests.utils import HRMSTestSuite, make_user


class TestEmployeeOverview(HRMSTestSuite):
	def setUp(self):
		self.employee = make_employee("employee_overview@example.com", company="_Test Company")

	def overview(self, employee=None):
		data = employee_overview.get_employee_overview(employee or self.employee, "Last 12 Months")
		self.assertFalse(data["errors"])
		return data

	def test_pay_matches_submitted_slips(self):
		slip = make_employee_salary_slip(self.employee, "Monthly")
		slip.submit()

		pay = self.overview()["pay"]
		self.assertEqual(flt(pay["gross"]["value"], 2), flt(slip.base_gross_pay, 2))
		self.assertEqual(flt(pay["net"]["value"], 2), flt(slip.base_net_pay, 2))
		self.assertEqual(pay["gross"]["count"], 1)
		self.assertEqual(flt(sum(p["gross"] for p in pay["points"]), 2), flt(slip.base_gross_pay, 2))

	def test_pay_leaves_out_slips_from_other_companies(self):
		slip = make_employee_salary_slip(self.employee, "Monthly")
		slip.submit()
		frappe.db.set_value("Salary Slip", slip.name, "company", "_Test Company 3")

		pay = self.overview()["pay"]
		self.assertEqual((pay["gross"]["value"], pay["gross"]["count"]), (0, 0))

	def test_attendance_rate_counts_half_days(self):
		as_of = getdate(today())
		for days_ago, status, half_day_status in (
			(4, "Present", None),
			(3, "Half Day", "Present"),
			(2, "Half Day", "Absent"),
			(1, "Absent", None),
		):
			mark_attendance(
				self.employee,
				add_days(as_of, -days_ago),
				status,
				ignore_validate=True,
				half_day_status=half_day_status,
			)

		attendance = self.overview()["attendance"]
		self.assertEqual(attendance["marked"], 4)
		self.assertEqual(attendance["counts"]["Half Day"], 2)
		self.assertEqual(attendance["days_worked"], 1.5)
		self.assertEqual(attendance["rate"], 37.5)

	def test_leave_balance_and_open_requests(self):
		allocation = create_leave_allocation(
			employee=self.employee, from_date=add_days(today(), -30), new_leaves_allocated=10
		)
		allocation.submit()
		make_leave_application(
			self.employee,
			add_days(today(), 10),
			add_days(today(), 11),
			"_Test Leave Type",
			status="Open",
			submit=False,
		)

		data = self.overview()
		self.assertEqual(data["leave"]["remaining"], 10)
		self.assertEqual(data["leave"]["pending"], 2)
		requests = data["pipeline"]["leave_requests"]
		self.assertEqual((requests["count"], requests["value"], requests["started"]), (1, 2, 0))

	def test_claims_awaiting_approval_and_unpaid(self):
		company = "_Test Company 3"
		employee = make_employee("employee_overview_claims@example.com", company=company)
		payable = get_payable_account(company)
		make_expense_claim(
			payable,
			300,
			300,
			company,
			"Travel Expenses - _TC3",
			employee=employee,
			approval_status="Draft",
			do_not_submit=True,
		).insert()
		make_expense_claim(payable, 500, 400, company, "Travel Expenses - _TC3", employee=employee)

		pipeline = self.overview(employee)["pipeline"]
		self.assertEqual(pipeline["claims_awaiting"], {"value": 300, "count": 1})
		self.assertEqual(pipeline["claims_unpaid"], {"value": 400, "count": 1})

		rows = employee_overview.get_employee_transactions(employee, "Expense Claim")
		self.assertEqual(sorted(r["outstanding"] or 0 for r in rows), [0, 400])

	def test_unpaid_advance_is_yet_to_be_paid(self):
		make_employee_advance(self.employee)

		advances = self.overview()["pipeline"]["advances"]
		self.assertEqual((advances["value"], advances["to_pay"], advances["count"]), (0, 1000, 1))

	def test_activity_and_transactions(self):
		self.assertFalse(employee_overview.has_activity(self.employee))
		advance = make_employee_advance(self.employee)

		self.assertTrue(employee_overview.has_activity(self.employee))
		rows = employee_overview.get_employee_transactions(self.employee)
		self.assertEqual([r["name"] for r in rows], [advance.name])
		self.assertEqual(rows[0]["amount"], 1000)
		self.assertEqual(rows[0]["currency"], advance.currency)

	def test_user_without_employee_access_is_refused(self):
		user = make_user("employee_overview_blocked@example.com", "Website Manager")
		frappe.set_user(user)
		try:
			self.assertRaises(frappe.PermissionError, employee_overview.get_employee_overview, self.employee)
			self.assertRaises(
				frappe.PermissionError, employee_overview.get_employee_transactions, self.employee
			)
		finally:
			frappe.set_user("Administrator")

	def test_overview_tab_comes_second(self):
		meta = frappe.get_meta("Employee")
		tabs = [f.fieldname for f in meta.fields if f.fieldtype == "Tab Break"]
		self.assertEqual(tabs[:2], ["basic_details_tab", "overview_tab"])
		fieldnames = [f.fieldname for f in meta.fields]
		self.assertEqual(fieldnames.index("overview_html"), fieldnames.index("overview_tab") + 1)
		self.assertLess(fieldnames.index("first_name"), fieldnames.index("overview_tab"))
		self.assertEqual(meta.get_field("basic_details_tab").label, "Details")
