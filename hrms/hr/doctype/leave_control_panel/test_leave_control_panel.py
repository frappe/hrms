# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from datetime import date

import frappe
from frappe.tests.utils import FrappeTestCase

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.leave_control_panel.leave_control_panel import LeaveControlPanel
from hrms.hr.doctype.leave_period.test_leave_period import create_leave_period
from hrms.hr.doctype.leave_policy.test_leave_policy import create_leave_policy
from hrms.tests.test_utils import create_company


class TestLeaveControlPanel(FrappeTestCase):
	@classmethod
	def setUpClass(self):
		create_company()
		super().setUpClass()
		frappe.db.sql("delete from `tabEmployee` where company='_Test Company'")

		self.create_records()

	@classmethod
	def tearDownClass(self):
		frappe.db.rollback()

	@classmethod
	def create_records(self):
		self.leave_period = create_leave_period(date(2030, 1, 1), date(2030, 12, 31), "_Test Company")
		self.leave_policy = create_leave_policy(leave_type="Casual Leave", annual_allocation=10)
		self.leave_policy.submit()

		self.emp1 = make_employee(
			"employee1@example.com",
			company="_Test Company",
		)
		self.emp2 = make_employee(
			"employee2@example.com",
			company="_Test Company",
		)
		self.emp3 = make_employee(
			"employee3@example.com",
			company="_Test Company",
		)

	def test_allocation_based_on_leave_type(self):
		args = {
			"doctype": "Leave Control Panel",
			"dates_based_on": "Custom Range",
			"from_date": date(2030, 4, 1),
			"to_date": date(2030, 4, 30),
			"allocate_based_on_leave_policy": 0,
			"leave_type": "Sick Leave",
			"no_of_days": 5,
		}
		lcp = LeaveControlPanel(args)
		lcp.allocate_leave([self.emp1, self.emp2])

		leave_allocations = frappe.get_list(
			"Leave Allocation",
			filters={"employee": ["in", [self.emp1, self.emp2]]},
			fields=["leave_type", "total_leaves_allocated", "from_date", "to_date"],
		)
		self.assertEqual(leave_allocations[0], leave_allocations[1])
		self.assertEqual(leave_allocations[0].leave_type, args["leave_type"])
		self.assertEqual(leave_allocations[0].total_leaves_allocated, args["no_of_days"])
		self.assertEqual(leave_allocations[0].from_date, args["from_date"])
		self.assertEqual(leave_allocations[0].to_date, args["to_date"])

	def test_allocation_based_on_leave_policy_assignment(self):
		args = {
			"doctype": "Leave Control Panel",
			"dates_based_on": "Leave Period",
			"leave_period": self.leave_period.name,
			"allocate_based_on_leave_policy": 1,
			"leave_policy": self.leave_policy,
		}
		lcp = LeaveControlPanel(args)
		lcp.allocate_leave([self.emp3])

		lpa = frappe.get_value(
			"Leave Policy Assignment",
			{"employee": self.emp3},
			["leave_policy", "leave_period", "effective_from", "effective_to"],
			as_dict=1,
		)
		self.assertEqual(lpa.leave_policy, self.leave_policy.name)
		self.assertEqual(lpa.leave_period, self.leave_period.name)
		self.assertEqual(lpa.effective_from, self.leave_period.from_date)
		self.assertEqual(lpa.effective_to, self.leave_period.to_date)
