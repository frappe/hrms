# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Task(Document):
    def validate(self):
        self.update_actual_time()

    def on_update(self):
        self.set_completion_date()
        self.send_approval_notification()

    def set_completion_date(self):
        """Set the completion date when the task is moved to 'Done'."""
        if self.status == "Done" and not self.completion_date:
            self.completion_date = frappe.utils.nowdate()

    def update_actual_time(self):
        """Calculates the total actual time from the child `Time Log` table."""
        total_hours = 0
        for log in self.get("time_logs"):
            total_hours += log.hours

        # To prevent recursion, only set the value if it has changed
        if self.actual_time != total_hours:
            self.actual_time = total_hours

    def send_approval_notification(self):
        """Send a notification to the approver when the task is moved to 'In Review'."""
        if self.is_new():
            return

        # Get the document before the update
        doc_before_save = self.get_doc_before_save()
        if not doc_before_save:
            return

        # Check if status has changed to "In Review"
        if (doc_before_save.status != "In Review" and self.status == "In Review" and self.approver):
            frappe.sendmail(
                recipients=[self.approver],
                subject=f"Task '{self.title}' is ready for your review",
                message=f"""
                    <p>Hello,</p>
                    <p>The task <b>{self.title}</b> (ID: {self.name}) has been marked as 'In Review' by {self.owner} and is waiting for your approval.</p>
                    <p>You can view the task here: {self.get_url()}</p>
                """,
                now=True # Send immediately
            )
