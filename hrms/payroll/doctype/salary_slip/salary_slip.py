# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import unicodedata
from datetime import date

import frappe
from frappe import _, msgprint
from frappe.model.naming import make_autoname
from frappe.query_builder import Order
from frappe.query_builder.functions import Sum
from frappe.utils import (
	add_days,
	ceil,
	cint,
	cstr,
	date_diff,
	floor,
	flt,
	formatdate,
	get_first_day,
	get_link_to_form,
	getdate,
	money_in_words,
	rounded,
)
from frappe.utils.background_jobs import enqueue

import erpnext
from erpnext.accounts.utils import get_fiscal_year
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from erpnext.utilities.transaction_base import TransactionBase

from hrms.hr.utils import validate_active_employee
from hrms.payroll.doctype.additional_salary.additional_salary import get_additional_salaries
from hrms.payroll.doctype.employee_benefit_application.employee_benefit_application import (
	get_benefit_component_amount,
)
from hrms.payroll.doctype.employee_benefit_claim.employee_benefit_claim import (
	get_benefit_claim_amount,
	get_last_payroll_period_benefits,
)
from hrms.payroll.doctype.payroll_entry.payroll_entry import get_start_end_dates
from hrms.payroll.doctype.payroll_period.payroll_period import (
	get_payroll_period,
	get_period_factor,
)
from hrms.payroll.doctype.salary_slip.salary_slip_loan_utils import (
	cancel_loan_repayment_entry,
	make_loan_repayment_entry,
	set_loan_repayment,
)
from hrms.payroll.utils import sanitize_expression
from hrms.utils.holiday_list import get_holiday_dates_between

# cache keys
HOLIDAYS_BETWEEN_DATES = "holidays_between_dates"
LEAVE_TYPE_MAP = "leave_type_map"
SALARY_COMPONENT_VALUES = "salary_component_values"
TAX_COMPONENTS_BY_COMPANY = "tax_components_by_company"


