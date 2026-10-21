# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import add_days, nowdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.tests.utils import HRMSTestSuite

# test_records = frappe.get_test_records("Leave Type")


def create_leave_type(**args):
	args = frappe._dict(args)
	leave_type_name = args.leave_type_name or "_Test Leave Type"
	if frappe.db.exists("Leave Type", leave_type_name):
		frappe.delete_doc("Leave Type", leave_type_name, force=True)

	leave_type = frappe.get_doc(
		{
			"doctype": "Leave Type",
			"leave_type_name": leave_type_name,
			"include_holiday": args.include_holidays or 1,
			"allow_encashment": args.allow_encashment or 0,
			"is_earned_leave": args.is_earned_leave or 0,
			"is_lwp": args.is_lwp or 0,
			"is_ppl": args.is_ppl or 0,
			"is_carry_forward": args.is_carry_forward or 0,
			"expire_carry_forwarded_leaves_after_days": args.expire_carry_forwarded_leaves_after_days or 0,
			"non_encashable_leaves": args.non_encashable_leaves or 5,
			"earning_component": "Leave Encashment",
			"max_leaves_allowed": args.max_leaves_allowed,
			"maximum_carry_forwarded_leaves": args.maximum_carry_forwarded_leaves,
			"allocate_on_day": args.allocate_on_day or "Last Day",
		}
	)

	if leave_type.is_ppl:
		leave_type.fraction_of_daily_salary_per_leave = args.fraction_of_daily_salary_per_leave or 0.5

	if leave_type.is_earned_leave and args.earned_leave_frequency:
		leave_type.earned_leave_frequency = args.earned_leave_frequency

	leave_type.insert()

	return leave_type


class TestLeaveType(HRMSTestSuite):
	def test_date_of_joining_only_for_monthly_earned_leave(self):
		for frequency in ("Quarterly", "Half-Yearly", "Yearly"):
			with self.assertRaises(frappe.ValidationError):
				create_leave_type(
					leave_type_name="_Test Earned Leave DOJ",
					is_earned_leave=1,
					earned_leave_frequency=frequency,
					allocate_on_day="Date of Joining",
				)

		leave_type = create_leave_type(
			leave_type_name="_Test Earned Leave DOJ",
			is_earned_leave=1,
			earned_leave_frequency="Monthly",
			allocate_on_day="Date of Joining",
		)
		self.assertEqual(leave_type.allocate_on_day, "Date of Joining")

	def test_draft_allocation_does_not_block_lwp(self):
		leave_type = create_leave_type(leave_type_name="_Test LWP Draft Allocation")
		employee = make_employee("test_lwp_draft_allocation@example.com", company="_Test Company")
		frappe.get_doc(
			{
				"doctype": "Leave Allocation",
				"employee": employee,
				"leave_type": leave_type.name,
				"from_date": add_days(nowdate(), -10),
				"to_date": add_days(nowdate(), 10),
				"new_leaves_allocated": 5,
			}
		).insert()

		leave_type.is_lwp = 1
		leave_type.save()
		self.assertEqual(frappe.db.get_value("Leave Type", leave_type.name, "is_lwp"), 1)
