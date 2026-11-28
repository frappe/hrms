# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.model.document import Document
from frappe.utils import cint, get_link_to_form, getdate


class PayrollSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		consider_marked_attendance_on_holidays: DF.Check
		consider_unmarked_attendance_as: DF.Literal["Present", "Absent"]
		create_overtime_slip: DF.Check
		daily_wages_fraction_for_half_day: DF.Float
		disable_rounded_total: DF.Check
		email_salary_slip_to_employee: DF.Check
		email_template: DF.Link | None
		encrypt_salary_slips_in_emails: DF.Check
		exclude_only_weekly_offs_from_working_days: DF.Check
		include_holidays_in_total_working_days: DF.Check
		mandatory_benefit_application: DF.Check
		max_working_hours_against_timesheet: DF.Float
		password_policy: DF.Data | None
		payroll_based_on: DF.Literal["Leave", "Attendance"]
		process_payroll_accounting_entry_based_on_employee: DF.Check
		sender: DF.Link | None
		sender_copy: DF.Link | None
		sender_email: DF.Data | None
		show_leave_balances_in_salary_slip: DF.Check
	# end: auto-generated types

	def validate(self):
		self.validate_password_policy()

		if not self.daily_wages_fraction_for_half_day:
			self.daily_wages_fraction_for_half_day = 0.5

		self.warn_about_holiday_lists_without_weekly_offs()

	def warn_about_holiday_lists_without_weekly_offs(self):
		if self.include_holidays_in_total_working_days or not self.exclude_only_weekly_offs_from_working_days:
			return

		if not self.has_value_changed("exclude_only_weekly_offs_from_working_days"):
			return

		holiday_lists = get_current_holiday_lists_without_weekly_offs()
		if not holiday_lists:
			return

		frappe.msgprint(
			_(
				"These holiday lists have no holidays marked as Weekly Off, so no days will be removed from the total no. of working days of employees who use them: {0}. Mark their weekly holidays as Weekly Off, or add them with the Add to Holidays button."
			).format(", ".join(get_link_to_form("Holiday List", name) for name in holiday_lists)),
			title=_("Holiday Lists Without Weekly Offs"),
			indicator="orange",
		)

	def validate_password_policy(self):
		if self.email_salary_slip_to_employee and self.encrypt_salary_slips_in_emails:
			if not self.password_policy:
				frappe.throw(_("Password policy for Salary Slips is not set"))

	def on_update(self):
		self.toggle_rounded_total()
		frappe.clear_cache()

	def toggle_rounded_total(self):
		disable_rounded_total = cint(self.disable_rounded_total)
		make_property_setter(
			"Salary Slip",
			"rounded_total",
			"hidden",
			disable_rounded_total,
			"Check",
			validate_fields_for_doctype=False,
		)
		make_property_setter(
			"Salary Slip",
			"rounded_total",
			"print_hide",
			disable_rounded_total,
			"Check",
			validate_fields_for_doctype=False,
		)


def get_current_holiday_lists_without_weekly_offs() -> list[str]:
	HolidayList = frappe.qb.DocType("Holiday List")
	Holiday = frappe.qb.DocType("Holiday")
	lists_with_weekly_offs = frappe.qb.from_(Holiday).select(Holiday.parent).where(Holiday.weekly_off == 1)

	return (
		frappe.qb.from_(HolidayList)
		.select(HolidayList.name)
		.where((HolidayList.to_date >= getdate()) & HolidayList.name.notin(lists_with_weekly_offs))
		.orderby(HolidayList.name)
		.run(pluck=True)
	)
