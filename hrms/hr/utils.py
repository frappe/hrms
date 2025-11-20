# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import calendar
import datetime

import frappe
from frappe import _, qb
from frappe.model.document import Document
from frappe.query_builder import Criterion
from frappe.query_builder.custom import ConstantColumn
from frappe.query_builder.functions import Count
from frappe.utils import (
	add_days,
	add_months,
	comma_and,
	cstr,
	flt,
	format_datetime,
	formatdate,
	get_datetime,
	get_first_day,
	get_last_day,
	get_link_to_form,
	get_number_format_info,
	get_quarter_ending,
	get_quarter_start,
	get_year_ending,
	get_year_start,
	getdate,
	nowdate,
)

import erpnext
from erpnext import get_company_currency
from erpnext.setup.doctype.employee.employee import (
	InactiveEmployeeStatusError,
	get_holiday_list_for_employee,
)

from hrms.hr.doctype.leave_policy_assignment.leave_policy_assignment import (
	calculate_pro_rated_leaves,
)

DateTimeLikeObject = str | datetime.date | datetime.datetime


class DuplicateDeclarationError(frappe.ValidationError):
	pass


class OverAllocationError(frappe.ValidationError):
	pass


def set_employee_name(doc):
	if doc.employee and not doc.employee_name:
		doc.employee_name = frappe.db.get_value("Employee", doc.employee, "employee_name")


def update_employee_work_history(employee, details, date=None, cancel=False):
	if not details:
		return employee

	if not employee.internal_work_history and not cancel:
		employee.append(
			"internal_work_history",
			{
				"branch": employee.branch,
				"designation": employee.designation,
				"department": employee.department,
				"from_date": employee.date_of_joining,
			},
		)

	internal_work_history = {}
	for item in details:
		field = frappe.get_meta("Employee").get_field(item.fieldname)
		if not field:
			continue

		new_value = item.new if not cancel else item.current
		new_value = get_formatted_value(new_value, field.fieldtype)
		setattr(employee, item.fieldname, new_value)

		if item.fieldname in ["department", "designation", "branch"]:
			internal_work_history[item.fieldname] = item.new

	if internal_work_history and not cancel:
		internal_work_history["from_date"] = date
		employee.append("internal_work_history", internal_work_history)

	if cancel:
		delete_employee_work_history(details, employee, date)

	update_to_date_in_work_history(employee, cancel)

	return employee


def get_formatted_value(value, fieldtype):
	"""
	Since the fields in Internal Work History table are `Data` fields
	format them as per relevant field types
	"""
	if not value:
		return

	if fieldtype == "Date":
		value = getdate(value)
	elif fieldtype == "Datetime":
		value = get_datetime(value)
	elif fieldtype in ["Currency", "Float"]:
		# in case of currency/float, the value might be in user's prefered number format
		# instead of machine readable format. Convert it into a machine readable format
		number_format = frappe.db.get_default("number_format") or "#,###.##"
		decimal_str, comma_str, _number_format_precision = get_number_format_info(number_format)

		if comma_str == "." and decimal_str == ",":
			value = value.replace(",", "#$")
			value = value.replace(".", ",")
			value = value.replace("#$", ".")

		value = flt(value)

	return value


def delete_employee_work_history(details, employee, date):
	filters = {}
	for d in details:
		for history in employee.internal_work_history:
			if d.property == "Department" and history.department == d.new:
				department = d.new
				filters["department"] = department
			if d.property == "Designation" and history.designation == d.new:
				designation = d.new
				filters["designation"] = designation
			if d.property == "Branch" and history.branch == d.new:
				branch = d.new
				filters["branch"] = branch
			if date and date == history.from_date:
				filters["from_date"] = date
	if filters:
		frappe.db.delete("Employee Internal Work History", filters)
		employee.save()


def update_to_date_in_work_history(employee, cancel):
	if not employee.internal_work_history:
		return

	for idx, row in enumerate(employee.internal_work_history):
		if not row.from_date or idx == 0:
			continue

		prev_row = employee.internal_work_history[idx - 1]
		if not prev_row.to_date:
			prev_row.to_date = add_days(row.from_date, -1)

	if cancel:
		employee.internal_work_history[-1].to_date = None