class SalarySlip(TransactionBase):
	def __init__(self, *args, **kwargs):
		super(SalarySlip, self).__init__(*args, **kwargs)
		self.series = "Sal Slip/{0}/.#####".format(self.employee)
		self.whitelisted_globals = {
			"int": int,
			"float": float,
			"long": int,
			"round": round,
			"date": date,
			"getdate": getdate,
			"ceil": ceil,
			"floor": floor,
		}

	def autoname(self):
		self.name = make_autoname(self.series)

	@property
	def joining_date(self):
		if not hasattr(self, "__joining_date"):
			self.__joining_date = frappe.get_cached_value(
				"Employee",
				self.employee,
				"date_of_joining",
			)

		return self.__joining_date

	@property
	def relieving_date(self):
		if not hasattr(self, "__relieving_date"):
			self.__relieving_date = frappe.get_cached_value(
				"Employee",
				self.employee,
				"relieving_date",
			)

		return self.__relieving_date

	@property
	def payroll_period(self):
		if not hasattr(self, "__payroll_period"):
			self.__payroll_period = get_payroll_period(self.start_date, self.end_date, self.company)

		return self.__payroll_period

	@property
	def actual_start_date(self):
		if not hasattr(self, "__actual_start_date"):
			self.__actual_start_date = self.start_date

			if self.joining_date and getdate(self.start_date) < self.joining_date <= getdate(self.end_date):
				self.__actual_start_date = self.joining_date

		return self.__actual_start_date

	@property
	def actual_end_date(self):
		if not hasattr(self, "__actual_end_date"):
			self.__actual_end_date = self.end_date

			if self.relieving_date and getdate(self.start_date) <= self.relieving_date < getdate(
				self.end_date
			):
				self.__actual_end_date = self.relieving_date

		return self.__actual_end_date

	def validate(self):
		self.status = self.get_status()
		validate_active_employee(self.employee)
		self.validate_dates()
		self.check_existing()

		if not self.salary_slip_based_on_timesheet:
			self.get_date_details()

		if not (len(self.get("earnings")) or len(self.get("deductions"))):
			# get details from salary structure
			self.get_emp_and_working_day_details()
		else:
			self.get_working_days_details(lwp=self.leave_without_pay)

		self.set_salary_structure_assignement()
		self.calculate_net_pay()
		self.compute_year_to_date()
		self.compute_month_to_date()
		self.compute_component_wise_year_to_date()

		self.add_leave_balances()

		max_working_hours = frappe.db.get_single_value(
			"Payroll Settings", "max_working_hours_against_timesheet"
		)
		if max_working_hours:
			if self.salary_slip_based_on_timesheet and (self.total_working_hours > int(max_working_hours)):
				frappe.msgprint(
					_("Total working hours should not be greater than max working hours {0}").format(
						max_working_hours
					),
					alert=True,
				)

	def set_net_total_in_words(self):
		doc_currency = self.currency
		company_currency = erpnext.get_company_currency(self.company)
		total = self.net_pay if self.is_rounding_total_disabled() else self.rounded_total
		base_total = self.base_net_pay if self.is_rounding_total_disabled() else self.base_rounded_total
		self.total_in_words = money_in_words(total, doc_currency)
		self.base_total_in_words = money_in_words(base_total, company_currency)

	def on_update(self):
		self.publish_update()

	def on_submit(self):
		if self.net_pay < 0:
			frappe.throw(_("Net Pay cannot be less than 0"))
		else:
			self.set_status()
			self.update_status(self.name)

			make_loan_repayment_entry(self)

			if not frappe.flags.via_payroll_entry and not frappe.flags.in_patch:
				email_salary_slip = cint(
					frappe.db.get_single_value("Payroll Settings", "email_salary_slip_to_employee")
				)
				if email_salary_slip:
					self.email_salary_slip()

		self.update_payment_status_for_gratuity()

	def update_payment_status_for_gratuity(self):
		additional_salary = frappe.db.get_all(
			"Additional Salary",
			filters={
				"payroll_date": ("between", [self.start_date, self.end_date]),
				"employee": self.employee,
				"ref_doctype": "Gratuity",
				"docstatus": 1,
			},
			fields=["ref_docname", "name"],
			limit=1,
		)

		if additional_salary:
			status = "Paid" if self.docstatus == 1 else "Unpaid"
			if additional_salary[0].name in [entry.additional_salary for entry in self.earnings]:
				frappe.db.set_value("Gratuity", additional_salary[0].ref_docname, "status", status)

	def on_cancel(self):
		self.set_status()
		self.update_status()
		self.update_payment_status_for_gratuity()

		cancel_loan_repayment_entry(self)
		self.publish_update()

	def publish_update(self):
		employee_user = frappe.db.get_value("Employee", self.employee, "user_id", cache=True)
		if frappe.session.user == employee_user:
			frappe.publish_realtime(
				event="hrms:update_salary_slips",
				message={"employee": self.employee},
				user=frappe.session.user,
				after_commit=True,
			)

	def on_trash(self):
		from frappe.model.naming import revert_series_if_last

		revert_series_if_last(self.series, self.name)

	def get_status(self):
		if self.docstatus == 0:
			status = "Draft"
		elif self.docstatus == 1:
			status = "Submitted"
		elif self.docstatus == 2:
			status = "Cancelled"
		return status

	def validate_dates(self):
		self.validate_from_to_dates("start_date", "end_date")

		if not self.joining_date:
			frappe.throw(
				_("Please set the Date Of Joining for employee {0}").format(frappe.bold(self.employee_name))
			)

		if date_diff(self.end_date, self.joining_date) < 0:
			frappe.throw(_("Cannot create Salary Slip for Employee joining after Payroll Period"))

		if self.relieving_date and date_diff(self.relieving_date, self.start_date) < 0:
			frappe.throw(_("Cannot create Salary Slip for Employee who has left before Payroll Period"))

	def is_rounding_total_disabled(self):
		return cint(frappe.db.get_single_value("Payroll Settings", "disable_rounded_total"))

	def check_existing(self):
		if not self.salary_slip_based_on_timesheet:
			ss = frappe.qb.DocType("Salary Slip")
			query = (
				frappe.qb.from_(ss)
				.select(ss.name)
				.where(
					(ss.start_date == self.start_date)
					& (ss.end_date == self.end_date)
					& (ss.docstatus != 2)
					& (ss.employee == self.employee)
					& (ss.name != self.name)
				)
			)

			if self.payroll_entry:
				query = query.where(ss.payroll_entry == self.payroll_entry)

			ret_exist = query.run()

			if ret_exist:
				frappe.throw(
					_("Salary Slip of employee {0} already created for this period").format(self.employee)
				)
		else:
			for data in self.timesheets:
				if frappe.db.get_value("Timesheet", data.time_sheet, "status") == "Payrolled":
					frappe.throw(
						_("Salary Slip of employee {0} already created for time sheet {1}").format(
							self.employee, data.time_sheet
						)
					)

	def get_date_details(self):
		if not self.end_date:
			date_details = get_start_end_dates(self.payroll_frequency, self.start_date or self.posting_date)
			self.start_date = date_details.start_date
			self.end_date = date_details.end_date

	@frappe.whitelist()
	def get_emp_and_working_day_details(self):
		"""First time, load all the components from salary structure"""
		if self.employee:
			self.set("earnings", [])
			self.set("deductions", [])

			if not self.salary_slip_based_on_timesheet:
				self.get_date_details()

			self.validate_dates()

			# getin leave details
			self.get_working_days_details()
			struct = self.check_sal_struct()

			if struct:
				self._salary_structure_doc = frappe.get_cached_doc("Salary Structure", struct)
				self.salary_slip_based_on_timesheet = (
					self._salary_structure_doc.salary_slip_based_on_timesheet or 0
				)
				self.set_time_sheet()
				self.pull_sal_struct()

	def set_time_sheet(self):
		if self.salary_slip_based_on_timesheet:
			self.set("timesheets", [])

			Timesheet = frappe.qb.DocType("Timesheet")
			timesheets = (
				frappe.qb.from_(Timesheet)
				.select(Timesheet.star)
				.where(
					(Timesheet.employee == self.employee)
					& (Timesheet.start_date.between(self.start_date, self.end_date))
					& ((Timesheet.status == "Submitted") | (Timesheet.status == "Billed"))
				)
			).run(as_dict=1)

			for data in timesheets:
				self.append("timesheets", {"time_sheet": data.name, "working_hours": data.total_hours})

	def check_sal_struct(self):
		ss = frappe.qb.DocType("Salary Structure")
		ssa = frappe.qb.DocType("Salary Structure Assignment")

		query = (
			frappe.qb.from_(ssa)
			.join(ss)
			.on(ssa.salary_structure == ss.name)
			.select(ssa.salary_structure)
			.where(
				(ssa.docstatus == 1)
				& (ss.docstatus == 1)
				& (ss.is_active == "Yes")
				& (ssa.employee == self.employee)
				& (
					(ssa.from_date <= self.start_date)
					| (ssa.from_date <= self.end_date)
					| (ssa.from_date <= self.joining_date)
				)
			)
			.orderby(ssa.from_date, order=Order.desc)
			.limit(1)
		)

		if not self.salary_slip_based_on_timesheet and self.payroll_frequency:
			query = query.where(ss.payroll_frequency == self.payroll_frequency)

		st_name = query.run()

		if st_name:
			self.salary_structure = st_name[0][0]
			return self.salary_structure

		else:
			self.salary_structure = None
			frappe.msgprint(
				_("No active or default Salary Structure found for employee {0} for the given dates").format(
					self.employee
				),
				title=_("Salary Structure Missing"),
			)

	def pull_sal_struct(self):
		from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

		if self.salary_slip_based_on_timesheet:
			self.salary_structure = self._salary_structure_doc.name
			self.hour_rate = self._salary_structure_doc.hour_rate
			self.base_hour_rate = flt(self.hour_rate) * flt(self.exchange_rate)
			self.total_working_hours = sum([d.working_hours or 0.0 for d in self.timesheets]) or 0.0
			wages_amount = self.hour_rate * self.total_working_hours

			self.add_earning_for_hourly_wages(
				self, self._salary_structure_doc.salary_component, wages_amount
			)

		make_salary_slip(self._salary_structure_doc.name, self)

	def get_working_days_details(self, lwp=None, for_preview=0):
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

		daily_wages_fraction_for_half_day = (
			flt(payroll_settings.daily_wages_fraction_for_half_day) or 0.5
		)

		working_days = date_diff(self.end_date, self.start_date) + 1
		if for_preview:
			self.total_working_days = working_days
			self.payment_days = working_days
			return

		holidays = self.get_holidays_for_employee(self.start_date, self.end_date)
		working_days_list = [
			add_days(getdate(self.start_date), days=day) for day in range(0, working_days)
		]

		if not cint(payroll_settings.include_holidays_in_total_working_days):
			working_days_list = [i for i in working_days_list if i not in holidays]

			working_days -= len(holidays)
			if working_days < 0:
				frappe.throw(_("There are more holidays than working days this month."))

		if not payroll_settings.payroll_based_on:
			frappe.throw(_("Please set Payroll based on in Payroll settings"))

		if payroll_settings.payroll_based_on == "Attendance":
			actual_lwp, absent = self.calculate_lwp_ppl_and_absent_days_based_on_attendance(
				holidays, daily_wages_fraction_for_half_day, consider_marked_attendance_on_holidays
			)
			self.absent_days = absent
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

		self.leave_without_pay = lwp
		self.total_working_days = working_days

		payment_days = self.get_payment_days(payroll_settings.include_holidays_in_total_working_days)

		if flt(payment_days) > flt(lwp):
			self.payment_days = flt(payment_days) - flt(lwp)

			if payroll_settings.payroll_based_on == "Attendance":
				self.payment_days -= flt(absent)

			consider_unmarked_attendance_as = payroll_settings.consider_unmarked_attendance_as or "Present"

			if (
				payroll_settings.payroll_based_on == "Attendance"
				and consider_unmarked_attendance_as == "Absent"
			):
				unmarked_days = self.get_unmarked_days(payroll_settings.include_holidays_in_total_working_days)
				self.absent_days += unmarked_days  # will be treated as absent
				self.payment_days -= unmarked_days
		else:
			self.payment_days = 0

	def get_unmarked_days(self, include_holidays_in_total_working_days):
		unmarked_days = self.total_working_days

		if self.actual_start_date != self.start_date:
			unmarked_days = self.get_unmarked_days_based_on_doj_or_relieving(
				unmarked_days,
				include_holidays_in_total_working_days,
				self.start_date,
				add_days(self.joining_date, -1),
			)

		if self.actual_end_date != self.end_date:
			unmarked_days = self.get_unmarked_days_based_on_doj_or_relieving(
				unmarked_days,
				include_holidays_in_total_working_days,
				add_days(self.relieving_date, 1),
				self.end_date,
			)

		# exclude days for which attendance has been marked
		marked_days = frappe.db.count(
			"Attendance",
			filters={
				"attendance_date": ["between", [self.actual_start_date, self.actual_end_date]],
				"employee": self.employee,
				"docstatus": 1,
			},
		)
		unmarked_days -= marked_days

		return unmarked_days

	def get_unmarked_days_based_on_doj_or_relieving(
		self, unmarked_days, include_holidays_in_total_working_days, start_date, end_date
	):
		"""
		Exclude days before DOJ or after
		Relieving Date from unmarked days
		"""
		from erpnext.setup.doctype.employee.employee import is_holiday

		if include_holidays_in_total_working_days:
			unmarked_days -= date_diff(end_date, start_date) + 1
		else:
			# exclude only if not holidays
			for days in range(date_diff(end_date, start_date) + 1):
				date = add_days(end_date, -days)
				if not is_holiday(self.employee, date):
					unmarked_days -= 1

		return unmarked_days

	def get_payment_days(self, include_holidays_in_total_working_days):
		if self.joining_date and self.joining_date > getdate(self.end_date):
			# employee joined after payroll date
			return 0

		if self.relieving_date:
			employee_status = frappe.db.get_value("Employee", self.employee, "status")
			if self.relieving_date < getdate(self.start_date) and employee_status != "Left":
				frappe.throw(_("Employee relieved on {0} must be set as 'Left'").format(self.relieving_date))

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

	def calculate_lwp_or_ppl_based_on_leave_application(
		self, holidays, working_days_list, daily_wages_fraction_for_half_day
	):
		lwp = 0
		leaves = get_lwp_or_ppl_for_date_range(
			self.employee,
			self.start_date,
			self.end_date,
		)

		for d in working_days_list:
			if self.relieving_date and d > self.relieving_date:
				continue

			leave = leaves.get(d)

			if not leave:
				continue

			if not leave.include_holidays and getdate(d) in holidays:
				continue

			equivalent_lwp_count = 0
			fraction_of_daily_salary_per_leave = flt(leave.fraction_of_daily_salary_per_leave)

			is_half_day_leave = False
			if cint(leave.half_day) and (leave.half_day_date == d or leave.from_date == leave.to_date):
				is_half_day_leave = True

			equivalent_lwp_count = (1 - daily_wages_fraction_for_half_day) if is_half_day_leave else 1

			if is_partially_paid_leave := cint(leave.is_ppl):
				equivalent_lwp_count *= (
					fraction_of_daily_salary_per_leave if fraction_of_daily_salary_per_leave else 1
				)

			lwp += equivalent_lwp_count

		return lwp

	def get_leave_type_map(self) -> dict:
		"""Returns (partially paid leaves/leave without pay) leave types by name"""

		def _get_leave_type_map():
			leave_types = frappe.get_all(
				"Leave Type",
				or_filters={"is_ppl": 1, "is_lwp": 1},
				fields=["name", "is_lwp", "is_ppl", "fraction_of_daily_salary_per_leave", "include_holiday"],
			)
			return {leave_type.name: leave_type for leave_type in leave_types}

		return frappe.cache().get_value(LEAVE_TYPE_MAP, _get_leave_type_map)

	def get_employee_attendance(self, start_date, end_date):
		attendance = frappe.qb.DocType("Attendance")

		attendance_details = (
			frappe.qb.from_(attendance)
			.select(attendance.attendance_date, attendance.status, attendance.leave_type)
			.where(
				(attendance.status.isin(["Absent", "Half Day", "On Leave"]))
				& (attendance.employee == self.employee)
				& (attendance.docstatus == 1)
				& (attendance.attendance_date.between(start_date, end_date))
			)
		).run(as_dict=1)

		return attendance_details

	def calculate_lwp_ppl_and_absent_days_based_on_attendance(
		self, holidays, daily_wages_fraction_for_half_day, consider_marked_attendance_on_holidays
	):
		lwp = 0
		absent = 0

		leave_type_map = self.get_leave_type_map()
		attendance_details = self.get_employee_attendance(
			start_date=self.start_date, end_date=self.actual_end_date
		)

		for d in attendance_details:
			if (
				d.status in ("Half Day", "On Leave")
				and d.leave_type
				and d.leave_type not in leave_type_map.keys()
			):
				continue

			# skip counting absent on holidays
			if not consider_marked_attendance_on_holidays and getdate(d.attendance_date) in holidays:
				if d.status == "Absent" or (
					d.leave_type
					and d.leave_type in leave_type_map.keys()
					and not leave_type_map[d.leave_type]["include_holiday"]
				):
					continue

			if d.leave_type:
				fraction_of_daily_salary_per_leave = leave_type_map[d.leave_type][
					"fraction_of_daily_salary_per_leave"
				]

			if d.status == "Half Day":
				equivalent_lwp = 1 - daily_wages_fraction_for_half_day

				if d.leave_type in leave_type_map.keys() and leave_type_map[d.leave_type]["is_ppl"]:
					equivalent_lwp *= (
						fraction_of_daily_salary_per_leave if fraction_of_daily_salary_per_leave else 1
					)
				lwp += equivalent_lwp

			elif d.status == "On Leave" and d.leave_type and d.leave_type in leave_type_map.keys():
				equivalent_lwp = 1
				if leave_type_map[d.leave_type]["is_ppl"]:
					equivalent_lwp *= (
						fraction_of_daily_salary_per_leave if fraction_of_daily_salary_per_leave else 1
					)
				lwp += equivalent_lwp

			elif d.status == "Absent":
				absent += 1

		return lwp, absent

	def add_earning_for_hourly_wages(self, doc, salary_component, amount):
		row_exists = False
		for row in doc.earnings:
			if row.salary_component == salary_component:
				row.amount = amount
				row_exists = True
				break

		if not row_exists:
			wages_row = {
				"salary_component": salary_component,
				"abbr": frappe.db.get_value(
					"Salary Component", salary_component, "salary_component_abbr", cache=True
				),
				"amount": self.hour_rate * self.total_working_hours,
				"default_amount": 0.0,
				"additional_amount": 0.0,
			}
			doc.append("earnings", wages_row)

	def set_salary_structure_assignement(self):
		self._salary_structure_assignment = frappe.db.get_value(
			"Salary Structure Assignment",
			{
				"employee": self.employee,
				"salary_structure": self.salary_structure,
				"from_date": ("<=", self.actual_start_date),
				"docstatus": 1,
			},
			"*",
			order_by="from_date desc",
			as_dict=True,
		)

		if not self._salary_structure_assignment:
			frappe.throw(
				_(
					"Please assign a Salary Structure for Employee {0} applicable from or before {1} first"
				).format(
					frappe.bold(self.employee_name),
					frappe.bold(formatdate(self.actual_start_date)),
				)
			)

	def calculate_net_pay(self):
		if self.salary_structure:
			self.calculate_component_amounts("earnings")

		# get remaining numbers of sub-period (period for which one salary is processed)
		if self.payroll_period:
			self.remaining_sub_periods = get_period_factor(
				self.employee,
				self.start_date,
				self.end_date,
				self.payroll_frequency,
				self.payroll_period,
				joining_date=self.joining_date,
				relieving_date=self.relieving_date,
			)[1]

		self.gross_pay = self.get_component_totals("earnings", depends_on_payment_days=1)
		self.base_gross_pay = flt(
			flt(self.gross_pay) * flt(self.exchange_rate), self.precision("base_gross_pay")
		)

		if self.salary_structure:
			self.calculate_component_amounts("deductions")

		set_loan_repayment(self)

		self.set_precision_for_component_amounts()
		self.set_net_pay()
		self.compute_income_tax_breakup()

	def set_net_pay(self):
		self.total_deduction = self.get_component_totals("deductions")
		self.base_total_deduction = flt(
			flt(self.total_deduction) * flt(self.exchange_rate), self.precision("base_total_deduction")
		)
		self.net_pay = flt(self.gross_pay) - (
			flt(self.total_deduction) + flt(self.get("total_loan_repayment"))
		)
		self.rounded_total = rounded(self.net_pay)
		self.base_net_pay = flt(
			flt(self.net_pay) * flt(self.exchange_rate), self.precision("base_net_pay")
		)
		self.base_rounded_total = flt(rounded(self.base_net_pay), self.precision("base_net_pay"))
		if self.hour_rate:
			self.base_hour_rate = flt(
				flt(self.hour_rate) * flt(self.exchange_rate), self.precision("base_hour_rate")
			)
		self.set_net_total_in_words()

	def compute_taxable_earnings_for_year(self):
		# get taxable_earnings, opening_taxable_earning, paid_taxes for previous period
		self.previous_taxable_earnings, exempted_amount = self.get_taxable_earnings_for_prev_period(
			self.payroll_period.start_date, self.start_date, self.tax_slab.allow_tax_exemption
		)

		self.previous_taxable_earnings_before_exemption = (
			self.previous_taxable_earnings + exempted_amount
		)

		self.compute_current_and_future_taxable_earnings()

		# Deduct taxes forcefully for unsubmitted tax exemption proof and unclaimed benefits in the last period
		if self.payroll_period.end_date <= getdate(self.end_date):
			self.deduct_tax_for_unsubmitted_tax_exemption_proof = 1
			self.deduct_tax_for_unclaimed_employee_benefits = 1

		# Get taxable unclaimed benefits
		self.unclaimed_taxable_benefits = 0
		if self.deduct_tax_for_unclaimed_employee_benefits:
			self.unclaimed_taxable_benefits = self.calculate_unclaimed_taxable_benefits()

		# Total exemption amount based on tax exemption declaration
		self.total_exemption_amount = self.get_total_exemption_amount()

		# Employee Other Incomes
		self.other_incomes = self.get_income_form_other_sources() or 0.0

		# Total taxable earnings including additional and other incomes
		self.total_taxable_earnings = (
			self.previous_taxable_earnings
			+ self.current_structured_taxable_earnings
			+ self.future_structured_taxable_earnings
			+ self.current_additional_earnings
			+ self.other_incomes
			+ self.unclaimed_taxable_benefits
			- self.total_exemption_amount
		)

		# Total taxable earnings without additional earnings with full tax
		self.total_taxable_earnings_without_full_tax_addl_components = (
			self.total_taxable_earnings - self.current_additional_earnings_with_full_tax
		)

	def compute_current_and_future_taxable_earnings(self):
		# get taxable_earnings for current period (all days)
		self.current_taxable_earnings = self.get_taxable_earnings(self.tax_slab.allow_tax_exemption)
		self.future_structured_taxable_earnings = self.current_taxable_earnings.taxable_earnings * (
			ceil(self.remaining_sub_periods) - 1
		)

		current_taxable_earnings_before_exemption = (
			self.current_taxable_earnings.taxable_earnings
			+ self.current_taxable_earnings.amount_exempted_from_income_tax
		)
		self.future_structured_taxable_earnings_before_exemption = (
			current_taxable_earnings_before_exemption * (ceil(self.remaining_sub_periods) - 1)
		)

		# get taxable_earnings, addition_earnings for current actual payment days
		self.current_taxable_earnings_for_payment_days = self.get_taxable_earnings(
			self.tax_slab.allow_tax_exemption, based_on_payment_days=1
		)

		self.current_structured_taxable_earnings = (
			self.current_taxable_earnings_for_payment_days.taxable_earnings
		)
		self.current_structured_taxable_earnings_before_exemption = (
			self.current_structured_taxable_earnings
			+ self.current_taxable_earnings_for_payment_days.amount_exempted_from_income_tax
		)

		self.current_additional_earnings = (
			self.current_taxable_earnings_for_payment_days.additional_income
		)

		self.current_additional_earnings_with_full_tax = (
			self.current_taxable_earnings_for_payment_days.additional_income_with_full_tax
		)

	def compute_income_tax_breakup(self):
		if not self.payroll_period:
			return

		self.standard_tax_exemption_amount = 0
		self.tax_exemption_declaration = 0
		self.deductions_before_tax_calculation = 0

		self.non_taxable_earnings = self.compute_non_taxable_earnings()

		self.ctc = self.compute_ctc()

		self.income_from_other_sources = self.get_income_form_other_sources()

		self.total_earnings = self.ctc + self.income_from_other_sources

		if hasattr(self, "tax_slab"):
			if self.tax_slab.allow_tax_exemption:
				self.standard_tax_exemption_amount = self.tax_slab.standard_tax_exemption_amount
				self.deductions_before_tax_calculation = (
					self.compute_annual_deductions_before_tax_calculation()
				)

			self.tax_exemption_declaration = (
				self.get_total_exemption_amount() - self.standard_tax_exemption_amount
			)

		self.annual_taxable_amount = self.total_earnings - (
			self.non_taxable_earnings
			+ self.deductions_before_tax_calculation
			+ self.tax_exemption_declaration
			+ self.standard_tax_exemption_amount
		)

		self.income_tax_deducted_till_date = self.get_income_tax_deducted_till_date()

		if hasattr(self, "total_structured_tax_amount") and hasattr(
			self, "current_structured_tax_amount"
		):
			self.future_income_tax_deductions = (
				self.total_structured_tax_amount - self.income_tax_deducted_till_date
			)

			self.current_month_income_tax = self.current_structured_tax_amount

			# non included current_month_income_tax separately as its already considered
			# while calculating income_tax_deducted_till_date

			self.total_income_tax = self.income_tax_deducted_till_date + self.future_income_tax_deductions

	def compute_ctc(self):
		if hasattr(self, "previous_taxable_earnings"):

			return (
				self.previous_taxable_earnings_before_exemption
				+ self.current_structured_taxable_earnings_before_exemption
				+ self.future_structured_taxable_earnings_before_exemption
				+ self.current_additional_earnings
				+ self.other_incomes
				+ self.unclaimed_taxable_benefits
				+ self.non_taxable_earnings
			)

		return 0.0

	def compute_non_taxable_earnings(self):
		# Previous period non taxable earnings
		prev_period_non_taxable_earnings = self.get_salary_slip_details(
			self.payroll_period.start_date, self.start_date, parentfield="earnings", is_tax_applicable=0
		)

		(
			current_period_non_taxable_earnings,
			non_taxable_additional_salary,
		) = self.get_non_taxable_earnings_for_current_period()

		# Future period non taxable earnings
		future_period_non_taxable_earnings = current_period_non_taxable_earnings * (
			ceil(self.remaining_sub_periods) - 1
		)

		non_taxable_earnings = (
			prev_period_non_taxable_earnings
			+ current_period_non_taxable_earnings
			+ future_period_non_taxable_earnings
			+ non_taxable_additional_salary
		)

		return non_taxable_earnings

	def get_non_taxable_earnings_for_current_period(self):
		current_period_non_taxable_earnings = 0.0

		non_taxable_additional_salary = self.get_salary_slip_details(
			self.payroll_period.start_date,
			self.start_date,
			parentfield="earnings",
			is_tax_applicable=0,
			field_to_select="additional_amount",
		)

		# Current period non taxable earnings
		for earning in self.earnings:
			if earning.is_tax_applicable:
				continue

			if earning.additional_amount:
				non_taxable_additional_salary += earning.additional_amount

				# Future recurring additional salary
				if earning.additional_salary and earning.is_recurring_additional_salary:
					non_taxable_additional_salary += self.get_future_recurring_additional_amount(
						earning.additional_salary, earning.additional_amount
					)
			else:
				current_period_non_taxable_earnings += earning.amount

		return current_period_non_taxable_earnings, non_taxable_additional_salary

	def compute_annual_deductions_before_tax_calculation(self):
		prev_period_exempted_amount = 0
		current_period_exempted_amount = 0
		future_period_exempted_amount = 0

		# Previous period exempted amount
		prev_period_exempted_amount = self.get_salary_slip_details(
			self.payroll_period.start_date,
			self.start_date,
			parentfield="deductions",
			exempted_from_income_tax=1,
		)

		# Current period exempted amount
		for d in self.get("deductions"):
			if d.exempted_from_income_tax:
				current_period_exempted_amount += d.amount

		# Future period exempted amount
		for deduction in self._salary_structure_doc.get("deductions"):
			if deduction.exempted_from_income_tax:
				if deduction.amount_based_on_formula:
					for sub_period in range(1, ceil(self.remaining_sub_periods)):
						future_period_exempted_amount += self.get_amount_from_formula(deduction, sub_period)
				else:
					future_period_exempted_amount += deduction.amount * (ceil(self.remaining_sub_periods) - 1)

		return (
			prev_period_exempted_amount + current_period_exempted_amount + future_period_exempted_amount
		) or 0

	def get_amount_from_formula(self, struct_row, sub_period=1):
		if self.payroll_frequency == "Monthly":
			start_date = frappe.utils.add_months(self.start_date, sub_period)
			end_date = frappe.utils.add_months(self.end_date, sub_period)
			posting_date = frappe.utils.add_months(self.posting_date, sub_period)

		else:
			if self.payroll_frequency == "Weekly":
				days_to_add = sub_period * 6

			if self.payroll_frequency == "Fortnightly":
				days_to_add = sub_period * 13

			if self.payroll_frequency == "Daily":
				days_to_add = start_date

			start_date = frappe.utils.add_days(self.start_date, days_to_add)
			end_date = frappe.utils.add_days(self.end_date, days_to_add)
			posting_date = start_date

		local_data = self.data.copy()
		local_data.update({"start_date": start_date, "end_date": end_date, "posting_date": posting_date})

		return flt(self.eval_condition_and_formula(struct_row, local_data))

	def get_income_tax_deducted_till_date(self):
		tax_deducted = 0.0
		for tax_component in self.get("_component_based_variable_tax") or {}:
			tax_deducted += (
				self._component_based_variable_tax[tax_component]["previous_total_paid_taxes"]
				+ self._component_based_variable_tax[tax_component]["current_tax_amount"]
			)
		return tax_deducted

	def calculate_component_amounts(self, component_type):
		if not getattr(self, "_salary_structure_doc", None):
			self._salary_structure_doc = frappe.get_cached_doc("Salary Structure", self.salary_structure)

		self.add_structure_components(component_type)
		self.add_additional_salary_components(component_type)
		if component_type == "earnings":
			self.add_employee_benefits()
		else:
			self.add_tax_components()

	def add_structure_components(self, component_type):
		self.data, self.default_data = self.get_data_for_eval()
		timesheet_component = self._salary_structure_doc.salary_component

		for struct_row in self._salary_structure_doc.get(component_type):
			if self.salary_slip_based_on_timesheet and struct_row.salary_component == timesheet_component:
				continue

			amount = self.eval_condition_and_formula(struct_row, self.data)
			if struct_row.statistical_component:
				# update statitical component amount in reference data based on payment days
				# since row for statistical component is not added to salary slip

				self.default_data[struct_row.abbr] = flt(amount)
				if struct_row.depends_on_payment_days:
					payment_days_amount = (
						flt(amount) * flt(self.payment_days) / cint(self.total_working_days)
						if self.total_working_days
						else 0
					)
					self.data[struct_row.abbr] = flt(payment_days_amount, struct_row.precision("amount"))

			else:
				# default behavior, the system does not add if component amount is zero
				# if remove_if_zero_valued is unchecked, then ask system to add component row
				remove_if_zero_valued = frappe.get_cached_value(
					"Salary Component", struct_row.salary_component, "remove_if_zero_valued"
				)

				default_amount = 0

				if (
					amount
					or (struct_row.amount_based_on_formula and amount is not None)
					or (not remove_if_zero_valued and amount is not None and not self.data[struct_row.abbr])
				):
					default_amount = self.eval_condition_and_formula(struct_row, self.default_data)
					self.update_component_row(
						struct_row,
						amount,
						component_type,
						data=self.data,
						default_amount=default_amount,
						remove_if_zero_valued=remove_if_zero_valued,
					)

	def get_data_for_eval(self):
		"""Returns data for evaluating formula"""
		data = frappe._dict()
		employee = frappe.get_cached_doc("Employee", self.employee).as_dict()

		if not hasattr(self, "_salary_structure_assignment"):
			self.set_salary_structure_assignement()

		data.update(self._salary_structure_assignment)
		data.update(employee)
		data.update(self.as_dict())

		data.update(self.get_component_abbr_map())

		# shallow copy of data to store default amounts (without payment days) for tax calculation
		default_data = data.copy()

		for key in ("earnings", "deductions"):
			for d in self.get(key):
				default_data[d.abbr] = d.default_amount or 0
				data[d.abbr] = d.amount or 0

		return data, default_data

	def get_component_abbr_map(self):
		def _fetch_component_values():
			return {
				component_abbr: 0
				for component_abbr in frappe.get_all("Salary Component", pluck="salary_component_abbr")
			}

		return frappe.cache().get_value(SALARY_COMPONENT_VALUES, generator=_fetch_component_values)

	def eval_condition_and_formula(self, struct_row, data):
		try:
			condition = sanitize_expression(struct_row.condition)
			if condition:
				if not _safe_eval(condition, self.whitelisted_globals, data):
					return None
			amount = struct_row.amount
			if struct_row.amount_based_on_formula:
				formula = sanitize_expression(struct_row.formula)
				if formula:
					amount = flt(
						_safe_eval(formula, self.whitelisted_globals, data), struct_row.precision("amount")
					)
			if amount:
				data[struct_row.abbr] = amount

			return amount

		except NameError as ne:
			throw_error_message(
				struct_row,
				ne,
				title=_("Name error"),
				description=_("This error can be due to missing or deleted field."),
			)
		except SyntaxError as se:
			throw_error_message(
				struct_row,
				se,
				title=_("Syntax error"),
				description=_("This error can be due to invalid syntax."),
			)
		except Exception as exc:
			throw_error_message(
				struct_row,
				exc,
				title=_("Error in formula or condition"),
				description=_("This error can be due to invalid formula or condition."),
			)
			raise

	def add_employee_benefits(self):
		for struct_row in self._salary_structure_doc.get("earnings"):
			if struct_row.is_flexible_benefit == 1:
				if (
					frappe.db.get_value(
						"Salary Component", struct_row.salary_component, "pay_against_benefit_claim", cache=True
					)
					!= 1
				):
					benefit_component_amount = get_benefit_component_amount(
						self.employee,
						self.start_date,
						self.end_date,
						struct_row.salary_component,
						self._salary_structure_doc,
						self.payroll_frequency,
						self.payroll_period,
					)
					if benefit_component_amount:
						self.update_component_row(struct_row, benefit_component_amount, "earnings")
				else:
					benefit_claim_amount = get_benefit_claim_amount(
						self.employee, self.start_date, self.end_date, struct_row.salary_component
					)
					if benefit_claim_amount:
						self.update_component_row(struct_row, benefit_claim_amount, "earnings")

		self.adjust_benefits_in_last_payroll_period(self.payroll_period)

	def adjust_benefits_in_last_payroll_period(self, payroll_period):
		if payroll_period:
			if getdate(payroll_period.end_date) <= getdate(self.end_date):
				last_benefits = get_last_payroll_period_benefits(
					self.employee, self.start_date, self.end_date, payroll_period, self._salary_structure_doc
				)
				if last_benefits:
					for last_benefit in last_benefits:
						last_benefit = frappe._dict(last_benefit)
						amount = last_benefit.amount
						self.update_component_row(frappe._dict(last_benefit.struct_row), amount, "earnings")

	def add_additional_salary_components(self, component_type):
		additional_salaries = get_additional_salaries(
			self.employee, self.start_date, self.end_date, component_type
		)

		for additional_salary in additional_salaries:
			self.update_component_row(
				get_salary_component_data(additional_salary.component),
				additional_salary.amount,
				component_type,
				additional_salary,
				is_recurring=additional_salary.is_recurring,
			)

	def add_tax_components(self):
		# Calculate variable_based_on_taxable_salary after all components updated in salary slip
		tax_components, self.other_deduction_components = [], []
		for d in self._salary_structure_doc.get("deductions"):
			if d.variable_based_on_taxable_salary == 1 and not d.formula and not flt(d.amount):
				tax_components.append(d.salary_component)
			else:
				self.other_deduction_components.append(d.salary_component)

		# consider manually added tax component
		if not tax_components:
			tax_components = [
				d.salary_component for d in self.get("deductions") if d.variable_based_on_taxable_salary
			]

		if self.is_new() and not tax_components:
			tax_components = self.get_tax_components()
			frappe.msgprint(
				_(
					"Added tax components from the Salary Component master as the salary structure didn't have any tax component."
				),
				indicator="blue",
				alert=True,
			)

		if tax_components and self.payroll_period and self.salary_structure:
			self.tax_slab = self.get_income_tax_slabs()
			self.compute_taxable_earnings_for_year()

		self._component_based_variable_tax = {}
		for d in tax_components:
			self._component_based_variable_tax.setdefault(d, {})
			tax_amount = self.calculate_variable_based_on_taxable_salary(d)
			tax_row = get_salary_component_data(d)
			self.update_component_row(tax_row, tax_amount, "deductions")

	def get_tax_components(self) -> list:
		"""
		Returns:
		        list: A list of tax components specific to the company.
		        If no tax components are defined for the company,
		        it returns the default tax components.
		"""
		tax_components = frappe.cache().get_value(
			TAX_COMPONENTS_BY_COMPANY, self._fetch_tax_components_by_company
		)

		default_tax_components = tax_components.get("default", [])
		return tax_components.get(self.company, default_tax_components)

	def _fetch_tax_components_by_company(self) -> dict:
		"""
		Returns:
		    dict: A dictionary containing tax components grouped by company.

		Raises:
		    None
		"""

		tax_components = {}
		sc = frappe.qb.DocType("Salary Component")
		sca = frappe.qb.DocType("Salary Component Account")

		components = (
			frappe.qb.from_(sc)
			.left_join(sca)
			.on(sca.parent == sc.name)
			.select(
				sc.name,
				sca.company,
			)
			.where(sc.variable_based_on_taxable_salary == 1)
		).run(as_dict=True)

		for component in components:
			key = component.company or "default"
			tax_components.setdefault(key, [])
			tax_components[key].append(component.name)

		return tax_components

	def update_component_row(
		self,
		component_data,
		amount,
		component_type,
		additional_salary=None,
		is_recurring=0,
		data=None,
		default_amount=None,
		remove_if_zero_valued=None,
	):
		component_row = None
		for d in self.get(component_type):
			if d.salary_component != component_data.salary_component:
				continue

			if (not d.additional_salary and (not additional_salary or additional_salary.overwrite)) or (
				additional_salary and additional_salary.name == d.additional_salary
			):
				component_row = d
				break

		if additional_salary and additional_salary.overwrite:
			# Additional Salary with overwrite checked, remove default rows of same component
			self.set(
				component_type,
				[
					d
					for d in self.get(component_type)
					if d.salary_component != component_data.salary_component
					or (d.additional_salary and additional_salary.name != d.additional_salary)
					or d == component_row
				],
			)

		if not component_row:
			if not (amount or default_amount) and remove_if_zero_valued:
				return

			component_row = self.append(component_type)
			for attr in (
				"depends_on_payment_days",
				"salary_component",
				"abbr",
				"do_not_include_in_total",
				"is_tax_applicable",
				"is_flexible_benefit",
				"variable_based_on_taxable_salary",
				"exempted_from_income_tax",
			):
				component_row.set(attr, component_data.get(attr))

		if additional_salary:
			if additional_salary.overwrite:
				component_row.additional_amount = flt(
					flt(amount) - flt(component_row.get("default_amount", 0)),
					component_row.precision("additional_amount"),
				)
			else:
				component_row.default_amount = 0
				component_row.additional_amount = amount

			component_row.is_recurring_additional_salary = is_recurring
			component_row.additional_salary = additional_salary.name
			component_row.deduct_full_tax_on_selected_payroll_date = (
				additional_salary.deduct_full_tax_on_selected_payroll_date
			)
		else:
			component_row.default_amount = default_amount or amount
			component_row.additional_amount = 0
			component_row.deduct_full_tax_on_selected_payroll_date = (
				component_data.deduct_full_tax_on_selected_payroll_date
			)

		component_row.amount = amount

		self.update_component_amount_based_on_payment_days(component_row, remove_if_zero_valued)

		if data:
			data[component_row.abbr] = component_row.amount

	def update_component_amount_based_on_payment_days(
		self, component_row, remove_if_zero_valued=None
	):
		component_row.amount = self.get_amount_based_on_payment_days(component_row)[0]

		# remove 0 valued components that have been updated later
		if component_row.amount == 0 and remove_if_zero_valued:
			self.remove(component_row)

	def set_precision_for_component_amounts(self):
		for component_type in ("earnings", "deductions"):
			for component_row in self.get(component_type):
				component_row.amount = flt(component_row.amount, component_row.precision("amount"))

	def calculate_variable_based_on_taxable_salary(self, tax_component):
		if not self.payroll_period:
			frappe.msgprint(
				_("Start and end dates not in a valid Payroll Period, cannot calculate {0}.").format(
					tax_component
				)
			)
			return

		return self.calculate_variable_tax(tax_component)

	def calculate_variable_tax(self, tax_component):
		self.previous_total_paid_taxes = self.get_tax_paid_in_period(
			self.payroll_period.start_date, self.start_date, tax_component
		)

		# Structured tax amount
		eval_locals, default_data = self.get_data_for_eval()
		self.total_structured_tax_amount = calculate_tax_by_tax_slab(
			self.total_taxable_earnings_without_full_tax_addl_components,
			self.tax_slab,
			self.whitelisted_globals,
			eval_locals,
		)

		self.current_structured_tax_amount = (
			self.total_structured_tax_amount - self.previous_total_paid_taxes
		) / self.remaining_sub_periods

		# Total taxable earnings with additional earnings with full tax
		self.full_tax_on_additional_earnings = 0.0
		if self.current_additional_earnings_with_full_tax:
			self.total_tax_amount = calculate_tax_by_tax_slab(
				self.total_taxable_earnings, self.tax_slab, self.whitelisted_globals, eval_locals
			)
			self.full_tax_on_additional_earnings = self.total_tax_amount - self.total_structured_tax_amount

		current_tax_amount = self.current_structured_tax_amount + self.full_tax_on_additional_earnings
		if flt(current_tax_amount) < 0:
			current_tax_amount = 0

		self._component_based_variable_tax[tax_component].update(
			{
				"previous_total_paid_taxes": self.previous_total_paid_taxes,
				"total_structured_tax_amount": self.total_structured_tax_amount,
				"current_structured_tax_amount": self.current_structured_tax_amount,
				"full_tax_on_additional_earnings": self.full_tax_on_additional_earnings,
				"current_tax_amount": current_tax_amount,
			}
		)

		return current_tax_amount

	def get_income_tax_slabs(self):
		income_tax_slab = self._salary_structure_assignment.income_tax_slab

		if not income_tax_slab:
			frappe.throw(
				_("Income Tax Slab not set in Salary Structure Assignment: {0}").format(
					self._salary_structure_assignment
				)
			)

		income_tax_slab_doc = frappe.get_cached_doc("Income Tax Slab", income_tax_slab)
		if income_tax_slab_doc.disabled:
			frappe.throw(_("Income Tax Slab: {0} is disabled").format(income_tax_slab))

		if getdate(income_tax_slab_doc.effective_from) > getdate(self.payroll_period.start_date):
			frappe.throw(
				_("Income Tax Slab must be effective on or before Payroll Period Start Date: {0}").format(
					self.payroll_period.start_date
				)
			)

		return income_tax_slab_doc

	def get_taxable_earnings_for_prev_period(self, start_date, end_date, allow_tax_exemption=False):
		exempted_amount = 0
		taxable_earnings = self.get_salary_slip_details(
			start_date, end_date, parentfield="earnings", is_tax_applicable=1
		)

		if allow_tax_exemption:
			exempted_amount = self.get_salary_slip_details(
				start_date, end_date, parentfield="deductions", exempted_from_income_tax=1
			)

		opening_taxable_earning = self.get_opening_for(
			"taxable_earnings_till_date", start_date, end_date
		)

		return (taxable_earnings + opening_taxable_earning) - exempted_amount, exempted_amount

	def get_opening_for(self, field_to_select, start_date, end_date):
		return self._salary_structure_assignment.get(field_to_select) or 0

	def get_salary_slip_details(
		self,
		start_date,
		end_date,
		parentfield,
		salary_component=None,
		is_tax_applicable=None,
		is_flexible_benefit=0,
		exempted_from_income_tax=0,
		variable_based_on_taxable_salary=0,
		field_to_select="amount",
	):
		ss = frappe.qb.DocType("Salary Slip")
		sd = frappe.qb.DocType("Salary Detail")

		if field_to_select == "amount":
			field = sd.amount
		else:
			field = sd.additional_amount

		query = (
			frappe.qb.from_(ss)
			.join(sd)
			.on(sd.parent == ss.name)
			.select(Sum(field))
			.where(sd.parentfield == parentfield)
			.where(sd.is_flexible_benefit == is_flexible_benefit)
			.where(ss.docstatus == 1)
			.where(ss.employee == self.employee)
			.where(ss.start_date.between(start_date, end_date))
			.where(ss.end_date.between(start_date, end_date))
		)

		if is_tax_applicable is not None:
			query = query.where(sd.is_tax_applicable == is_tax_applicable)

		if exempted_from_income_tax:
			query = query.where(sd.exempted_from_income_tax == exempted_from_income_tax)

		if variable_based_on_taxable_salary:
			query = query.where(sd.variable_based_on_taxable_salary == variable_based_on_taxable_salary)

		if salary_component:
			query = query.where(sd.salary_component == salary_component)

		result = query.run()

		return flt(result[0][0]) if result else 0.0

	def get_tax_paid_in_period(self, start_date, end_date, tax_component):
		# find total_tax_paid, tax paid for benefit, additional_salary
		total_tax_paid = self.get_salary_slip_details(
			start_date,
			end_date,
			parentfield="deductions",
			salary_component=tax_component,
			variable_based_on_taxable_salary=1,
		)

		tax_deducted_till_date = self.get_opening_for("tax_deducted_till_date", start_date, end_date)

		return total_tax_paid + tax_deducted_till_date

	def get_taxable_earnings(self, allow_tax_exemption=False, based_on_payment_days=0):
		taxable_earnings = 0
		additional_income = 0
		additional_income_with_full_tax = 0
		flexi_benefits = 0
		amount_exempted_from_income_tax = 0

		for earning in self.earnings:
			if based_on_payment_days:
				amount, additional_amount = self.get_amount_based_on_payment_days(earning)
			else:
				if earning.additional_amount:
					amount, additional_amount = earning.amount, earning.additional_amount
				else:
					amount, additional_amount = earning.default_amount, earning.additional_amount

			if earning.is_tax_applicable:
				if earning.is_flexible_benefit:
					flexi_benefits += amount
				else:
					taxable_earnings += amount - additional_amount
					additional_income += additional_amount

					# Get additional amount based on future recurring additional salary
					if additional_amount and earning.is_recurring_additional_salary:
						additional_income += self.get_future_recurring_additional_amount(
							earning.additional_salary, earning.additional_amount
						)  # Used earning.additional_amount to consider the amount for the full month

					if earning.deduct_full_tax_on_selected_payroll_date:
						additional_income_with_full_tax += additional_amount

		if allow_tax_exemption:
			for ded in self.deductions:
				if ded.exempted_from_income_tax:
					amount, additional_amount = ded.amount, ded.additional_amount
					if based_on_payment_days:
						amount, additional_amount = self.get_amount_based_on_payment_days(ded)

					taxable_earnings -= flt(amount - additional_amount)
					additional_income -= additional_amount
					amount_exempted_from_income_tax = flt(amount - additional_amount)

					if additional_amount and ded.is_recurring_additional_salary:
						additional_income -= self.get_future_recurring_additional_amount(
							ded.additional_salary, ded.additional_amount
						)  # Used ded.additional_amount to consider the amount for the full month

		return frappe._dict(
			{
				"taxable_earnings": taxable_earnings,
				"additional_income": additional_income,
				"amount_exempted_from_income_tax": amount_exempted_from_income_tax,
				"additional_income_with_full_tax": additional_income_with_full_tax,
				"flexi_benefits": flexi_benefits,
			}
		)

	def get_future_recurring_period(
		self,
		additional_salary,
	):
		to_date = None

		if self.relieving_date:
			to_date = self.relieving_date

		if not to_date:
			to_date = frappe.db.get_value("Additional Salary", additional_salary, "to_date", cache=True)

		# future month count excluding current
		from_date, to_date = getdate(self.start_date), getdate(to_date)

		# If recurring period end date is beyond the payroll period,
		# last day of payroll period should be considered for recurring period calculation
		if getdate(to_date) > getdate(self.payroll_period.end_date):
			to_date = getdate(self.payroll_period.end_date)

		future_recurring_period = ((to_date.year - from_date.year) * 12) + (
			to_date.month - from_date.month
		)

		return future_recurring_period

	def get_future_recurring_additional_amount(self, additional_salary, monthly_additional_amount):
		future_recurring_additional_amount = 0

		future_recurring_period = self.get_future_recurring_period(additional_salary)

		if future_recurring_period > 0:
			future_recurring_additional_amount = (
				monthly_additional_amount * future_recurring_period
			)  # Used earning.additional_amount to consider the amount for the full month
		return future_recurring_additional_amount

	def get_amount_based_on_payment_days(self, row):
		amount, additional_amount = row.amount, row.additional_amount
		timesheet_component = self._salary_structure_doc.salary_component

		if (
			self.salary_structure
			and cint(row.depends_on_payment_days)
			and cint(self.total_working_days)
			and not (
				row.additional_salary and row.default_amount
			)  # to identify overwritten additional salary
			and (
				row.salary_component != timesheet_component
				or getdate(self.start_date) < self.joining_date
				or (self.relieving_date and getdate(self.end_date) > self.relieving_date)
			)
		):
			additional_amount = flt(
				(flt(row.additional_amount) * flt(self.payment_days) / cint(self.total_working_days)),
				row.precision("additional_amount"),
			)
			amount = (
				flt(
					(flt(row.default_amount) * flt(self.payment_days) / cint(self.total_working_days)),
					row.precision("amount"),
				)
				+ additional_amount
			)

		elif (
			not self.payment_days
			and row.salary_component != timesheet_component
			and cint(row.depends_on_payment_days)
		):
			amount, additional_amount = 0, 0
		elif not row.amount:
			amount = flt(row.default_amount) + flt(row.additional_amount)

		# apply rounding
		if frappe.db.get_value(
			"Salary Component", row.salary_component, "round_to_the_nearest_integer", cache=True
		):
			amount, additional_amount = rounded(amount or 0), rounded(additional_amount or 0)

		return amount, additional_amount

	def calculate_unclaimed_taxable_benefits(self):
		# get total sum of benefits paid
		total_benefits_paid = self.get_salary_slip_details(
			self.payroll_period.start_date,
			self.start_date,
			parentfield="earnings",
			is_tax_applicable=1,
			is_flexible_benefit=1,
		)

		# get total benefits claimed
		BenefitClaim = frappe.qb.DocType("Employee Benefit Claim")
		total_benefits_claimed = (
			frappe.qb.from_(BenefitClaim)
			.select(Sum(BenefitClaim.claimed_amount))
			.where(
				(BenefitClaim.docstatus == 1)
				& (BenefitClaim.employee == self.employee)
				& (BenefitClaim.claim_date.between(self.payroll_period.start_date, self.end_date))
			)
		).run()
		total_benefits_claimed = flt(total_benefits_claimed[0][0]) if total_benefits_claimed else 0

		unclaimed_taxable_benefits = (
			total_benefits_paid - total_benefits_claimed
		) + self.current_taxable_earnings_for_payment_days.flexi_benefits
		return unclaimed_taxable_benefits

	def get_total_exemption_amount(self):
		total_exemption_amount = 0
		if self.tax_slab.allow_tax_exemption:
			if self.deduct_tax_for_unsubmitted_tax_exemption_proof:
				exemption_proof = frappe.db.get_value(
					"Employee Tax Exemption Proof Submission",
					{"employee": self.employee, "payroll_period": self.payroll_period.name, "docstatus": 1},
					"exemption_amount",
					cache=True,
				)
				if exemption_proof:
					total_exemption_amount = exemption_proof
			else:
				declaration = frappe.db.get_value(
					"Employee Tax Exemption Declaration",
					{"employee": self.employee, "payroll_period": self.payroll_period.name, "docstatus": 1},
					"total_exemption_amount",
					cache=True,
				)
				if declaration:
					total_exemption_amount = declaration

		if self.tax_slab.standard_tax_exemption_amount:
			total_exemption_amount += flt(self.tax_slab.standard_tax_exemption_amount)

		return total_exemption_amount

	def get_income_form_other_sources(self):
		return (
			frappe.get_all(
				"Employee Other Income",
				filters={
					"employee": self.employee,
					"payroll_period": self.payroll_period.name,
					"company": self.company,
					"docstatus": 1,
				},
				fields="SUM(amount) as total_amount",
			)[0].total_amount
			or 0.0
		)

	def get_component_totals(self, component_type, depends_on_payment_days=0):
		total = 0.0
		for d in self.get(component_type):
			if not d.do_not_include_in_total:
				if depends_on_payment_days:
					amount = self.get_amount_based_on_payment_days(d)[0]
				else:
					amount = flt(d.amount, d.precision("amount"))
				total += amount
		return total

	def email_salary_slip(self):
		receiver = frappe.db.get_value("Employee", self.employee, "prefered_email", cache=True)
		payroll_settings = frappe.get_single("Payroll Settings")
		message = "Please see attachment"
		password = None
		if payroll_settings.encrypt_salary_slips_in_emails:
			password = generate_password_for_pdf(payroll_settings.password_policy, self.employee)
			message += """<br>Note: Your salary slip is password protected,
				the password to unlock the PDF is of the format {0}. """.format(
				payroll_settings.password_policy
			)

		if receiver:
			email_args = {
				"sender": payroll_settings.sender_email,
				"recipients": [receiver],
				"message": _(message),
				"subject": "Salary Slip - from {0} to {1}".format(self.start_date, self.end_date),
				"attachments": [
					frappe.attach_print(self.doctype, self.name, file_name=self.name, password=password)
				],
				"reference_doctype": self.doctype,
				"reference_name": self.name,
			}
			if not frappe.flags.in_test:
				enqueue(method=frappe.sendmail, queue="short", timeout=300, is_async=True, **email_args)
			else:
				frappe.sendmail(**email_args)
		else:
			msgprint(_("{0}: Employee email not found, hence email not sent").format(self.employee_name))

	def update_status(self, salary_slip=None):
		for data in self.timesheets:
			if data.time_sheet:
				timesheet = frappe.get_doc("Timesheet", data.time_sheet)
				timesheet.salary_slip = salary_slip
				timesheet.flags.ignore_validate_update_after_submit = True
				timesheet.set_status()
				timesheet.save()

	def set_status(self, status=None):
		"""Get and update status"""
		if not status:
			status = self.get_status()
		self.db_set("status", status)

	def process_salary_structure(self, for_preview=0):
		"""Calculate salary after salary structure details have been updated"""
		if not self.salary_slip_based_on_timesheet:
			self.get_date_details()
		self.pull_emp_details()
		self.get_working_days_details(for_preview=for_preview)
		self.calculate_net_pay()

	def pull_emp_details(self):
		account_details = frappe.get_cached_value(
			"Employee", self.employee, ["bank_name", "bank_ac_no", "salary_mode"], as_dict=1
		)
		if account_details:
			self.mode_of_payment = account_details.salary_mode
			self.bank_name = account_details.bank_name
			self.bank_account_no = account_details.bank_ac_no

	@frappe.whitelist()
	def process_salary_based_on_working_days(self):
		self.get_working_days_details(lwp=self.leave_without_pay)
		self.calculate_net_pay()

	@frappe.whitelist()
	def set_totals(self):
		self.gross_pay = 0.0
		if self.salary_slip_based_on_timesheet == 1:
			self.calculate_total_for_salary_slip_based_on_timesheet()
		else:
			self.total_deduction = 0.0
			if hasattr(self, "earnings"):
				for earning in self.earnings:
					self.gross_pay += flt(earning.amount, earning.precision("amount"))
			if hasattr(self, "deductions"):
				for deduction in self.deductions:
					self.total_deduction += flt(deduction.amount, deduction.precision("amount"))
			self.net_pay = (
				flt(self.gross_pay) - flt(self.total_deduction) - flt(self.get("total_loan_repayment"))
			)
		self.set_base_totals()

	def set_base_totals(self):
		self.base_gross_pay = flt(self.gross_pay) * flt(self.exchange_rate)
		self.base_total_deduction = flt(self.total_deduction) * flt(self.exchange_rate)
		self.rounded_total = rounded(self.net_pay or 0)
		self.base_net_pay = flt(self.net_pay) * flt(self.exchange_rate)
		self.base_rounded_total = rounded(self.base_net_pay or 0)
		self.set_net_total_in_words()

	# calculate total working hours, earnings based on hourly wages and totals
	def calculate_total_for_salary_slip_based_on_timesheet(self):
		if self.timesheets:
			self.total_working_hours = 0
			for timesheet in self.timesheets:
				if timesheet.working_hours:
					self.total_working_hours += timesheet.working_hours

		wages_amount = self.total_working_hours * self.hour_rate
		self.base_hour_rate = flt(self.hour_rate) * flt(self.exchange_rate)
		salary_component = frappe.db.get_value(
			"Salary Structure", {"name": self.salary_structure}, "salary_component", cache=True
		)
		if self.earnings:
			for i, earning in enumerate(self.earnings):
				if earning.salary_component == salary_component:
					self.earnings[i].amount = wages_amount
				self.gross_pay += flt(self.earnings[i].amount, earning.precision("amount"))
		self.net_pay = flt(self.gross_pay) - flt(self.total_deduction)

	def compute_year_to_date(self):
		year_to_date = 0
		period_start_date, period_end_date = self.get_year_to_date_period()

		salary_slip_sum = frappe.get_list(
			"Salary Slip",
			fields=["sum(net_pay) as net_sum", "sum(gross_pay) as gross_sum"],
			filters={
				"employee": self.employee,
				"start_date": [">=", period_start_date],
				"end_date": ["<", period_end_date],
				"name": ["!=", self.name],
				"docstatus": 1,
			},
		)

		year_to_date = flt(salary_slip_sum[0].net_sum) if salary_slip_sum else 0.0
		gross_year_to_date = flt(salary_slip_sum[0].gross_sum) if salary_slip_sum else 0.0

		year_to_date += self.net_pay
		gross_year_to_date += self.gross_pay
		self.year_to_date = year_to_date
		self.gross_year_to_date = gross_year_to_date

	def compute_month_to_date(self):
		month_to_date = 0
		first_day_of_the_month = get_first_day(self.start_date)
		salary_slip_sum = frappe.get_list(
			"Salary Slip",
			fields=["sum(net_pay) as sum"],
			filters={
				"employee": self.employee,
				"start_date": [">=", first_day_of_the_month],
				"end_date": ["<", self.start_date],
				"name": ["!=", self.name],
				"docstatus": 1,
			},
		)

		month_to_date = flt(salary_slip_sum[0].sum) if salary_slip_sum else 0.0

		month_to_date += self.net_pay
		self.month_to_date = month_to_date

	def compute_component_wise_year_to_date(self):
		period_start_date, period_end_date = self.get_year_to_date_period()

		ss = frappe.qb.DocType("Salary Slip")
		sd = frappe.qb.DocType("Salary Detail")

		for key in ("earnings", "deductions"):
			for component in self.get(key):
				year_to_date = 0
				component_sum = (
					frappe.qb.from_(sd)
					.inner_join(ss)
					.on(sd.parent == ss.name)
					.select(Sum(sd.amount).as_("sum"))
					.where(
						(ss.employee == self.employee)
						& (sd.salary_component == component.salary_component)
						& (ss.start_date >= period_start_date)
						& (ss.end_date < period_end_date)
						& (ss.name != self.name)
						& (ss.docstatus == 1)
					)
				).run()

				year_to_date = flt(component_sum[0][0]) if component_sum else 0.0
				year_to_date += component.amount
				component.year_to_date = year_to_date

	def get_year_to_date_period(self):
		if self.payroll_period:
			period_start_date = self.payroll_period.start_date
			period_end_date = self.payroll_period.end_date
		else:
			# get dates based on fiscal year if no payroll period exists
			fiscal_year = get_fiscal_year(date=self.start_date, company=self.company, as_dict=1)
			period_start_date = fiscal_year.year_start_date
			period_end_date = fiscal_year.year_end_date

		return period_start_date, period_end_date

	def add_leave_balances(self):
		self.set("leave_details", [])

		if frappe.db.get_single_value("Payroll Settings", "show_leave_balances_in_salary_slip"):
			from hrms.hr.doctype.leave_application.leave_application import get_leave_details

			leave_details = get_leave_details(self.employee, self.end_date)

			for leave_type, leave_values in leave_details["leave_allocation"].items():
				self.append(
					"leave_details",
					{
						"leave_type": leave_type,
						"total_allocated_leaves": flt(leave_values.get("total_leaves")),
						"expired_leaves": flt(leave_values.get("expired_leaves")),
						"used_leaves": flt(leave_values.get("leaves_taken")),
						"pending_leaves": flt(leave_values.get("leaves_pending_approval")),
						"available_leaves": flt(leave_values.get("remaining_leaves")),
					},
				)


