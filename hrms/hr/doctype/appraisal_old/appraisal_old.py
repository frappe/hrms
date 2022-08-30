# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class AppraisalCycle(Document):
	@frappe.whitelist()
	def get_employees(self):
		# pull employees in appraisee list based on selected filters
		employees = self.get_employees_for_appraisal()

		if employees:
			self.set("appraisee_list", [])

			for data in employees:
				self.append(
					"appraisee_list",
					{
						"employee": data.name,
						"employee_name": data.employee_name,
						"branch": data.branch,
						"designation": data.designation,
						"department": data.department,
					},
				)
				return self
		else:
			self.set("appraisee_list", [])
			frappe.msgprint(_("No employees found for the selected criteria"))

	def get_employees_for_appraisal(self):
		filters = {
			"status": "Active",
			"company": self.company,
		}
		if self.department:
			filters["department"] = self.department
		if self.branch:
			filters["branch"] = self.branch
		if self.designation:
			filters["designation"] = self.designation

		employees = frappe.db.get_list(
			"Employee",
			filters=filters,
			fields=["name", "employee_name", "branch", "designation", "department"],
		)

		return employees