@frappe.whitelist()
def get_employee_field_property(employee, fieldname):
	if not (employee and fieldname):
		return

	field = frappe.get_meta("Employee").get_field(fieldname)
	if not field:
		return

	value = frappe.db.get_value("Employee", employee, fieldname)
	if field.fieldtype == "Date":
		value = formatdate(value)
	elif field.fieldtype == "Datetime":
		value = format_datetime(value)

	return {
		"value": value,
		"datatype": field.fieldtype,
		"label": field.label,
		"options": field.options,
	}


def validate_dates(doc, from_date, to_date, restrict_future_dates=True):
	date_of_joining, relieving_date = frappe.db.get_value(
		"Employee", doc.employee, ["date_of_joining", "relieving_date"]
	)
	if getdate(from_date) > getdate(to_date):
		frappe.throw(_("To date can not be less than from date"))
	elif getdate(from_date) > getdate(nowdate()) and restrict_future_dates:
		frappe.throw(_("Future dates not allowed"))
	elif date_of_joining and getdate(from_date) < getdate(date_of_joining):
		frappe.throw(_("From date can not be less than employee's joining date"))
	elif relieving_date and getdate(to_date) > getdate(relieving_date):
		frappe.throw(_("To date can not greater than employee's relieving date"))


def validate_overlap(doc, from_date, to_date, company=None):
	query = """
		select name
		from `tab{0}`
		where name != %(name)s
		"""
	query += get_doc_condition(doc.doctype)

	if not doc.name:
		# hack! if name is null, it could cause problems with !=
		doc.name = "New " + doc.doctype

	overlap_doc = frappe.db.sql(
		query.format(doc.doctype),
		{
			"employee": doc.get("employee"),
			"from_date": from_date,
			"to_date": to_date,
			"name": doc.name,
			"company": company,
		},
		as_dict=1,
	)

	if overlap_doc:
		if doc.get("employee"):
			exists_for = doc.employee
		if company:
			exists_for = company
		throw_overlap_error(doc, exists_for, overlap_doc[0].name, from_date, to_date)


def get_doc_condition(doctype):
	if doctype == "Compensatory Leave Request":
		return "and employee = %(employee)s and docstatus < 2 \
		and (work_from_date between %(from_date)s and %(to_date)s \
		or work_end_date between %(from_date)s and %(to_date)s \
		or (work_from_date < %(from_date)s and work_end_date > %(to_date)s))"
	elif doctype == "Leave Period":
		return "and company = %(company)s and (from_date between %(from_date)s and %(to_date)s \
			or to_date between %(from_date)s and %(to_date)s \
			or (from_date < %(from_date)s and to_date > %(to_date)s))"


def throw_overlap_error(doc, exists_for, overlap_doc, from_date, to_date):
	msg = (
		_("A {0} exists between {1} and {2} (").format(
			doc.doctype, formatdate(from_date), formatdate(to_date)
		)
		+ f""" <b><a href="/app/Form/{doc.doctype}/{overlap_doc}">{overlap_doc}</a></b>"""
		+ _(") for {0}").format(exists_for)
	)
	frappe.throw(msg)


def validate_duplicate_exemption_for_payroll_period(doctype, docname, payroll_period, employee):
	existing_record = frappe.db.exists(
		doctype,
		{
			"payroll_period": payroll_period,
			"employee": employee,
			"docstatus": ["<", 2],
			"name": ["!=", docname],
		},
	)
	if existing_record:
		frappe.throw(
			_("{0} already exists for employee {1} and period {2}").format(doctype, employee, payroll_period),
			DuplicateDeclarationError,
		)


def validate_tax_declaration(declarations):
	subcategories = []
	for d in declarations:
		if d.exemption_sub_category in subcategories:
			frappe.throw(_("More than one selection for {0} not allowed").format(d.exemption_sub_category))
		subcategories.append(d.exemption_sub_category)