def unlink_ref_doc_from_salary_slip(doc, method=None):
	"""Unlinks accrual Journal Entry from Salary Slips on cancellation"""
	linked_ss = frappe.get_all(
		"Salary Slip", filters={"journal_entry": doc.name, "docstatus": ["<", 2]}, pluck="name"
	)

	if linked_ss:
		for ss in linked_ss:
			ss_doc = frappe.get_doc("Salary Slip", ss)
			frappe.db.set_value("Salary Slip", ss_doc.name, "journal_entry", "")


def generate_password_for_pdf(policy_template, employee):
	employee = frappe.get_cached_doc("Employee", employee)
	return policy_template.format(**employee.as_dict())


def get_salary_component_data(component):
	# get_cached_value doesn't work here due to alias "name as salary_component"
	return frappe.db.get_value(
		"Salary Component",
		component,
		(
			"name as salary_component",
			"depends_on_payment_days",
			"salary_component_abbr as abbr",
			"do_not_include_in_total",
			"is_tax_applicable",
			"is_flexible_benefit",
			"variable_based_on_taxable_salary",
		),
		as_dict=1,
		cache=True,
	)


def get_payroll_payable_account(company, payroll_entry):
	if payroll_entry:
		payroll_payable_account = frappe.db.get_value(
			"Payroll Entry", payroll_entry, "payroll_payable_account", cache=True
		)
	else:
		payroll_payable_account = frappe.db.get_value(
			"Company", company, "default_payroll_payable_account", cache=True
		)

	return payroll_payable_account


