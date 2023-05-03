# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, format_date, getdate

from erpnext.setup.doctype.employee.employee import is_holiday

from hrms.hr.utils import validate_active_employee, validate_dates


class AttendanceRequest(Document):
	def validate(self):
		validate_active_employee(self.employee)
		validate_dates(self, self.from_date, self.to_date)
		if self.half_day:
			if not getdate(self.from_date) <= getdate(self.half_day_date) <= getdate(self.to_date):
				frappe.throw(_("Half day date should be in between from date and to date"))

	def on_submit(self):
		self.create_attendance_records()

	def on_cancel(self):
		attendance_list = frappe.get_all(
			"Attendance", {"employee": self.employee, "attendance_request": self.name, "docstatus": 1}
		)
		if attendance_list:
			for attendance in attendance_list:
				attendance_obj = frappe.get_doc("Attendance", attendance["name"])
				attendance_obj.cancel()

	def create_attendance_records(self):
		request_days = date_diff(self.to_date, self.from_date) + 1
		for day in range(request_days):
			attendance_date = add_days(self.from_date, day)
			if self.should_mark_attendance(attendance_date):
				self.create_or_update_attendance(attendance_date)

	def create_or_update_attendance(self, date: str):
		attendance_name = self.get_attendance_record(date)

		if self.half_day and date_diff(getdate(self.half_day_date), getdate(date)) == 0:
			status = "Half Day"
		elif self.reason == "Work From Home":
			status = "Work From Home"
		else:
			status = "Present"

		if attendance_name:
			# update existing attendance, change the status
			doc = frappe.get_doc("Attendance", attendance_name)
			if doc.status != status:
				text = _("Status updated from {0} to {1} via Attendance Request").format(
					frappe.bold(doc.status), frappe.bold(status)
				)

				doc.db_set({"status": status, "attendance_request": self.name})
				doc.add_comment(text=text)
		else:
			# submit a new attendance record
			doc = frappe.new_doc("Attendance")
			doc.employee = self.employee
			doc.attendance_date = date
			doc.company = self.company
			doc.attendance_request = self.name
			doc.status = status
			doc.insert(ignore_permissions=True)
			doc.submit()

	def should_mark_attendance(self, attendance_date: str) -> bool:
		# Check if attendance_date is a holiday
		if is_holiday(self.employee, attendance_date):
			frappe.msgprint(
				_("Attendance not submitted for {0} as it is a Holiday.").format(
					frappe.bold(format_date(attendance_date))
				)
			)
			return False

		# Check if employee is on leave
		if self.has_leave_record(attendance_date):
			frappe.msgprint(
				_("Attendance not submitted for {0} as {1} is on leave.").format(
					frappe.bold(format_date(attendance_date)), frappe.bold(self.employee)
				)
			)
			return False

		return True

	def has_leave_record(self, attendance_date: str) -> str | None:
		return frappe.db.exists(
			"Leave Application",
			{
				"employee": self.employee,
				"docstatus": 1,
				"from_date": ("<=", attendance_date),
				"to_date": (">=", attendance_date),
			},
		)

	def get_attendance_record(self, attendance_date: str) -> str | None:
		return frappe.db.exists(
			"Attendance",
			{
				"employee": self.employee,
				"attendance_date": attendance_date,
				"docstatus": 1,
			},
		)

	@frappe.whitelist()
	def get_attendance_warnings(self) -> list:
		attendance_warnings = []
		request_days = date_diff(self.to_date, self.from_date) + 1

		for day in range(request_days):
			attendance_date = add_days(self.from_date, day)

			if is_holiday(self.employee, attendance_date):
				attendance_warnings.append({"date": attendance_date, "reason": "Holiday", "action": "Skip"})
			elif self.has_leave_record(attendance_date):
				attendance_warnings.append({"date": attendance_date, "reason": "On Leave", "action": "Skip"})
			else:
				attendance = self.get_attendance_record(attendance_date)
				if attendance:
					attendance_warnings.append(
						{
							"date": attendance_date,
							"reason": "Attendance already marked",
							"record": attendance,
							"action": "Overwrite",
						}
					)

		return attendance_warnings