def get_total_exemption_amount(declarations):
	exemptions = frappe._dict()
	for d in declarations:
		exemptions.setdefault(d.exemption_category, frappe._dict())
		category_max_amount = exemptions.get(d.exemption_category).max_amount
		if not category_max_amount:
			category_max_amount = frappe.db.get_value(
				"Employee Tax Exemption Category", d.exemption_category, "max_amount"
			)
			exemptions.get(d.exemption_category).max_amount = category_max_amount
		sub_category_exemption_amount = (
			d.max_amount if (d.max_amount and flt(d.amount) > flt(d.max_amount)) else d.amount
		)

		exemptions.get(d.exemption_category).setdefault("total_exemption_amount", 0.0)
		exemptions.get(d.exemption_category).total_exemption_amount += flt(sub_category_exemption_amount)

		if (
			category_max_amount
			and exemptions.get(d.exemption_category).total_exemption_amount > category_max_amount
		):
			exemptions.get(d.exemption_category).total_exemption_amount = category_max_amount

	total_exemption_amount = sum([flt(d.total_exemption_amount) for d in exemptions.values()])
	return total_exemption_amount


@frappe.whitelist()
def get_leave_period(from_date, to_date, company):
	leave_period = frappe.db.sql(
		"""
		select name, from_date, to_date
		from `tabLeave Period`
		where company=%(company)s and is_active=1
			and (from_date between %(from_date)s and %(to_date)s
				or to_date between %(from_date)s and %(to_date)s
				or (from_date < %(from_date)s and to_date > %(to_date)s))
	""",
		{"from_date": from_date, "to_date": to_date, "company": company},
		as_dict=1,
	)

	if leave_period:
		return leave_period


def generate_leave_encashment():
	"""Generates a draft leave encashment on allocation expiry"""
	from hrms.hr.doctype.leave_encashment.leave_encashment import create_leave_encashment

	if frappe.db.get_single_value("HR Settings", "auto_leave_encashment"):
		leave_type = frappe.get_all("Leave Type", filters={"allow_encashment": 1}, fields=["name"])
		leave_type = [l["name"] for l in leave_type]

		leave_allocation = frappe.get_all(
			"Leave Allocation",
			filters=[
				["to_date", "=", add_days(getdate(), -1)],
				["leave_type", "in", leave_type],
			],
			fields=[
				"employee",
				"leave_period",
				"leave_type",
				"to_date",
				"total_leaves_allocated",
				"new_leaves_allocated",
			],
		)

		create_leave_encashment(leave_allocation=leave_allocation)


def allocate_earned_leaves():
	"""Allocate earned leaves to Employees"""
	e_leave_types = get_earned_leaves()
	today = frappe.flags.current_date or getdate()
	failed_allocations = []
	for e_leave_type in e_leave_types:
		leave_allocations = get_leave_allocations(today, e_leave_type.name)
		for allocation in leave_allocations:
			if allocation.earned_leave_schedule_exists:
				allocation_date, earned_leaves = get_upcoming_earned_leave_from_schedule(
					allocation.name, today
				) or (None, None)
				annual_allocation = get_annual_allocation_from_policy(allocation, e_leave_type)
			else:
				date_of_joining = frappe.db.get_value("Employee", allocation.employee, "date_of_joining")
				allocation_date = get_expected_allocation_date_for_period(
					e_leave_type.earned_leave_frequency, e_leave_type.allocate_on_day, today, date_of_joining
				)
				annual_allocation = get_annual_allocation_from_policy(allocation, e_leave_type)
				earned_leaves = calculate_upcoming_earned_leave(allocation, e_leave_type, date_of_joining)

			if not allocation_date or allocation_date != today:
				continue
			try:
				update_previous_leave_allocation(
					allocation, annual_allocation, e_leave_type, earned_leaves, today
				)
			except Exception as e:
				log_allocation_error(allocation.name, e)
				failed_allocations.append(allocation.name)
	if failed_allocations:
		send_email_for_failed_allocations(failed_allocations)


def get_upcoming_earned_leave_from_schedule(allocation_name, today):
	return frappe.db.get_value(
		"Earned Leave Schedule",
		{"parent": allocation_name, "attempted": 0, "allocation_date": today},
		["allocation_date", "number_of_leaves"],
	)