def calculate_tax_by_tax_slab(
	annual_taxable_earning, tax_slab, eval_globals=None, eval_locals=None
):
	eval_locals.update({"annual_taxable_earning": annual_taxable_earning})
	tax_amount = 0
	for slab in tax_slab.slabs:
		cond = cstr(slab.condition).strip()
		if cond and not eval_tax_slab_condition(cond, eval_globals, eval_locals):
			continue
		if not slab.to_amount and annual_taxable_earning >= slab.from_amount:
			tax_amount += (annual_taxable_earning - slab.from_amount + 1) * slab.percent_deduction * 0.01
			continue

		if annual_taxable_earning >= slab.from_amount and annual_taxable_earning < slab.to_amount:
			tax_amount += (annual_taxable_earning - slab.from_amount + 1) * slab.percent_deduction * 0.01
		elif annual_taxable_earning >= slab.from_amount and annual_taxable_earning >= slab.to_amount:
			tax_amount += (slab.to_amount - slab.from_amount + 1) * slab.percent_deduction * 0.01

	# other taxes and charges on income tax
	for d in tax_slab.other_taxes_and_charges:
		if flt(d.min_taxable_income) and flt(d.min_taxable_income) > annual_taxable_earning:
			continue

		if flt(d.max_taxable_income) and flt(d.max_taxable_income) < annual_taxable_earning:
			continue

		tax_amount += tax_amount * flt(d.percent) / 100

	return tax_amount


