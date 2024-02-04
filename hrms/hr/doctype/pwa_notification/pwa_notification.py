# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.push_notification import PushNotification

import hrms


class PWANotification(Document):
	def on_update(self):
		hrms.refetch_resource("hrms:notifications", self.to_user)

	def after_insert(self):
		self.send_push_notification()

	def send_push_notification(self):
		try:
			url = frappe.utils.get_url()

			push_notification = PushNotification("hrms")
			if push_notification.is_enabled():
				push_notification.send_notification_to_user(
					self.to_user, self.reference_document_type, self.message, link=url, truncate_body=True
				)
		except Exception:
			self.log_error(f"Error sending push notification: {self.name}")