def get_annual_allocation_from_policy(allocation, e_leave_type):
	return frappe.db.get_value(
		"Leave Policy Detail",
		filters={"parent": allocation.leave_policy, "leave_type": e_leave_type.name},
		fieldname=["annual_allocation"],
	)


def calculate_upcoming_earned_leave(allocation, e_leave_type, date_of_joining):
	annual_allocation = get_annual_allocation_from_policy(allocation, e_leave_type)
	earned_leave = get_monthly_earned_leave(
		date_of_joining,
		annual_allocation,
		e_leave_type.earned_leave_frequency,
		e_leave_type.rounding,
	)
	return earned_leave


def update_previous_leave_allocation(allocation, annual_allocation, e_leave_type, earned_leaves, today):
	allocation = frappe.get_doc("Leave Allocation", allocation.name)
	annual_allocation = flt(annual_allocation, allocation.precision("total_leaves_allocated"))

	new_allocation = flt(allocation.total_leaves_allocated) + flt(earned_leaves)
	new_allocation_without_cf = flt(
		flt(allocation.get_existing_leave_count()) + flt(earned_leaves),
		allocation.precision("total_leaves_allocated"),
	)

	if new_allocation > e_leave_type.max_leaves_allowed and e_leave_type.max_leaves_allowed > 0:
		frappe.throw(
			_(
				"Allocation was skipped due to maximum leave allocation limit set in leave type. Please increase the limit and retry failed allocation."
			),
			OverAllocationError,
		)
	if (
		# annual allocation as per policy should not be exceeded except for yearly leaves
		new_allocation_without_cf > annual_allocation and e_leave_type.earned_leave_frequency != "Yearly"
	):
		frappe.throw(
			_("Allocation was skipped due to exceeding annual allocation set in leave policy"),
			OverAllocationError,
		)

	allocation.db_set("total_leaves_allocated", new_allocation, update_modified=False)
	create_additional_leave_ledger_entry(allocation, earned_leaves, today)
	earned_leave_schedule = qb.DocType("Earned Leave Schedule")
	qb.update(earned_leave_schedule).where(
		(earned_leave_schedule.parent == allocation.name) & (earned_leave_schedule.allocation_date == today)
	).set(earned_leave_schedule.is_allocated, 1).set(earned_leave_schedule.attempted, 1).set(
		earned_leave_schedule.allocated_via, "Scheduler"
	).run()


def log_allocation_error(allocation_name, error):
	error_log = frappe.log_error(error, reference_doctype="Leave Allocation")
	text = _("{0}. Check error log for more details.").format(error_log.method)
	earned_leave_schedule = qb.DocType("Earned Leave Schedule")
	today = getdate(frappe.flags.current_date) or getdate()

	qb.update(earned_leave_schedule).where(
		(earned_leave_schedule.parent == allocation_name) & (earned_leave_schedule.allocation_date == today)
	).set(earned_leave_schedule.attempted, 1).set(earned_leave_schedule.failed, 1).set(
		earned_leave_schedule.failure_reason, text
	).run()


def send_email_for_failed_allocations(failed_allocations):
	allocations = comma_and([get_link_to_form("Leave Allocation", x) for x in failed_allocations])
	User = frappe.qb.DocType("User")
	HasRole = frappe.qb.DocType("Has Role")
	query = (
		frappe.qb.from_(HasRole)
		.left_join(User)
		.on(HasRole.parent == User.name)
		.select(HasRole.parent)
		.distinct()
		.where((HasRole.parenttype == "User") & (User.enabled == 1) & (HasRole.role == "HR Manager"))
	)
	hr_managers = query.run(pluck=True)

	frappe.sendmail(
		recipients=hr_managers,
		subject=_("Failure of Automatic Allocation of Earned Leaves"),
		message=_(
			"Automatic Leave Allocation has failed for the following Earned Leaves: {0}. Please check {1} for more details."
		).format(allocations, get_link_to_form("Error Log", label="Error Log List")),
	)


