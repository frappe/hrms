# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.query_builder.functions import Count
from frappe.utils import add_days, cint, date_diff, flt, formatdate, get_link_to_form, getdate

from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

from hrms.payroll.doctype.salary_slip.salary_slip_utils import verify_lwp_days_corrected
from hrms.payroll.utils import HOLIDAYS_BETWEEN_DATES
from hrms.utils.holiday_list import get_holiday_dates_between


class PaymentDaysMixin:
	def get_working_days_details(self, lwp=None, for_preview=0, lwp_days_corrected=None):
		for fieldname, value in self.compute_payment_days(lwp, for_preview, lwp_days_corrected).items():
			self.set(fieldname, value)

	def compute_payment_days(self, lwp=None, for_preview=0, lwp_days_corrected=None) -> frappe._dict:
		"""Day counts for this slip's period, returned rather than written, so a caller
		can ask what the period looks like without changing the slip.

		Only the counts this period actually determines are returned: a preview settles
		nothing about leave, and absences are only known when payroll runs on attendance.
		"""
		payroll_settings = frappe.get_cached_value(
			"Payroll Settings",
			None,
			(
				"payroll_based_on",
				"include_holidays_in_total_working_days",
				"consider_marked_attendance_on_holidays",
				"daily_wages_fraction_for_half_day",
				"consider_unmarked_attendance_as",
			),
			as_dict=1,
		)

		consider_marked_attendance_on_holidays = (
			payroll_settings.include_holidays_in_total_working_days
			and payroll_settings.consider_marked_attendance_on_holidays
		)

		daily_wages_fraction_for_half_day = flt(payroll_settings.daily_wages_fraction_for_half_day) or 0.5

		working_days = date_diff(self.end_date, self.start_date) + 1
		if for_preview:
			return frappe._dict(total_working_days=working_days, payment_days=working_days)

		holidays = self.get_holidays_for_employee(self.start_date, self.end_date)
		working_days_list = [add_days(getdate(self.start_date), days=day) for day in range(0, working_days)]

		if not cint(payroll_settings.include_holidays_in_total_working_days):
			working_days_list = [i for i in working_days_list if i not in holidays]

			working_days -= len(holidays)
			if working_days < 0:
				frappe.throw(_("There are more holidays than working days this month."))

		if not payroll_settings.payroll_based_on:
			frappe.throw(_("Please set Payroll based on in Payroll settings"))

		based_on_attendance = payroll_settings.payroll_based_on == "Attendance"
		absent_days = None

		if based_on_attendance:
			actual_lwp, absent_days = self.calculate_lwp_ppl_and_absent_days_based_on_attendance(
				holidays, daily_wages_fraction_for_half_day, consider_marked_attendance_on_holidays
			)
		else:
			actual_lwp = self.calculate_lwp_or_ppl_based_on_leave_application(
				holidays, working_days_list, daily_wages_fraction_for_half_day
			)

		if not lwp:
			lwp = actual_lwp
		elif lwp != actual_lwp:
			frappe.msgprint(
				_("Leave Without Pay does not match with approved {} records").format(
					payroll_settings.payroll_based_on
				)
			)

		payable_days = self.get_payment_days(payroll_settings.include_holidays_in_total_working_days)

		if flt(payable_days) > flt(lwp):
			payment_days = flt(payable_days) - flt(lwp)

			if based_on_attendance:
				payment_days -= flt(absent_days)

				consider_unmarked_attendance_as = (
					payroll_settings.consider_unmarked_attendance_as or "Present"
				)
				if consider_unmarked_attendance_as == "Absent":
					unmarked_days = self.get_unmarked_days(
						payroll_settings.include_holidays_in_total_working_days, working_days, holidays
					)
					absent_days += unmarked_days  # will be treated as absent
					payment_days -= unmarked_days

				half_absent_days = self.get_half_absent_days(
					consider_marked_attendance_on_holidays,
					holidays,
				)
				absent_days += half_absent_days * daily_wages_fraction_for_half_day
				payment_days -= half_absent_days * daily_wages_fraction_for_half_day
		else:
			payment_days = 0

		if lwp_days_corrected and lwp_days_corrected > 0:
			if verify_lwp_days_corrected(self.employee, self.start_date, self.end_date, lwp_days_corrected):
				payment_days += lwp_days_corrected

		days = frappe._dict(
			total_working_days=working_days,
			payment_days=payment_days,
			leave_without_pay=lwp,
		)
		if absent_days is not None:
			days.absent_days = absent_days

		return days

	def get_unmarked_days(
		self,
		include_holidays_in_total_working_days: bool,
		total_working_days: float,
		holidays: list | None = None,
	) -> float:
		"""Calculates the number of unmarked days for an employee within a date range"""
		unmarked_days = (
			total_working_days
			- self._get_days_outside_period(include_holidays_in_total_working_days, holidays)
			- self._get_marked_attendance_days(holidays)
		)

		if include_holidays_in_total_working_days and holidays:
			unmarked_days -= self._get_number_of_holidays(holidays)

		return unmarked_days

	def get_half_absent_days(self, consider_marked_attendance_on_holidays, holidays):
		"""Calculates the number of half absent days for an employee within a date range"""
		Attendance = frappe.qb.DocType("Attendance")
		query = (
			frappe.qb.from_(Attendance)
			.select(Count("*"))
			.where(
				(Attendance.attendance_date.between(self.actual_start_date, self.actual_end_date))
				& (Attendance.employee == self.employee)
				& (Attendance.docstatus == 1)
				& (Attendance.status == "Half Day")
				& (Attendance.half_day_status == "Absent")
			)
		)
		if (not consider_marked_attendance_on_holidays) and holidays:
			query = query.where(Attendance.attendance_date.notin(holidays))
		return query.run()[0][0]

	def _get_days_outside_period(
		self, include_holidays_in_total_working_days: bool, holidays: list | None = None
	):
		"""Returns days before DOJ or after relieving date"""

		def _get_days(start_date, end_date):
			no_of_days = date_diff(end_date, start_date) + 1

			if include_holidays_in_total_working_days:
				return no_of_days
			else:
				days = 0
				end_date = getdate(end_date)
				for day in range(no_of_days):
					date = add_days(end_date, -day)
					if date not in holidays:
						days += 1
				return days

		days = 0
		if self.actual_start_date != self.start_date:
			days += _get_days(self.start_date, add_days(self.joining_date, -1))

		if self.actual_end_date != self.end_date:
			days += _get_days(add_days(self.relieving_date, 1), self.end_date)

		return days

	def _get_number_of_holidays(self, holidays: list | None = None) -> float:
		no_of_holidays = 0
		actual_end_date = getdate(self.actual_end_date)

		for days in range(date_diff(self.actual_end_date, self.actual_start_date) + 1):
			date = add_days(actual_end_date, -days)
			if date in holidays:
				no_of_holidays += 1

		return no_of_holidays

	def _get_marked_attendance_days(self, holidays: list | None = None) -> float:
		Attendance = frappe.qb.DocType("Attendance")
		query = (
			frappe.qb.from_(Attendance)
			.select(Count("*"))
			.where(
				(Attendance.attendance_date.between(self.actual_start_date, self.actual_end_date))
				& (Attendance.employee == self.employee)
				& (Attendance.docstatus == 1)
			)
		)
		if holidays:
			query = query.where(Attendance.attendance_date.notin(holidays))

		return query.run()[0][0]

	def get_payment_days(self, include_holidays_in_total_working_days):
		if self.joining_date and self.joining_date > getdate(self.end_date):
			# employee joined after payroll date
			return 0

		if self.relieving_date:
			employee_status = frappe.db.get_value("Employee", self.employee, "status")
			if self.relieving_date < getdate(self.start_date) and employee_status != "Left":
				frappe.throw(
					_("Employee {0} relieved on {1} must be set as 'Left'").format(
						get_link_to_form("Employee", self.employee), formatdate(self.relieving_date)
					)
				)

		payment_days = date_diff(self.actual_end_date, self.actual_start_date) + 1

		if not cint(include_holidays_in_total_working_days):
			holidays = self.get_holidays_for_employee(self.actual_start_date, self.actual_end_date)
			payment_days -= len(holidays)

		return payment_days

	def get_holidays_for_employee(self, start_date, end_date):
		holiday_list = get_holiday_list_for_employee(self.employee)
		key = f"{holiday_list}:{start_date}:{end_date}"
		holiday_dates = frappe.cache().hget(HOLIDAYS_BETWEEN_DATES, key)

		if not holiday_dates:
			holiday_dates = get_holiday_dates_between(holiday_list, start_date, end_date)
			frappe.cache().hset(HOLIDAYS_BETWEEN_DATES, key, holiday_dates)

		return holiday_dates