def eval_tax_slab_condition(condition, eval_globals=None, eval_locals=None):
	if not eval_globals:
		eval_globals = {
			"int": int,
			"float": float,
			"long": int,
			"round": round,
			"date": date,
			"getdate": getdate,
		}

	try:
		condition = condition.strip()
		if condition:
			return frappe.safe_eval(condition, eval_globals, eval_locals)
	except NameError as err:
		frappe.throw(
			_("{0} <br> This error can be due to missing or deleted field.").format(err),
			title=_("Name error"),
		)
	except SyntaxError as err:
		frappe.throw(_("Syntax error in condition: {0} in Income Tax Slab").format(err))
	except Exception as e:
		frappe.throw(_("Error in formula or condition: {0} in Income Tax Slab").format(e))
		raise


def get_lwp_or_ppl_for_date_range(employee, start_date, end_date):
	LeaveApplication = frappe.qb.DocType("Leave Application")
	LeaveType = frappe.qb.DocType("Leave Type")

	leaves = (
		frappe.qb.from_(LeaveApplication)
		.inner_join(LeaveType)
		.on((LeaveType.name == LeaveApplication.leave_type))
		.select(
			LeaveApplication.name,
			LeaveType.is_ppl,
			LeaveType.fraction_of_daily_salary_per_leave,
			LeaveType.include_holiday,
			LeaveApplication.from_date,
			LeaveApplication.to_date,
			LeaveApplication.half_day,
			LeaveApplication.half_day_date,
		)
		.where(
			(((LeaveType.is_lwp == 1) | (LeaveType.is_ppl == 1)))
			& (LeaveApplication.docstatus == 1)
			& (LeaveApplication.status == "Approved")
			& (LeaveApplication.employee == employee)
			& ((LeaveApplication.salary_slip.isnull()) | (LeaveApplication.salary_slip == ""))
			& ((LeaveApplication.from_date >= start_date) & (LeaveApplication.to_date <= end_date))
		)
	).run(as_dict=True)

	leave_date_mapper = frappe._dict()
	for leave in leaves:
		if leave.from_date == leave.to_date:
			leave_date_mapper[leave.from_date] = leave
		else:
			date_diff = (getdate(leave.to_date) - getdate(leave.from_date)).days
			for i in range(date_diff + 1):
				date = add_days(leave.from_date, i)
				leave_date_mapper[date] = leave

	return leave_date_mapper


