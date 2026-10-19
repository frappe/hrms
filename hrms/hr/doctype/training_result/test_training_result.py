# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.email.doctype.notification.notification import get_context

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
