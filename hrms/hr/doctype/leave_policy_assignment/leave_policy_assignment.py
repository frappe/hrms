# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _, bold
from frappe.model.document import Document
from frappe.utils import (
	add_months,
	add_to_date,
	cint,
	comma_and,
	date_diff,
	flt,
	formatdate,
	get_first_day,
	get_last_day,
	get_link_to_form,
	get_quarter_ending,
	get_quarter_start,
	get_year_ending,
	get_year_start,
	getdate,
	rounded,
)


class LeavePolicyAssignment(Document):
	def validate(self):
		self.set_dates()
		self.validate_policy_assignment_overlap()
		self.warn_about_carry_forwarding()

	def on_submit(self):
		self.grant_leave_alloc_for_employee()

	def set_dates(self):
		if self.assignment_based_on == "Leave Period":
			self.effective_from, self.effective_to = frappe.db.get_value(
				"Leave Period", self.leave_period, ["from_date", "to_date"]
			)
		elif self.assignment_based_on == "Joining Date":
			self.effective_from = frappe.db.get_value("Employee", self.employee, "date_of_joining")
			if not self.effective_to:
				self.effective_to = get_last_day(add_months(self.effective_from, 12))

	def validate_policy_assignment_overlap(self):
		leave_policy_assignment = frappe.db.get_value(
			"Leave Policy Assignment",
			{
				"employee": self.employee,
				"name": ("!=", self.name),
				"docstatus": 1,
				"effective_to": (">=", self.effective_from),
				"effective_from": ("<=", self.effective_to),
			},
			"leave_policy",
		)

		if leave_policy_assignment:
			frappe.throw(
				_("Leave Policy: {0} already assigned for Employee {1} for period {2} to {3}").format(
					bold(leave_policy_assignment),
					bold(self.employee),
					bold(formatdate(self.effective_from)),
					bold(formatdate(self.effective_to)),
				),
				title=_("Leave Policy Assignment Overlap"),
			)

	def warn_about_carry_forwarding(self):
		if not self.carry_forward:
			return

		leave_types = get_leave_type_details()
		leave_policy = frappe.get_doc("Leave Policy", self.leave_policy)

		for policy in leave_policy.leave_policy_details:
			leave_type = leave_types.get(policy.leave_type)
			if not leave_type.is_carry_forward:
				msg = _(
					"Leaves for the Leave Type {0} won't be carry-forwarded since carry-forwarding is disabled."
				).format(frappe.bold(get_link_to_form("Leave Type", leave_type.name)))
				frappe.msgprint(msg, indicator="orange", alert=True)

	def grant_leave_alloc_for_employee(self):
		if self.leaves_allocated:
			frappe.throw(_("Leave already have been assigned for this Leave Policy Assignment"))
		else:
			leave_allocations = {}
			leave_type_details = get_leave_type_details()

			leave_policy = frappe.get_doc("Leave Policy", self.leave_policy)
			date_of_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")

			for leave_policy_detail in leave_policy.leave_policy_details:
				leave_details = leave_type_details.get(leave_policy_detail.leave_type)

				if not leave_details.is_lwp:
					leave_allocation, new_leaves_allocated = self.create_leave_allocation(
						leave_policy_detail.annual_allocation,
						leave_details,
						date_of_joining,
					)
					leave_allocations[leave_details.name] = {
						"name": leave_allocation,
						"leaves": new_leaves_allocated,
					}
			self.db_set("leaves_allocated", 1)
			return leave_allocations

	def create_leave_allocation(self, annual_allocation, leave_details, date_of_joining):
		# Creates leave allocation for the given employee in the provided leave period
		carry_forward = self.carry_forward
		if self.carry_forward and not leave_details.is_carry_forward:
			carry_forward = 0

		new_leaves_allocated = self.get_new_leaves(annual_allocation, leave_details, date_of_joining)
		earned_leave_schedule = (
			self.get_earned_leave_schedule(
				annual_allocation, leave_details, date_of_joining, new_leaves_allocated
			)
			if leave_details.is_earned_leave
			else []
		)

		if new_leaves_allocated == 0 and not leave_details.is_earned_leave:
			text = _(
				"Leave allocation is skipped for {0}, because number of leaves to be allocated is 0."
			).format(frappe.bold(leave_details.name))

			frappe.get_doc(
				{
					"doctype": "Comment",
					"comment_type": "Comment",
					"reference_doctype": "Leave Policy Assignment",
					"reference_name": self.name,
					"content": text,
				}
			).insert(ignore_permissions=True)
			return None, 0

		allocation = frappe.get_doc(
			doctype="Leave Allocation",
			employee=self.employee,
			leave_type=leave_details.name,
			from_date=self.effective_from,
			to_date=self.effective_to,
			new_leaves_allocated=new_leaves_allocated,
			leave_period=self.leave_period if self.assignment_based_on == "Leave Policy" else "",
			leave_policy_assignment=self.name,
			leave_policy=self.leave_policy,
			carry_forward=carry_forward,
			earned_leave_schedule=earned_leave_schedule,
		)
		allocation.save(ignore_permissions=True)
		allocation.submit()
		return allocation.name, new_leaves_allocated

	def get_new_leaves(self, annual_allocation, leave_details, date_of_joining):
		from frappe.model.meta import get_field_precision

		precision = get_field_precision(frappe.get_meta("Leave Allocation").get_field("new_leaves_allocated"))
		current_date = getdate(frappe.flags.current_date) or getdate()
		# Earned Leaves and Compensatory Leaves are allocated by scheduler, initially allocate 0
		if leave_details.is_compensatory:
			new_leaves_allocated = 0
		# if earned leave is being allcated after the effective period, then let them be calculated pro-rata
		elif leave_details.is_earned_leave and current_date < getdate(self.effective_to):
			new_leaves_allocated = self.get_leaves_for_passed_period(
				annual_allocation, leave_details, date_of_joining
			)
		else:
			# calculate pro-rated leaves for other leave types
			new_leaves_allocated = calculate_pro_rated_leaves(
				annual_allocation,
				date_of_joining,
				self.effective_from,
				self.effective_to,
				is_earned_leave=False,
			)
		# leave allocation should not exceed annual allocation as per policy assignment expect when allocation is of earned type and yearly
		if new_leaves_allocated > annual_allocation and not (
			leave_details.is_earned_leave and leave_details.earned_leave_frequency == "Yearly"
		):
			new_leaves_allocated = annual_allocation

		return flt(new_leaves_allocated, precision)

	def get_leaves_for_passed_period(self, annual_allocation, leave_details, date_of_joining):
		consider_current_period = is_earned_leave_applicable_for_current_period(
			date_of_joining, leave_details.allocate_on_day, leave_details.earned_leave_frequency
		)
		current_date, from_date = self.get_current_and_from_date(date_of_joining)
		periods_passed = self.get_periods_passed(
			leave_details.earned_leave_frequency, current_date, from_date, consider_current_period
		)
		if periods_passed > 0:
			new_leaves_allocated = self.calculate_leaves_for_passed_period(
				annual_allocation, leave_details, date_of_joining, periods_passed, consider_current_period
			)
		else:
			new_leaves_allocated = 0

		return new_leaves_allocated

	def get_current_and_from_date(self, date_of_joining):
		current_date = getdate(frappe.flags.current_date) or getdate()
		if current_date > getdate(self.effective_to):
			current_date = getdate(self.effective_to)

		from_date = getdate(self.effective_from)
		if getdate(date_of_joining) > from_date:
			from_date = getdate(date_of_joining)

		return current_date, from_date

	def get_periods_passed(self, earned_leave_frequency, current_date, from_date, consider_current_period):
		periods_per_year, months_per_period = {
			"Monthly": (12, 1),
			"Quarterly": (4, 3),
			"Half-Yearly": (2, 6),
			"Yearly": (1, 12),
		}.get(earned_leave_frequency)

		periods_passed = calculate_periods_passed(
			current_date, from_date, periods_per_year, months_per_period, consider_current_period
		)

		return periods_passed

	def calculate_leaves_for_passed_period(
		self, annual_allocation, leave_details, date_of_joining, periods_passed, consider_current_period
	):
		from hrms.hr.utils import get_monthly_earned_leave as get_periodically_earned_leave
		from hrms.hr.utils import get_sub_period_start_and_end

		periodically_earned_leave = get_periodically_earned_leave(
			date_of_joining,
			annual_allocation,
			leave_details.earned_leave_frequency,
			leave_details.rounding,
			pro_rated=False,
		)

		period_end_date = get_pro_rata_period_end_date(consider_current_period)
		if getdate(self.effective_from) <= date_of_joining <= period_end_date:
			# if the employee joined within the allocation period in some previous month,
			# calculate pro-rated leave for that month
			# and normal monthly earned leave for remaining passed months
			start_date, end_date = get_sub_period_start_and_end(
				date_of_joining, leave_details.earned_leave_frequency
			)
			leaves = get_periodically_earned_leave(
				date_of_joining,
				annual_allocation,
				leave_details.earned_leave_frequency,
				leave_details.rounding,
				start_date,
				end_date,
			)
			leaves += periodically_earned_leave * (periods_passed - 1)
		else:
			leaves = periodically_earned_leave * periods_passed

		return leaves

	def get_earned_leave_schedule(
		self, annual_allocation, leave_details, date_of_joining, new_leaves_allocated
	):
		from hrms.hr.utils import (
			get_expected_allocation_date_for_period,
			get_monthly_earned_leave,
			get_sub_period_start_and_end,
		)

		today = getdate(frappe.flags.current_date) or getdate()
		from_date = last_allocated_date = getdate(self.effective_from)
		to_date = getdate(self.effective_to)
		months_to_add = {"Monthly": 1, "Quarterly": 3, "Half-Yearly": 6, "Yearly": 12}.get(
			leave_details.earned_leave_frequency
		)
		periodically_earned_leave = get_monthly_earned_leave(
			date_of_joining,
			annual_allocation,
			leave_details.earned_leave_frequency,
			leave_details.rounding,
			pro_rated=False,
		)
		date = get_expected_allocation_date_for_period(
			leave_details.earned_leave_frequency,
			leave_details.allocate_on_day,
			from_date,
			date_of_joining,
		)
		schedule = []
		if new_leaves_allocated:
			schedule.append(
				{
					"allocation_date": today,
					"number_of_leaves": new_leaves_allocated,
					"is_allocated": 1,
					"allocated_via": "Leave Policy Assignment",
					"attempted": 1,
				}
			)
			last_allocated_date = get_sub_period_start_and_end(today, leave_details.earned_leave_frequency)[1]

		while date <= to_date:
			date_already_passed = today > date
			if date >= last_allocated_date:
				row = {
					"allocation_date": date,
					"number_of_leaves": periodically_earned_leave,
					"is_allocated": 1 if date_already_passed else 0,
					"allocated_via": "Leave Policy Assignment" if date_already_passed else None,
					"attempted": 1 if date_already_passed else 0,
				}
				schedule.append(row)
			date = get_expected_allocation_date_for_period(
				leave_details.earned_leave_frequency,
				leave_details.allocate_on_day,
				add_to_date(date, months=months_to_add),
				date_of_joining,
			)
		if from_date < getdate(date_of_joining):
			pro_rated_period_start, pro_rated_period_end = get_sub_period_start_and_end(
				date_of_joining, leave_details.earned_leave_frequency
			)
			pro_rated_earned_leave = get_monthly_earned_leave(
				date_of_joining,
				annual_allocation,
				leave_details.earned_leave_frequency,
				leave_details.rounding,
				pro_rated_period_start,
				pro_rated_period_end,
			)
			schedule[0]["number_of_leaves"] = pro_rated_earned_leave
		return schedule