@frappe.whitelist()
def make_salary_slip_from_timesheet(source_name, target_doc=None):
	target = frappe.new_doc("Salary Slip")
	set_missing_values(source_name, target)
	target.run_method("get_emp_and_working_day_details")

	return target


def set_missing_values(time_sheet, target):
	doc = frappe.get_doc("Timesheet", time_sheet)
	target.employee = doc.employee
	target.employee_name = doc.employee_name
	target.salary_slip_based_on_timesheet = 1
	target.start_date = doc.start_date
	target.end_date = doc.end_date
	target.posting_date = doc.modified
	target.total_working_hours = doc.total_hours
	target.append("timesheets", {"time_sheet": doc.name, "working_hours": doc.total_hours})


def throw_error_message(row, error, title, description=None):
	data = frappe._dict(
		{
			"doctype": row.parenttype,
			"name": row.parent,
			"doclink": get_link_to_form(row.parenttype, row.parent),
			"row_id": row.idx,
			"error": error,
			"title": title,
			"description": description or "",
		}
	)

	message = _(
		"Error while evaluating the {doctype} {doclink} at row {row_id}. <br><br> <b>Error:</b> {error} <br><br> <b>Hint:</b> {description}"
	).format(**data)

	frappe.throw(message, title=title)


def on_doctype_update():
	frappe.db.add_index("Salary Slip", ["employee", "start_date", "end_date"])


