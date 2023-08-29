# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe import bold


class PWANotificationsMixin:
	"""Mixin class for managing PWA updates"""

	def notify_approval_status(self):
		"""Send Leave Application & Expense Claim Approval status notification - to employees"""
		status_field = self._get_doc_status_field()
		status = self.get(status_field)

		if self.has_value_changed(status_field) and status in ["Approved", "Rejected"]:
			notification = frappe.new_doc("PWA Notification")
			notification.message = f"Your {self.doctype} {bold(self.name)} has been {bold(status)}"
			notification.from_user = self._get_doc_approver()
			notification.to_employee = self.employee

			notification.reference_document_type = self.doctype
			notification.reference_document_name = self.name
			notification.insert(ignore_permissions=True)

	def notify_approver(self):
		"""Send new Leave Application & Expense Claim request notification - to approvers"""
		notification = frappe.new_doc("PWA Notification")
		notification.message = (
			f"New {self.doctype} {bold(self.name)} request from {bold(self.employee_name)}"
		)
		notification.from_employee = self.employee
		notification.to_user = self._get_doc_approver()

		notification.reference_document_type = self.doctype
		notification.reference_document_name = self.name
		notification.insert(ignore_permissions=True)

	def _get_doc_status_field(self) -> str:
		APPROVAL_STATUS_FIELD = {
			"Leave Application": "status",
			"Expense Claim": "approval_status",
		}
		return APPROVAL_STATUS_FIELD[self.doctype]

	def _get_doc_approver(self) -> str:
		APPROVER_FIELD = {
			"Leave Application": "leave_approver",
			"Expense Claim": "expense_approver",
		}
		approver_field = APPROVER_FIELD[self.doctype]
		return self.get(approver_field)
