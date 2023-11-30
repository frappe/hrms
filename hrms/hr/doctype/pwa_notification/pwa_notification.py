# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document


class PWANotification(Document):
	def on_update(self):
		self.publish_update()

	def publish_update(self):
		frappe.publish_realtime(
			event="hrms:update_notifications",
			user=self.to_user,
			after_commit=True,
		)