def _safe_eval(code: str, eval_globals: dict | None = None, eval_locals: dict | None = None):
	"""Old version of safe_eval from framework.

	Note: current frappe.safe_eval transforms code so if you have nested
	iterations with too much depth then it can hit recursion limit of python.
	There's no workaround for this and people need large formulas in some
	countries so this is alternate implementation for that.

	WARNING: DO NOT use this function anywhere else outside of this file.
	"""
	code = unicodedata.normalize("NFKC", code)

	_check_attributes(code)

	whitelisted_globals = {"int": int, "float": float, "long": int, "round": round}
	if not eval_globals:
		eval_globals = {}

	eval_globals["__builtins__"] = {}
	eval_globals.update(whitelisted_globals)
	return eval(code, eval_globals, eval_locals)  # nosemgrep


def _check_attributes(code: str) -> None:
	import ast

	from frappe.utils.safe_exec import UNSAFE_ATTRIBUTES

	unsafe_attrs = set(UNSAFE_ATTRIBUTES).union(["__"]) - {"format"}

	for attribute in unsafe_attrs:
		if attribute in code:
			raise SyntaxError(f'Illegal rule {frappe.bold(code)}. Cannot use "{attribute}"')

	BLOCKED_NODES = (ast.NamedExpr,)

	tree = ast.parse(code, mode="eval")
	for node in ast.walk(tree):
		if isinstance(node, BLOCKED_NODES):
			raise SyntaxError(f"Operation not allowed: line {node.lineno} column {node.col_offset}")
		if (
			isinstance(node, ast.Attribute)
			and isinstance(node.attr, str)
			and node.attr in UNSAFE_ATTRIBUTES
		):
			raise SyntaxError(f'Illegal rule {frappe.bold(code)}. Cannot use "{node.attr}"')


@frappe.whitelist()
def enqueue_email_salary_slips(names) -> None:
	"""enqueue bulk emailing salary slips"""
	import json

	if isinstance(names, str):
		names = json.loads(names)

	frappe.enqueue("hrms.payroll.doctype.salary_slip.salary_slip.email_salary_slips", names=names)
	frappe.msgprint(
		_("Salary slip emails have been enqueued for sending. Check {0} for status.").format(
			f"""<a href='{frappe.utils.get_url_to_list("Email Queue")}' target='blank'>Email Queue</a>"""
		)
	)


def email_salary_slips(names) -> None:
	for name in names:
		salary_slip = frappe.get_doc("Salary Slip", name)
		salary_slip.email_salary_slip()
