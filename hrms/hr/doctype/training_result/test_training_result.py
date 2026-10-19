# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.email.doctype.notification.notification import get_context

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.training_event.test_training_event import (
	create_training_event,
	create_training_program,
)
from hrms.tests.utils import HRMSTestSuite


class TestTrainingResult(HRMSTestSuite):
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
		create_training_program("Basic Training")
		employees = [
			make_employee(f"training-result-{i}@example.com", company="_Test Company") for i in range(3)
		]
		event = create_training_event(
			[
				{"employee": employees[0], "attendance": "Present"},
				{"employee": employees[1], "attendance": "Absent"},
				{"employee": employees[2], "attendance": "Present", "status": "Feedback Submitted"},
			]
		)
		event.submit()
		result = frappe.get_doc(
			{
				"doctype": "Training Result",
				"training_event": event.name,
				"employees": [{"employee": employee} for employee in employees],
			}
		).insert()
		result.submit()
		event.reload()

		self.assertEqual(event.event_status, "Completed")
		self.assertEqual([row.status for row in event.employees], ["Completed", "Open", "Feedback Submitted"])