@frappe.whitelist()
def get_monthly_earned_leave(
	date_of_joining,
	annual_leaves,
	frequency,
	rounding,
	period_start_date=None,
	period_end_date=None,
	pro_rated=True,
):
	earned_leaves = 0.0
	divide_by_frequency = {"Yearly": 1, "Half-Yearly": 2, "Quarterly": 4, "Monthly": 12}
	if annual_leaves:
		earned_leaves = flt(annual_leaves) / divide_by_frequency[frequency]

		if pro_rated:
			if not (period_start_date or period_end_date):
				today_date = frappe.flags.current_date or getdate()
				period_start_date, period_end_date = get_sub_period_start_and_end(today_date, frequency)

			earned_leaves = calculate_pro_rated_leaves(
				earned_leaves, date_of_joining, period_start_date, period_end_date, is_earned_leave=True
			)

		earned_leaves = round_earned_leaves(earned_leaves, rounding)

	return earned_leaves


def get_sub_period_start_and_end(date, frequency):
	return {
		"Monthly": (get_first_day(date), get_last_day(date)),
		"Quarterly": (get_quarter_start(date), get_quarter_ending(date)),
		"Half-Yearly": (get_semester_start(date), get_semester_end(date)),
		"Yearly": (get_year_start(date), get_year_ending(date)),
	}.get(frequency)


def round_earned_leaves(earned_leaves, rounding):
	if not rounding:
		return earned_leaves

	if rounding == "0.25":
		earned_leaves = round(earned_leaves * 4) / 4
	elif rounding == "0.5":
		earned_leaves = round(earned_leaves * 2) / 2
	else:
		earned_leaves = round(earned_leaves)

	return earned_leaves


def get_leave_allocations(date, leave_type):
	employee = frappe.qb.DocType("Employee")
	leave_allocation = frappe.qb.DocType("Leave Allocation")
	earned_leave_schedule = frappe.qb.DocType("Earned Leave Schedule")

	query = (
		frappe.qb.from_(leave_allocation)
		.join(employee)
		.on(leave_allocation.employee == employee.name)
		.left_join(earned_leave_schedule)
		.on(leave_allocation.name == earned_leave_schedule.parent)
		.select(
			leave_allocation.name,
			leave_allocation.employee,
			leave_allocation.from_date,
			leave_allocation.to_date,
			leave_allocation.leave_policy_assignment,
			leave_allocation.leave_policy,
			Count(earned_leave_schedule.parent).as_("earned_leave_schedule_exists"),
		)
		.where(
			(date >= leave_allocation.from_date)
			& (date <= leave_allocation.to_date)
			& (leave_allocation.docstatus == 1)
			& (leave_allocation.leave_type == leave_type)
			& (leave_allocation.leave_policy_assignment.isnotnull())
			& (leave_allocation.leave_policy.isnotnull())
			& (employee.status != "Left")
		)
		.groupby(leave_allocation.name)
	)
	return query.run(as_dict=1) or []


def get_earned_leaves():
	return frappe.get_all(
		"Leave Type",
		fields=[
			"name",
			"max_leaves_allowed",
			"earned_leave_frequency",
			"rounding",
			"allocate_on_day",
		],
		filters={"is_earned_leave": 1},
	)


def create_additional_leave_ledger_entry(allocation, leaves, date):
	"""Create leave ledger entry for leave types"""
	allocation.new_leaves_allocated = leaves
	allocation.from_date = date
	allocation.unused_leaves = 0
	allocation.create_leave_ledger_entry()


def get_expected_allocation_date_for_period(frequency, allocate_on_day, date, date_of_joining=None):
	try:
		doj = date_of_joining.replace(month=date.month, year=date.year)
	except ValueError:
		doj = datetime.date(date.year, date.month, calendar.monthrange(date.year, date.month)[1])
	return {
		"Monthly": {
			"First Day": get_first_day(date),
			"Last Day": get_last_day(date),
			"Date of Joining": doj,
		},
		"Quarterly": {
			"First Day": get_quarter_start(date),
			"Last Day": get_quarter_ending(date),
		},
		"Half-Yearly": {"First Day": get_semester_start(date), "Last Day": get_semester_end(date)},
		"Yearly": {"First Day": get_year_start(date), "Last Day": get_year_ending(date)},
	}[frequency][allocate_on_day]


