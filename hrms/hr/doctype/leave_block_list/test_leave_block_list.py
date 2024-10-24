# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import getdate

from hrms.hr.doctype.leave_block_list.leave_block_list import get_applicable_block_dates

test_dependencies = ["Employee"]
test_records = frappe.get_test_records("Leave Block List")


class TestLeaveBlockList(IntegrationTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")

	def test_get_applicable_block_dates(self):
		frappe.set_user("test@example.com")
		frappe.db.set_value(
			"Department", "_Test Department - _TC", "leave_block_list", "_Test Leave Block List"
		)
		block_days = [d.block_date for d in get_applicable_block_dates("2013-01-01", "2013-01-03")]
		self.assertIn(getdate("2013-01-02"), block_days)

	def test_get_applicable_block_dates_for_allowed_user(self):
		frappe.set_user("test1@example.com")
		frappe.db.set_value(
			"Department", "_Test Department 1 - _TC", "leave_block_list", "_Test Leave Block List"
		)
		self.assertEqual([], [d.block_date for d in get_applicable_block_dates("2013-01-01", "2013-01-03")])

	def test_get_applicable_block_dates_all_lists(self):
		frappe.set_user("test1@example.com")
		frappe.db.set_value(
			"Department", "_Test Department 1 - _TC", "leave_block_list", "_Test Leave Block List"
		)
		block_days = [
			d.block_date for d in get_applicable_block_dates("2013-01-01", "2013-01-03", all_lists=True)
		]
		self.assertIn(getdate("2013-01-02"), block_days)

	def test_get_applicable_block_dates_all_lists_for_leave_type(self):
		frappe.set_user("test1@example.com")
		frappe.db.set_value("Department", "_Test Department 1 - _TC", "leave_block_list", "")

		block_days = [
			d.block_date
			for d in get_applicable_block_dates(
				"2013-01-01", "2013-01-31", all_lists=True, leave_type="Casual Leave"
			)
		]
		self.assertIn(getdate("2013-01-16"), block_days)
		self.assertIn(getdate("2013-01-19"), block_days)
		self.assertIn(getdate("2013-01-02"), block_days)
		self.assertNotIn(getdate("2013-01-25"), block_days)

	def test_get_applicable_block_dates_for_allowed_user_for_leave_type(self):
		frappe.set_user("test1@example.com")
		frappe.db.set_value("Department", "_Test Department 1 - _TC", "leave_block_list", "")

		block_days = [
			d.block_date
			for d in get_applicable_block_dates("2013-01-01", "2013-01-31", leave_type="Casual Leave")
		]
		self.assertIn(getdate("2013-01-19"), block_days)
		self.assertNotIn(getdate("2013-01-16"), block_days)
		self.assertNotIn(getdate("2013-01-02"), block_days)
		self.assertNotIn(getdate("2013-01-25"), block_days)
