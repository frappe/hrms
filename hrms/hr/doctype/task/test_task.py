# hrms/hr/doctype/task/test_task.py

import frappe
import unittest

class TestTask(unittest.TestCase):
    def setUp(self):
        # Create a user to be the approver
        self.approver = frappe.get_doc({
            "doctype": "User",
            "email": "test_approver@example.com",
            "first_name": "Test Approver"
        }).insert(ignore_permissions=True)

        # Create a task to test with
        self.task = frappe.get_doc({
            "doctype": "Task",
            "title": "Test Task for Time Summation",
            "owner": "Administrator",
            "approver": self.approver.name
        }).insert()

    def tearDown(self):
        # Clean up the created documents
        frappe.delete_doc("Task", self.task.name, ignore_permissions=True)
        frappe.delete_doc("User", self.approver.name, ignore_permissions=True)
        frappe.db.commit()

    def test_time_summation(self):
        # Add some time logs
        self.task.append("time_logs", {"hours": 2.5})
        self.task.append("time_logs", {"hours": 3.0})
        self.task.save()

        # Check if the actual_time is updated
        self.assertEqual(self.task.actual_time, 5.5)

        # Update a time log
        self.task.time_logs[0].hours = 2.0
        self.task.save()
        self.assertEqual(self.task.actual_time, 5.0)

    def test_approval_notification(self):
        # Mock frappe.sendmail
        frappe.sendmail = unittest.mock.MagicMock()

        # Change status to "In Review" and save
        self.task.status = "In Review"
        self.task.save()

        # Check if sendmail was called
        frappe.sendmail.assert_called_once()
        args, kwargs = frappe.sendmail.call_args
        self.assertIn(self.approver.email, kwargs['recipients'])
        self.assertIn("ready for your review", kwargs['subject'])

        # Reset mock and save again to ensure it doesn't send again
        frappe.sendmail.reset_mock()
        self.task.save()
        frappe.sendmail.assert_not_called()
