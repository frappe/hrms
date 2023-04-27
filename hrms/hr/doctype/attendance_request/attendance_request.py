# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, getdate

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
		attendance_list = frappe.get_list(
			"Attendance", {"employee": self.employee, "attendance_request": self.name, "docstatus": 1}
		)
		if attendance_list:
			for attendance in attendance_list:
				attendance_obj = frappe.get_doc("Attendance", attendance["name"])
				attendance_obj.cancel()

	def create_attendance_records(self):
		request_days = date_diff(self.to_date, self.from_date) + 1
		for number in range(request_days):
			attendance_date = add_days(self.from_date, number)
			if self.validate_if_attendance_not_applicable(attendance_date):
				continue

			self.create_or_update_attendance(attendance_date)

	def create_or_update_attendance(self, date):
		attendance_name = frappe.db.exists(
			"Attendance", dict(employee=self.employee, attendance_date=date, docstatus=("!=", 2))
		)

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
				text = _("updated status from {0} to {1} via Attendance Request").format(
					frappe.bold(doc.status), frappe.bold(status)
				)

				doc.db_set({"status": status, "attendance_request": self.name})
				doc.add_comment(comment_type="Info", text=text)
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

	def validate_if_attendance_not_applicable(self, attendance_date):
		# Check if attendance_date is a Holiday
		if is_holiday(self.employee, attendance_date):
			frappe.msgprint(
				_("Attendance not submitted for {0} as it is a Holiday.").format(attendance_date), alert=1
			)
			return True

		# Check if employee on Leave
		leave_record = frappe.db.sql(
			"""select half_day from `tabLeave Application`
			where employee = %s and %s between from_date and to_date
			and docstatus = 1""",
			(self.employee, attendance_date),
			as_dict=True,
		)
		if leave_record:
			frappe.msgprint(
				_("Attendance not submitted for {0} as {1} on leave.").format(attendance_date, self.employee),
				alert=1,
			)
			return True

		return False