def get_pro_rata_period_end_date(consider_current_month):
	# for earned leave, pro-rata period ends on the last day of the month
	# pro rata period end date is different for different periods

	date = getdate(frappe.flags.current_date) or getdate()
	if consider_current_month:
		period_end_date = get_last_day(date)
	else:
		period_end_date = get_last_day(add_months(date, -1))

	return period_end_date


def calculate_periods_passed(
	current_date, from_date, periods_per_year, months_per_period, consider_current_period
):
	periods_passed = 0

	from_period = (from_date.year * periods_per_year) + ((from_date.month - 1) // months_per_period)
	current_period = (current_date.year * periods_per_year) + ((current_date.month - 1) // months_per_period)

	periods_passed = current_period - from_period
	if consider_current_period:
		periods_passed += 1

	return periods_passed


def is_earned_leave_applicable_for_current_period(date_of_joining, allocate_on_day, earned_leave_frequency):
	from hrms.hr.utils import get_semester_end, get_semester_start

	date = getdate(frappe.flags.current_date) or getdate()
	# If the date of assignment creation is >= the leave type's "Allocate On" date,
	# then the current month should be considered
	# because the employee is already entitled for the leave of that month

	condition_map = {
		"Monthly": (
			(allocate_on_day == "Date of Joining" and date.day >= date_of_joining.day)
			or (allocate_on_day == "First Day" and date >= get_first_day(date))
			or (allocate_on_day == "Last Day" and date == get_last_day(date))
		),
		"Quarterly": (allocate_on_day == "First Day" and date >= get_quarter_start(date))
		or (allocate_on_day == "Last Day" and date == get_quarter_ending(date)),
		"Half-Yearly": (allocate_on_day == "First Day" and date >= get_semester_start(date))
		or (allocate_on_day == "Last Day" and date == get_semester_end(date)),
		"Yearly": (
			(allocate_on_day == "First Day" and date >= get_year_start(date))
			or (allocate_on_day == "Last Day" and date == get_year_ending(date))
		),
	}

	return condition_map.get(earned_leave_frequency)


def calculate_pro_rated_leaves(
	leaves, date_of_joining, period_start_date, period_end_date, is_earned_leave=False
):
	if not leaves or getdate(date_of_joining) <= getdate(period_start_date):
		return leaves

	precision = cint(frappe.db.get_single_value("System Settings", "float_precision", cache=True))
	actual_period = date_diff(period_end_date, date_of_joining) + 1
	complete_period = date_diff(period_end_date, period_start_date) + 1

	leaves *= actual_period / complete_period

	if is_earned_leave:
		return flt(leaves, precision)
	return rounded(leaves)


@frappe.whitelist()
def create_assignment_for_multiple_employees(employees, data):
	if isinstance(employees, str):
		employees = json.loads(employees)

	if isinstance(data, str):
		data = frappe._dict(json.loads(data))

	docs_name = []
	failed = []

	for employee in employees:
		assignment = create_assignment(employee, data)
		savepoint = "before_assignment_submission"
		try:
			frappe.db.savepoint(savepoint)
			assignment.submit()
		except Exception:
			frappe.db.rollback(save_point=savepoint)
			assignment.log_error("Leave Policy Assignment submission failed")
			failed.append(assignment.name)

		docs_name.append(assignment.name)

	if failed:
		show_assignment_submission_status(failed)

	return docs_name


@frappe.whitelist()
def create_assignment(employee, data):
	assignment = frappe.new_doc("Leave Policy Assignment")
	assignment.employee = employee
	assignment.assignment_based_on = data.assignment_based_on or None
	assignment.leave_policy = data.leave_policy
	assignment.effective_from = getdate(data.effective_from) or None
	assignment.effective_to = getdate(data.effective_to) or None
	assignment.leave_period = data.leave_period or None
	assignment.carry_forward = data.carry_forward
	assignment.save()
	return assignment


def show_assignment_submission_status(failed):
	frappe.clear_messages()
	assignment_list = [get_link_to_form("Leave Policy Assignment", entry) for entry in failed]

	msg = _("Failed to submit some leave policy assignments:")
	msg += " " + comma_and(assignment_list, False) + "<hr>"
	msg += (
		_("Check {0} for more details")
		.format("<a href='/app/List/Error Log?reference_doctype=Leave Policy Assignment'>{0}</a>")
		.format(_("Error Log"))
	)

	frappe.msgprint(
		msg,
		indicator="red",
		title=_("Submission Failed"),
		is_minimizable=True,
	)


def get_leave_type_details():
	leave_type_details = frappe._dict()
	leave_types = frappe.get_all(
		"Leave Type",
		fields=[
			"name",
			"is_lwp",
			"is_earned_leave",
			"is_compensatory",
			"allocate_on_day",
			"is_carry_forward",
			"expire_carry_forwarded_leaves_after_days",
			"earned_leave_frequency",
			"rounding",
		],
	)
	for d in leave_types:
		leave_type_details.setdefault(d.name, d)
	return leave_type_details
