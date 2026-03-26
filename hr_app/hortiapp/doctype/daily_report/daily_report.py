import frappe
from frappe.model.document import Document


class DailyReport(Document):
	def before_insert(self):
		if not self.employee:
			employee = frappe.db.get_value(
				"Employee",
				{"user_id": frappe.session.user, "status": "Active"},
				"name",
			)
			if employee:
				self.employee = employee

	def validate(self):
		if self.employee:
			self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
