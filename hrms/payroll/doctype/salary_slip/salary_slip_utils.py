# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import datetime

import frappe
from frappe import _
from frappe.query_builder.functions import Sum
from frappe.utils import add_days, date_diff, format_datetime, formatdate, getdate


def get_benefits_details_parent(employee, payroll_period, salary_structure_assignment):
	"""Returns the parent and doctype of benefit details based on the following logic:
	1. If 'Mandatory Benefit Application' is enabled in Payroll Settings, only consider Employee Benefit Application
	2. If not enabled, prefer Employee Benefit Application but fallback to Salary Structure Assignment if
	   former does not exist"""
	mandatory_benefit_application = frappe.db.get_single_value(
		"Payroll Settings", "mandatory_benefit_application"
	)
	benefit_details_parent = None
	benefit_details_doctype = None
	# Check if Employee Benefit Application exists
	employee_benefit_application = frappe.db.get_value(
		"Employee Benefit Application",
		{"employee": employee, "payroll_period": payroll_period, "docstatus": 1},
		"name",
	)

	if mandatory_benefit_application:
		# If mandatory, only consider Employee Benefit Application
		if employee_benefit_application:
			benefit_details_parent = employee_benefit_application
			benefit_details_doctype = "Employee Benefit Application Detail"
	else:
		# If not mandatory, prefer Employee Benefit Application but fallback to Salary Structure Assignment
		if employee_benefit_application:
			benefit_details_parent = employee_benefit_application
			benefit_details_doctype = "Employee Benefit Application Detail"
		else:
			benefit_details_parent = salary_structure_assignment
			benefit_details_doctype = "Employee Benefit Detail"

	return benefit_details_parent, benefit_details_doctype


class SystemFormattedDate(datetime.date):
	"""Date that renders in the system date format when interpolated into a password policy.

	Subclasses `date` so that policies relying on the underlying object, like
	`{date_of_birth.year}` or `{date_of_birth:%d%m%Y}`, keep working.
	"""

	def __str__(self):
		return formatdate(datetime.date(self.year, self.month, self.day))


class SystemFormattedDatetime(datetime.datetime):
	"""Datetime counterpart of `SystemFormattedDate`."""

	def __str__(self):
		return format_datetime(
			datetime.datetime(
				self.year, self.month, self.day, self.hour, self.minute, self.second, self.microsecond
			)
		)


def format_dates_in_system_format(value):
	# datetime is a subclass of date, so it has to be checked first
	if isinstance(value, datetime.datetime):
		return SystemFormattedDatetime(
			value.year, value.month, value.day, value.hour, value.minute, value.second, value.microsecond
		)
	if isinstance(value, datetime.date):
		return SystemFormattedDate(value.year, value.month, value.day)
	return value


def generate_password_for_pdf(policy_template, employee):
	employee = frappe.get_cached_doc("Employee", employee)
	values = {key: format_dates_in_system_format(value) for key, value in employee.as_dict().items()}
	return policy_template.format(**values)


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


def get_lwp_or_ppl_for_date_range(employee, start_date, end_date):
	LeaveApplication = frappe.qb.DocType("Leave Application")
	LeaveType = frappe.qb.DocType("Leave Type")

	leaves = (
		frappe.qb.from_(LeaveApplication)
		.inner_join(LeaveType)
		.on(LeaveType.name == LeaveApplication.leave_type)
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
			((LeaveType.is_lwp == 1) | (LeaveType.is_ppl == 1))
			& (LeaveApplication.docstatus == 1)
			& (LeaveApplication.status == "Approved")
			& (LeaveApplication.employee == employee)
			& ((LeaveApplication.salary_slip.isnull()) | (LeaveApplication.salary_slip == ""))
			& ((LeaveApplication.from_date <= end_date) & (LeaveApplication.to_date >= start_date))
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


def verify_lwp_days_corrected(employee, start_date, end_date, lwp_days_corrected):
	#  Verify that the provided lwp_days_corrected matches actual payroll corrections.
	PayrollCorrection = frappe.qb.DocType("Payroll Correction")
	SalarySlip = frappe.qb.DocType("Salary Slip")

	actual_days_reversed = (
		frappe.qb.from_(PayrollCorrection)
		.join(SalarySlip)
		.on(PayrollCorrection.salary_slip_reference == SalarySlip.name)
		.select(Sum(PayrollCorrection.days_to_reverse).as_("total_days"))
		.where(
			(PayrollCorrection.employee == employee)
			& (PayrollCorrection.docstatus == 1)
			& (SalarySlip.start_date == start_date)
			& (SalarySlip.end_date == end_date)
		)
	).run(pluck=True)

	actual_total = actual_days_reversed[0] or 0.0

	if lwp_days_corrected != actual_total:
		frappe.throw(
			_(
				"LWP Days Reversed ({0}) does not match actual Payroll Corrections total ({1}) for employee {2} from {3} to {4}"
			).format(lwp_days_corrected, actual_total, employee, start_date, end_date),
			title=_("Invalid LWP Days Reversed"),
		)

	return True