def get_salary_assignments(employee, payroll_period):
	start_date, end_date = frappe.db.get_value("Payroll Period", payroll_period, ["start_date", "end_date"])
	assignments = frappe.get_all(
		"Salary Structure Assignment",
		filters={"employee": employee, "docstatus": 1, "from_date": ["between", (start_date, end_date)]},
		fields=["*"],
		order_by="from_date",
	)

	if not assignments or getdate(assignments[0].from_date) > getdate(start_date):
		# if no assignments found for the given period
		# or the assignment has started in the middle of the period
		# get the last one assigned before the period start date
		past_assignment = frappe.get_all(
			"Salary Structure Assignment",
			filters={"employee": employee, "docstatus": 1, "from_date": ["<", start_date]},
			fields=["*"],
			order_by="from_date desc",
			limit=1,
		)

		if past_assignment:
			assignments = past_assignment + assignments

	return assignments


def get_sal_slip_total_benefit_given(employee, payroll_period, component=False):
	total_given_benefit_amount = 0
	query = """
	select sum(sd.amount) as total_amount
	from `tabSalary Slip` ss, `tabSalary Detail` sd
	where ss.employee=%(employee)s
	and ss.docstatus = 1 and ss.name = sd.parent
	and sd.is_flexible_benefit = 1 and sd.parentfield = "earnings"
	and sd.parenttype = "Salary Slip"
	and (ss.start_date between %(start_date)s and %(end_date)s
		or ss.end_date between %(start_date)s and %(end_date)s
		or (ss.start_date < %(start_date)s and ss.end_date > %(end_date)s))
	"""

	if component:
		query += "and sd.salary_component = %(component)s"

	sum_of_given_benefit = frappe.db.sql(
		query,
		{
			"employee": employee,
			"start_date": payroll_period.start_date,
			"end_date": payroll_period.end_date,
			"component": component,
		},
		as_dict=True,
	)

	if sum_of_given_benefit and flt(sum_of_given_benefit[0].total_amount) > 0:
		total_given_benefit_amount = sum_of_given_benefit[0].total_amount
	return total_given_benefit_amount


def get_holiday_dates_for_employee(employee, start_date, end_date):
	"""return a list of holiday dates for the given employee between start_date and end_date"""
	# return only date
	holidays = get_holidays_for_employee(employee, start_date, end_date)

	return [cstr(h.holiday_date) for h in holidays]


def get_holidays_for_employee(employee, start_date, end_date, raise_exception=True, only_non_weekly=False):
	"""Get Holidays for a given employee

	`employee` (str)
	`start_date` (str or datetime)
	`end_date` (str or datetime)
	`raise_exception` (bool)
	`only_non_weekly` (bool)

	return: list of dicts with `holiday_date` and `description`
	"""
	holiday_list = get_holiday_list_for_employee(employee, raise_exception=raise_exception)

	if not holiday_list:
		return []

	filters = {"parent": holiday_list, "holiday_date": ("between", [start_date, end_date])}

	if only_non_weekly:
		filters["weekly_off"] = False

	holidays = frappe.get_all(
		"Holiday", fields=["description", "holiday_date"], filters=filters, order_by="holiday_date"
	)

	return holidays


@erpnext.allow_regional
def calculate_annual_eligible_hra_exemption(doc):
	# Don't delete this method, used for localization
	# Indian HRA Exemption Calculation
	return {}


@erpnext.allow_regional
def calculate_hra_exemption_for_period(doc):
	# Don't delete this method, used for localization
	# Indian HRA Exemption Calculation
	return {}


@erpnext.allow_regional
def calculate_tax_with_marginal_relief(tax_slab, tax_amount, annual_taxable_earning):
	# Don't delete this method, used for localization
	# Indian TDS Calculation
	return None


def get_previous_claimed_amount(employee, payroll_period, non_pro_rata=False, component=False):
	total_claimed_amount = 0
	query = """
	select sum(claimed_amount) as 'total_amount'
	from `tabEmployee Benefit Claim`
	where employee=%(employee)s
	and docstatus = 1
	and (claim_date between %(start_date)s and %(end_date)s)
	"""
	if non_pro_rata:
		query += "and pay_against_benefit_claim = 1"
	if component:
		query += "and earning_component = %(component)s"

	sum_of_claimed_amount = frappe.db.sql(
		query,
		{
			"employee": employee,
			"start_date": payroll_period.start_date,
			"end_date": payroll_period.end_date,
			"component": component,
		},
		as_dict=True,
	)
	if sum_of_claimed_amount and flt(sum_of_claimed_amount[0].total_amount) > 0:
		total_claimed_amount = sum_of_claimed_amount[0].total_amount
	return total_claimed_amount


