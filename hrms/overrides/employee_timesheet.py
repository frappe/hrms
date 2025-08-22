# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from frappe.utils.data import flt

from erpnext.projects.doctype.timesheet.timesheet import Timesheet


class EmployeeTimesheet(Timesheet):
	def set_status(self):
		self.status = {"0": "Draft", "1": "Submitted", "2": "Cancelled"}[str(self.docstatus or 0)]

		if flt(self.per_billed, self.precision("per_billed")) >= 100.0:
			self.status = "Billed"

		if self.salary_slip:
			self.status = "Payslip"

		if self.sales_invoice and self.salary_slip:
			self.status = "Completed"
