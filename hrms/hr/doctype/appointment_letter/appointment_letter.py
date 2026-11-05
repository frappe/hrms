# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import calendar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, fmt_money, format_time, getdate, global_date_format, in_words
from frappe.utils.jinja import validate_template

from hrms.hr.doctype.appointment_letter_template.appointment_letter_template import (
	get_default_letter_body,
	get_default_template,
)


class AppointmentLetter(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		address: DF.SmallText | None
		applicant_email: DF.Data | None
		applicant_name: DF.Data
		appointment_date: DF.Date
		appointment_letter_print_format: DF.Link | None
		appointment_letter_template: DF.Link | None
		company: DF.Link
		employee: DF.Link | None
		end_time: DF.Time | None
		job_offer: DF.Link
		letter_body: DF.TextEditor | None
		letter_date: DF.Date | None
		letter_head: DF.Link | None
		retirement_age: DF.Int
		shift_type: DF.Link | None
		signature: DF.AttachImage | None
		start_time: DF.Time | None
	# end: auto-generated types

	def before_insert(self):
		if not self.retirement_age:
			self.retirement_age = cint(frappe.db.get_single_value("HR Settings", "retirement_age"))
		if not self.shift_type:
			self.set_shift_from_employee()
		if not self.letter_body:
			self.appointment_letter_template = self.appointment_letter_template or get_default_template()
			self.letter_body = self.get_template_body()

	def validate(self):
		validate_template(self.letter_body)

	def get_template_body(self) -> str:
		if self.appointment_letter_template:
			return frappe.db.get_value(
				"Appointment Letter Template", self.appointment_letter_template, "letter_body"
			)
		return get_default_letter_body()

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

	def get_letter_body_html(self) -> str:
		return frappe.render_template(self.letter_body or "", self.get_placeholders())

	def get_placeholders(self) -> dict:
		offer = frappe.get_cached_doc("Job Offer", self.job_offer) if self.job_offer else frappe._dict()
		return {
			"doc": self,
			"offer": offer,
			"applicant_name": self.applicant_name,
			"company": self.company,
			"employee": self.employee,
			"designation": offer.designation,
			"department": get_title("Department", offer.department, "department_name"),
			"reports_to": get_title("Employee", offer.reports_to, "employee_name"),
			"employment_type": offer.employment_type,
			"grade": offer.grade,
			"appointment_date": format_date(self.appointment_date),
			"letter_date": format_date(self.letter_date),
			"offer_date": format_date(offer.offer_date),
			"place_of_posting": offer.branch,
			"probation": format_probation(offer.probation_period_days),
			"notice_period": format_days(offer.notice_number_of_days),
			"notice_period_during_probation": format_days(offer.notice_period_during_probation),
			"ctc": fmt_money(offer.ctc, currency=offer.currency) if offer.ctc else "",
			"variable": fmt_money(offer.variable, currency=offer.currency) if offer.variable else "",
			"working_days": get_working_days(offer.weekly_off_days),
			"weekly_off": join_and(split_days(offer.weekly_off_days)),
			"start_time": format_time(self.start_time, "h:mm a") if self.start_time else "",
			"end_time": format_time(self.end_time, "h:mm a") if self.end_time else "",
			"working_hours": format_number(offer.working_hours),
			"public_holidays": offer.total_public_holidays,
			"leave_entitlement": join_and(
				[
					_("{0} days of {1}").format(format_number(row.annual_allocation), row.leave_type)
					for row in offer.get("leave_allocations") or []
				]
			),
			"retirement_age": self.retirement_age or "",
		}


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


def get_title(doctype: str, name: str | None, title_field: str) -> str | None:
	return frappe.get_cached_value(doctype, name, title_field) if name else None


def format_date(date) -> str:
	return global_date_format(date, "long") if date else ""


def format_number(value) -> str:
	return f"{flt(value):g}" if value else ""


def format_days(days: int | None) -> str:
	if not days:
		return ""
	return _("{0} ({1}) days").format(in_words(days), days) if days > 1 else _("one (1) day")


def format_probation(days: int | None) -> str:
	if not days or days % 30:
		return format_days(days)
	months = days // 30
	return _("{0} ({1}) months").format(in_words(months), months) if months > 1 else _("one (1) month")


def split_days(days: str | None) -> list[str]:
	return [day.strip() for day in (days or "").split(",") if day.strip()]


def get_working_days(weekly_off_days: str | None) -> str:
	off_days = split_days(weekly_off_days)
	if not off_days:
		return ""
	week = list(calendar.day_name)
	working_days = [day for day in week if day not in off_days]
	positions = [week.index(day) for day in working_days]
	if len(working_days) > 2 and positions == list(range(positions[0], positions[-1] + 1)):
		return _("{0} to {1}").format(_(working_days[0]), _(working_days[-1]))
	return join_and([_(day) for day in working_days])


def join_and(items: list[str]) -> str:
	if len(items) < 2:
		return "".join(items)
	return _("{0} and {1}").format(", ".join(items[:-1]), items[-1])