def share_doc_with_approver(doc, user):
	if not user:
		return

	# if approver does not have permissions, share
	if not frappe.has_permission(doc=doc, ptype="submit", user=user):
		frappe.share.add_docshare(
			doc.doctype, doc.name, user, submit=1, flags={"ignore_share_permission": True}
		)

		frappe.msgprint(
			_("Shared document with the user {0} with 'Submit' permission").format(user), alert=True
		)

	# remove shared doc if approver changes
	doc_before_save = doc.get_doc_before_save()
	if doc_before_save:
		approvers = {
			"Leave Application": "leave_approver",
			"Expense Claim": "expense_approver",
			"Shift Request": "approver",
		}

		approver = approvers.get(doc.doctype)
		if doc_before_save.get(approver) != doc.get(approver):
			frappe.share.remove(doc.doctype, doc.name, doc_before_save.get(approver))


def validate_active_employee(employee, method=None):
	if isinstance(employee, dict | Document):
		employee = employee.get("employee")

	if employee and frappe.db.get_value("Employee", employee, "status") == "Inactive":
		frappe.throw(
			_("Transactions cannot be created for an Inactive Employee {0}.").format(
				get_link_to_form("Employee", employee)
			),
			InactiveEmployeeStatusError,
		)


def validate_loan_repay_from_salary(doc, method=None):
	if doc.applicant_type == "Employee" and doc.repay_from_salary:
		from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
			get_employee_currency,
		)

		if not doc.applicant:
			frappe.throw(_("Please select an Applicant"))

		if not doc.company:
			frappe.throw(_("Please select a Company"))

		employee_currency = get_employee_currency(doc.applicant)
		company_currency = erpnext.get_company_currency(doc.company)
		if employee_currency != company_currency:
			frappe.throw(
				_(
					"Loan cannot be repayed from salary for Employee {0} because salary is processed in currency {1}"
				).format(doc.applicant, employee_currency)
			)

	if not doc.is_term_loan and doc.repay_from_salary:
		frappe.throw(_("Repay From Salary can be selected only for term loans"))


def get_matching_queries(
	bank_account,
	company,
	transaction,
	document_types,
	exact_match,
	account_from_to=None,
	from_date=None,
	to_date=None,
	filter_by_reference_date=None,
	from_reference_date=None,
	to_reference_date=None,
	common_filters=None,
):
	"""Returns matching queries for Bank Reconciliation"""
	queries = []
	if transaction.withdrawal > 0:
		if "expense_claim" in document_types:
			ec_amount_matching = get_ec_matching_query(
				bank_account, company, exact_match, from_date, to_date, common_filters
			)
			queries.extend([ec_amount_matching])

	return queries


def get_ec_matching_query(
	bank_account, company, exact_match, from_date=None, to_date=None, common_filters=None
):
	# get matching Expense Claim query
	filters = []
	ec = qb.DocType("Expense Claim")

	mode_of_payments = [
		x["parent"]
		for x in frappe.db.get_all(
			"Mode of Payment Account", filters={"default_account": bank_account}, fields=["parent"]
		)
	]
	company_currency = get_company_currency(company)

	filters.append(ec.docstatus == 1)
	filters.append(ec.is_paid == 1)
	filters.append(ec.clearance_date.isnull())
	if mode_of_payments:
		filters.append(ec.mode_of_payment.isin(mode_of_payments))

	if common_filters:
		ref_rank = frappe.qb.terms.Case().when(ec.employee == common_filters.party, 1).else_(0) + 1

		if exact_match:
			filters.append(ec.total_amount_reimbursed == common_filters.amount)
		else:
			filters.append(ec.total_amount_reimbursed.gt(common_filters.amount))
	else:
		ref_rank = ConstantColumn(1)

	if from_date and to_date:
		filters.append(ec.posting_date[from_date:to_date])

	ec_query = (
		qb.from_(ec)
		.select(
			ref_rank.as_("rank"),
			ConstantColumn("Expense Claim").as_("doctype"),
			ec.name,
			ec.total_sanctioned_amount.as_("paid_amount"),
			ConstantColumn("").as_("reference_no"),
			ConstantColumn("").as_("reference_date"),
			ec.employee.as_("party"),
			ConstantColumn("Employee").as_("party_type"),
			ec.posting_date,
			ConstantColumn(company_currency).as_("currency"),
		)
		.where(Criterion.all(filters))
	)

	if from_date and to_date:
		ec_query = ec_query.orderby(ec.posting_date)

	return ec_query


