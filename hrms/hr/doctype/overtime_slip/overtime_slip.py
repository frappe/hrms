# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import timedelta
from email.utils import formatdate

import frappe
from frappe import _, bold
from frappe.model.docstatus import DocStatus
from frappe.model.document import Document
from frappe.utils.data import get_link_to_form, getdate

from hrms.payroll.doctype.payroll_entry.payroll_entry import get_start_end_dates
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
	get_assigned_salary_structure,
)


class OvertimeSlip(Document):
	def validate(self):
		if not (self.from_date or self.to_date or self.payroll_frequency):
			self.get_frequency_and_dates()

		self.validate_overlap()
		if self.from_date >= self.to_date:
			frappe.throw(_("From date can not be greater than To date"))

		if not len(self.overtime_details):
			self.get_emp_and_overtime_details()

	def validate_overlap(self):
		overtime_slips = frappe.db.get_all(
			"Overtime Slip",
			filters={
				"docstatus": ("<", 2),
				"employee": self.employee,
				"to_date": (">=", self.from_date),
				"from_date": ("<=", self.to_date),
				"name": ("!=", self.name),
			},
		)
		if len(overtime_slips):
			form_link = get_link_to_form("Overtime Slip", overtime_slips[0].name)
			msg = _("Overtime Slip:{0} has been created between {1} and {1}").format(
				bold(form_link), bold(formatdate(self.from_date)), bold(formatdate(self.to_date))
			)
			frappe.throw(msg)

	def on_submit(self):
		if self.status == "Pending":
			frappe.throw(_("Overtime Slip with Status 'Approved' or 'Rejected' are allowed for Submission"))

	@frappe.whitelist()
	def get_frequency_and_dates(self):
		date = self.from_date or self.posting_date

		salary_structure = get_assigned_salary_structure(self.employee, date)
		if salary_structure:
			payroll_frequency = frappe.db.get_value("Salary Structure", salary_structure, "payroll_frequency")
			date_details = get_start_end_dates(
				payroll_frequency, date, frappe.db.get_value("Employee", self.employee, "company")
			)
			self.from_date = date_details.start_date
			self.to_date = date_details.end_date
			self.payroll_frequency = payroll_frequency
		else:
			frappe.throw(_("No Salary Structure Assignment found for Employee: {0}").format(self.employee))

	@frappe.whitelist()
	def get_emp_and_overtime_details(self):
		records = self.get_attendance_record()
		if len(records):
			self.create_overtime_details_row_for_attendance(records)
		if len(self.overtime_details):
			self.total_overtime_duration = timedelta()
			for detail in self.overtime_details:
				if detail.overtime_duration is not None:
					self.total_overtime_duration += detail.overtime_duration

	def create_overtime_details_row_for_attendance(self, records):
		self.overtime_details = []
		for record in records:
			if record.overtime_duration:
				self.append(
					"overtime_details",
					{
						"reference_document_type": "Attendance",
						"reference_document": record.name,
						"date": record.attendance_date,
						"overtime_type": record.overtime_type,
						"overtime_duration": record.overtime_duration,
						"standard_working_hours": record.standard_working_hours,
					},
				)

	def get_attendance_record(self):
		records = []
		if self.from_date and self.to_date:
			records = frappe.get_all(
				"Attendance",
				fields=[
					"overtime_duration",
					"name",
					"attendance_date",
					"overtime_type",
					"standard_working_hours",
				],
				filters={
					"employee": self.employee,
					"docstatus": DocStatus.submitted(),
					"attendance_date": ("between", [getdate(self.from_date), getdate(self.to_date)]),
					"status": "Present",
					"overtime_type": ["!=", ""],
				},
			)
		return records
