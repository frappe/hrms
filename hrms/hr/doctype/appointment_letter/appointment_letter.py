# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document
from frappe.utils import cint, getdate


class AppointmentLetter(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.appointment_letter_content.appointment_letter_content import (
			AppointmentLettercontent,
		)

		address: DF.SmallText | None
		applicant_email: DF.Data | None
		applicant_name: DF.Data
		appointment_date: DF.Date
		appointment_letter_preview: DF.HTML | None
		appointment_letter_print_format: DF.Link | None
		appointment_letter_template: DF.Link | None
		company: DF.Link
		employee: DF.Link | None
		end_time: DF.Time | None
		introduction: DF.LongText | None
		job_offer: DF.Link
		job_responsibilities: DF.TextEditor | None
		letter_date: DF.Date | None
		letter_head: DF.Link | None
		retirement_age: DF.Int
		shift_type: DF.Link | None
		signature: DF.AttachImage | None
		start_time: DF.Time | None
		terms: DF.Table[AppointmentLettercontent]
	# end: auto-generated types

	def before_insert(self):
		if not self.retirement_age:
			self.retirement_age = cint(frappe.db.get_single_value("HR Settings", "retirement_age"))
		if not self.shift_type:
			self.set_shift_from_employee()

	@frappe.whitelist()
	def set_shift_from_employee(self):
		if not self.employee:
			return
		shift_type = get_shift_type_on(self.employee, getdate(self.appointment_date))
		if shift_type:
			self.shift_type = shift_type
			self.start_time, self.end_time = frappe.get_cached_value(
				"Shift Type", shift_type, ["start_time", "end_time"]
			)


def get_shift_type_on(employee: str, date) -> str | None:
	assignment = frappe.get_all(
		"Shift Assignment",
		filters={"employee": employee, "docstatus": 1, "status": "Active", "start_date": ("<=", date)},
		or_filters=[["end_date", "is", "not set"], ["end_date", ">=", date]],
		pluck="shift_type",
		order_by="start_date desc",
		limit=1,
	)
	return assignment[0] if assignment else frappe.db.get_value("Employee", employee, "default_shift")


@frappe.whitelist()
def get_appointment_letter_details(template: str) -> list:
	body = []
	intro = frappe.get_list(
		"Appointment Letter Template",
		fields=["introduction"],
		filters={"name": template},
	)[0]
	content = frappe.get_all(
		"Appointment Letter content",
		fields=["title", "description"],
		filters={"parent": template},
		order_by="idx",
	)
	body.append(intro)
	body.append({"description": content})
	return body
