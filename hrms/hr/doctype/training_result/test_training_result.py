# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.email.doctype.notification.notification import get_context

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.training_event.test_training_event import (
	create_training_event,
	create_training_program,
)
from hrms.tests.utils import HRMSTestSuite, make_user


class TestTrainingResult(HRMSTestSuite):
	def setUp(self):
		self.user = make_user("training-manager@example.com")
		create_training_program("Basic Training")
		employees = [
			make_employee(f"training-result-{i}@example.com", company="_Test Company") for i in range(3)
		]
		self.event = create_training_event(
			[
				{"employee": employees[0], "attendance": "Present"},
				{"employee": employees[1], "attendance": "Absent"},
				{"employee": employees[2], "attendance": "Present", "status": "Feedback Submitted"},
			]
		)
		self.event.submit()
		self.result = frappe.get_doc(
			{
				"doctype": "Training Result",
				"training_event": self.event.name,
				"employees": [{"employee": employee, "grade": "C"} for employee in employees],
			}
		).insert()

	def test_training_feedback_notification(self):
		frappe.reload_doc("hr", "notification", "training_feedback", force=True)
		notification = frappe.get_doc("Notification", "Training Feedback")
		result = frappe.get_doc({"doctype": "Training Result", "training_event": "Test Training Event"})
		context = get_context(result)
		notification.load_standard_properties(context)

		message = frappe.render_template(notification.message, context, restrict_globals=True)
		self.assertIn("Test Training Event", message)
		self.assertIn("Please share your feedback", message)

	def test_submit_completes_training_event(self):
		self.result.submit()
		self.event.reload()

		self.assertEqual(self.event.event_status, "Completed")
		self.assertEqual(
			[row.status for row in self.event.employees], ["Completed", "Open", "Feedback Submitted"]
		)

	def test_amend_cancelled_training_result(self):
		with self.set_user(self.user):
			self.result.submit()
			for grade in ("B", "A"):
				self.result.cancel()
				amended = frappe.copy_doc(self.result)
				amended.docstatus = 0
				amended.amended_from = self.result.name
				amended.employees[0].grade = grade
				amended.insert()
				amended.submit()
				amended.reload()

				self.assertEqual(amended.docstatus, 1)
				self.assertEqual(amended.training_event, self.result.training_event)
				self.assertEqual(amended.employees[0].grade, grade)
				self.assertEqual(self.result.reload().docstatus, 2)
				self.result = amended

	def test_duplicate_active_training_result(self):
		with self.set_user(self.user):
			for docstatus in (0, 1):
				with self.subTest(docstatus=docstatus):
					if docstatus:
						self.result.submit()
					else:
						self.result.employees[0].grade = "B"
						self.result.save()

					duplicate = frappe.copy_doc(self.result)
					duplicate.docstatus = 0
					self.assertRaises(frappe.UniqueValidationError, duplicate.insert)
