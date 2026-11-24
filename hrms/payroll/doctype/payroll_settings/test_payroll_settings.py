# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from hrms.payroll.doctype.payroll_settings.payroll_settings import (
	get_current_holiday_lists_without_weekly_offs,
)
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.tests.utils import HRMSTestSuite


class TestPayrollSettings(HRMSTestSuite):
	@HRMSTestSuite.change_settings(
		"Payroll Settings",
		{"include_holidays_in_total_working_days": 0, "exclude_only_weekly_offs_from_working_days": 0},
	)
	def test_warn_about_holiday_lists_without_weekly_offs(self):
		without_weekly_offs = make_holiday_list("Test Payroll Settings No Weekly Offs", add_weekly_offs=False)
		with_weekly_offs = make_holiday_list("Test Payroll Settings Weekly Offs")

		lists = get_current_holiday_lists_without_weekly_offs()
		self.assertIn(without_weekly_offs, lists)
		self.assertNotIn(with_weekly_offs, lists)

		frappe.clear_messages()
		settings = frappe.get_single("Payroll Settings")
		settings.exclude_only_weekly_offs_from_working_days = 1
		settings.save()

		messages = " ".join(message.get("message", "") for message in frappe.get_message_log())
		self.assertIn(without_weekly_offs, messages)
		self.assertNotIn(with_weekly_offs, messages)
