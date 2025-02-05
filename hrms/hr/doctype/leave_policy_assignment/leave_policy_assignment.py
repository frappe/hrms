# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _, bold
from frappe.model.document import Document
from frappe.utils import (
	add_months,
	cint,
	comma_and,
	date_diff,
	flt,
	formatdate,
	get_first_day,
	get_last_day,
	get_link_to_form,
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

		allocation = frappe.get_doc(
			dict(
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
			)
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
			new_leaves_allocated = self.get_leaves_for_passed_months(
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

		# leave allocation should not exceed annual allocation as per policy assignment
		if new_leaves_allocated > annual_allocation:
			new_leaves_allocated = annual_allocation

		return flt(new_leaves_allocated, precision)

	def get_leaves_for_passed_months(self, annual_allocation, leave_details, date_of_joining):
		from hrms.hr.utils import get_monthly_earned_leave

		def _get_current_and_from_date():
			current_date = frappe.flags.current_date or getdate()
			if current_date > getdate(self.effective_to):
				current_date = getdate(self.effective_to)

			from_date = getdate(self.effective_from)
			if getdate(date_of_joining) > from_date:
				from_date = getdate(date_of_joining)

			return current_date, from_date

		def _get_months_passed(current_date, from_date, consider_current_month):
			months_passed = 0
			if current_date.year == from_date.year and current_date.month >= from_date.month:
				months_passed = current_date.month - from_date.month
				if consider_current_month:
					months_passed += 1

			elif current_date.year > from_date.year:
				months_passed = (
					(12 - from_date.month)
					+ (current_date.year - from_date.year - 1) * 12
					+ current_date.month
				)
				if consider_current_month:
					months_passed += 1

			return months_passed

		def _get_pro_rata_period_end_date(consider_current_month):
			# for earned leave, pro-rata period ends on the last day of the month
			date = getdate(frappe.flags.current_date) or getdate()
			if consider_current_month:
				period_end_date = get_last_day(date)
			else:
				period_end_date = get_last_day(add_months(date, -1))

			return period_end_date

		def _calculate_leaves_for_passed_months(consider_current_month):
			monthly_earned_leave = get_monthly_earned_leave(
				date_of_joining,
				annual_allocation,
				leave_details.earned_leave_frequency,
				leave_details.rounding,
				pro_rated=False,
			)

			period_end_date = _get_pro_rata_period_end_date(consider_current_month)

			if getdate(self.effective_from) <= date_of_joining <= period_end_date:
				# if the employee joined within the allocation period in some previous month,
				# calculate pro-rated leave for that month
				# and normal monthly earned leave for remaining passed months
				leaves = get_monthly_earned_leave(
					date_of_joining,
					annual_allocation,
					leave_details.earned_leave_frequency,
					leave_details.rounding,
					get_first_day(date_of_joining),
					get_last_day(date_of_joining),
				)

				leaves += monthly_earned_leave * (months_passed - 1)
			else:
				leaves = monthly_earned_leave * months_passed

			return leaves

		consider_current_month = is_earned_leave_applicable_for_current_month(
			date_of_joining, leave_details.allocate_on_day
		)
		current_date, from_date = _get_current_and_from_date()
		months_passed = _get_months_passed(current_date, from_date, consider_current_month)

		if months_passed > 0:
			new_leaves_allocated = _calculate_leaves_for_passed_months(consider_current_month)
		else:
			new_leaves_allocated = 0

		return new_leaves_allocated


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


def is_earned_leave_applicable_for_current_month(date_of_joining, allocate_on_day):
	date = getdate(frappe.flags.current_date) or getdate()

	# If the date of assignment creation is >= the leave type's "Allocate On" date,
	# then the current month should be considered
	# because the employee is already entitled for the leave of that month
	if (
		(allocate_on_day == "Date of Joining" and date.day >= date_of_joining.day)
		or (allocate_on_day == "First Day" and date >= get_first_day(date))
		or (allocate_on_day == "Last Day" and date == get_last_day(date))
	):
		return True
	return False


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