def validate_bulk_tool_fields(
	self, fields: list, employees: list, from_date: str | None = None, to_date: str | None = None
) -> None:
	for d in fields:
		if not self.get(d):
			frappe.throw(_("{0} is required").format(_(self.meta.get_label(d))), title=_("Missing Field"))
	if self.get(from_date) and self.get(to_date):
		self.validate_from_to_dates(from_date, to_date)
	if not employees:
		frappe.throw(
			_("Please select at least one employee to perform this action."),
			title=_("No Employees Selected"),
		)


def notify_bulk_action_status(doctype: str, failure: list, success: list) -> None:
	frappe.clear_messages()

	msg = ""
	title = ""
	if failure:
		msg += _("Failed to create/submit {0} for employees:").format(doctype)
		msg += " " + comma_and(failure, False) + "<hr>"
		msg += (
			_("Check {0} for more details")
			.format("<a href='/app/List/Error Log?reference_doctype={0}'>{1}</a>")
			.format(doctype, _("Error Log"))
		)

		if success:
			title = _("Partial Success")
			msg += "<hr>"
		else:
			title = _("Creation Failed")
	else:
		title = _("Success")

	if success:
		msg += _("Successfully created {0} for employees:").format(doctype)
		msg += " " + comma_and(success, False)

	if failure:
		indicator = "orange" if success else "red"
	else:
		indicator = "green"

	frappe.msgprint(
		msg,
		indicator=indicator,
		title=title,
		is_minimizable=True,
	)


@frappe.whitelist()
def set_geolocation_from_coordinates(doc):
	if not frappe.db.get_single_value("HR Settings", "allow_geolocation_tracking"):
		return

	if not (doc.latitude and doc.longitude):
		return

	doc.geolocation = frappe.json.dumps(
		{
			"type": "FeatureCollection",
			"features": [
				{
					"type": "Feature",
					"properties": {},
					# geojson needs coordinates in reverse order: long, lat instead of lat, long
					"geometry": {"type": "Point", "coordinates": [doc.longitude, doc.latitude]},
				}
			],
		}
	)


def get_distance_between_coordinates(lat1, long1, lat2, long2):
	from math import asin, cos, pi, sqrt

	r = 6371
	p = pi / 180

	a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((long2 - long1) * p)) / 2
	return 2 * r * asin(sqrt(a)) * 1000


def check_app_permission():
	"""Check if user has permission to access the app (for showing the app on app screen)"""
	if frappe.session.user == "Administrator":
		return True

	if frappe.has_permission("Employee", ptype="read"):
		return True

	return False


def get_exact_month_diff(string_ed_date: DateTimeLikeObject, string_st_date: DateTimeLikeObject) -> int:
	"""Return the difference between given two dates in months."""
	ed_date = getdate(string_ed_date)
	st_date = getdate(string_st_date)
	diff = (ed_date.year - st_date.year) * 12 + ed_date.month - st_date.month

	# count the last month only if end date's day > start date's day
	# to handle cases like 16th Jul 2024 - 15th Jul 2025
	# where framework's month_diff will calculate diff as 13 months
	if ed_date.day >= st_date.day:
		diff += 1
	return diff


def get_semester_start(date):
	if date.month <= 6:
		return get_year_start(date)
	else:
		return add_months(get_year_start(date), 6)


def get_semester_end(date):
	if date.month > 6:
		return get_year_ending(date)
	else:
		return add_months(get_year_ending(date), -6)
