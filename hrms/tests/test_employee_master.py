# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.overrides.employee_master import set_status_left_after_relieving_date
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeMaster(HRMSTestSuite):
	def test_left_status_waits_for_relieving_date(self):
		employee = frappe.get_doc(
			"Employee", make_employee("left_future@example.com", company="_Test Company")
		)

		employee.status = "Left"
		employee.relieving_date = add_days(getdate(), 1)
		self.assertRaises(frappe.ValidationError, employee.save)
		self.assertTrue(frappe.db.get_value("User", employee.user_id, "enabled"))

		# The last working day is today, so the employee can be marked Left now.
		employee.relieving_date = getdate()
		employee.save()
		self.assertFalse(frappe.db.get_value("User", employee.user_id, "enabled"))

	def test_status_set_to_left_after_relieving_date(self):
		left = make_relieving_employee("relieved_yesterday@example.com", add_days(getdate(), -1))
		serving = make_relieving_employee("serving_notice@example.com", add_days(getdate(), 1))
		leaves_today = make_relieving_employee("leaves_today@example.com", getdate())

		set_status_left_after_relieving_date()

		self.assertEqual(frappe.db.get_value("Employee", left, "status"), "Left")
		self.assertFalse(frappe.db.get_value("User", "relieved_yesterday@example.com", "enabled"))
		for employee, user in (
			(serving, "serving_notice@example.com"),
			(leaves_today, "leaves_today@example.com"),
		):
			self.assertEqual(frappe.db.get_value("Employee", employee, "status"), "Active")
			self.assertTrue(frappe.db.get_value("User", user, "enabled"))

	def test_manager_and_reportee_leave_on_same_day(self):
		yesterday = add_days(getdate(), -1)
		manager = make_relieving_employee("left_manager@example.com", yesterday)
		reportee = make_relieving_employee("left_reportee@example.com", yesterday, reports_to=manager)

		set_status_left_after_relieving_date()

		self.assertEqual(frappe.db.get_value("Employee", manager, "status"), "Left")
		self.assertEqual(frappe.db.get_value("Employee", reportee, "status"), "Left")

	def test_failed_employee_is_logged_and_others_continue(self):
		yesterday = add_days(getdate(), -1)
		manager = make_relieving_employee("blocked_manager@example.com", yesterday)
		staying = make_employee("staying_reportee@example.com", company="_Test Company", reports_to=manager)
		other = make_relieving_employee("other_leaver@example.com", yesterday)

		with patch("hrms.overrides.employee_master.frappe.log_error") as log_error:
			set_status_left_after_relieving_date()

		# An Active employee still reports to the manager, so the manager stays Active.
		self.assertEqual(frappe.db.get_value("Employee", manager, "status"), "Active")
		# Only the manager failed: the reportee without a Relieving Date was not picked up.
		log_error.assert_called_once()
		self.assertEqual(log_error.call_args.kwargs["reference_name"], manager)
		self.assertEqual(frappe.db.get_value("Employee", staying, "status"), "Active")
		self.assertEqual(frappe.db.get_value("Employee", other, "status"), "Left")


def make_relieving_employee(user, relieving_date, **kwargs):
	return make_employee(user, company="_Test Company", relieving_date=relieving_date, **kwargs)
