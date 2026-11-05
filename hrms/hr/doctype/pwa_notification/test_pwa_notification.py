# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.api import mark_notification_as_read
from hrms.tests.utils import HRMSTestSuite


class TestPWANotification(HRMSTestSuite):
	def setUp(self):
		self.user_a = "pwa_notification_a@example.com"
		self.user_b = "pwa_notification_b@example.com"
		make_employee(self.user_a, company="_Test Company")
		make_employee(self.user_b, company="_Test Company")
		self.notification = make_notification(self.user_a)

	def test_notification_visible_only_to_recipient(self):
		with self.set_user(self.user_b):
			self.assertEqual(frappe.get_list("PWA Notification", filters={"to_user": self.user_a}), [])
			self.assertFalse(frappe.has_permission("PWA Notification", doc=self.notification.name))

		with self.set_user(self.user_a):
			self.assertEqual(
				frappe.get_list("PWA Notification", filters={"to_user": self.user_a}, pluck="name"),
				[self.notification.name],
			)
			self.assertTrue(frappe.has_permission("PWA Notification", doc=self.notification.name))

	def test_mark_notification_as_read(self):
		with self.set_user(self.user_b):
			mark_notification_as_read(self.notification.name)
		self.assertEqual(frappe.db.get_value("PWA Notification", self.notification.name, "read"), 0)

		with self.set_user(self.user_a):
			mark_notification_as_read(self.notification.name)
		self.assertEqual(frappe.db.get_value("PWA Notification", self.notification.name, "read"), 1)

	def test_no_approval_status_notification_without_employee_user(self):
		employee = make_employee("pwa_notification_no_user@example.com", company="_Test Company")
		frappe.db.set_value("Employee", employee, "user_id", None)

		shift_request = frappe.new_doc("Shift Request")
		shift_request.update({"name": "_Test PWA Shift Request", "employee": employee, "status": "Approved"})
		with patch.object(shift_request, "has_value_changed", return_value=True):
			shift_request.notify_approval_status()

		self.assertFalse(
			frappe.db.exists("PWA Notification", {"reference_document_name": "_Test PWA Shift Request"})
		)

	def test_shift_request_push_link(self):
		notification = frappe.get_doc(
			{
				"doctype": "PWA Notification",
				"reference_document_type": "Shift Request",
				"reference_document_name": "HR-SHR-0001",
			}
		)
		self.assertTrue(notification.get_notification_link().endswith("/hrms/shift-requests/HR-SHR-0001"))


def make_notification(to_user):
	return frappe.get_doc(
		{
			"doctype": "PWA Notification",
			"from_user": "Administrator",
			"to_user": to_user,
			"message": "Your Leave Application has been Approved",
			"reference_document_type": "Leave Application",
			"reference_document_name": "_Test Leave Application",
		}
	).insert(ignore_permissions=True)
