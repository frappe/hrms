# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	add_days,
	cstr,
	flt,
	format_datetime,
	formatdate,
	get_datetime,
	get_first_day,
	get_last_day,
	get_link_to_form,
	get_number_format_info,
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


class DuplicateDeclarationError(frappe.ValidationError):
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


def validate_dates(doc, from_date, to_date):
	date_of_joining, relieving_date = frappe.db.get_value(
		"Employee", doc.employee, ["date_of_joining", "relieving_date"]
	)
	if getdate(from_date) > getdate(to_date):
		frappe.throw(_("To date can not be less than from date"))
	elif getdate(from_date) > getdate(nowdate()):
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
		+ """ <b><a href="/app/Form/{0}/{1}">{1}</a></b>""".format(doc.doctype, overlap_doc)
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
			_("{0} already exists for employee {1} and period {2}").format(
				doctype, employee, payroll_period
			),
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
			filters={"to_date": add_days(getdate(), -1), "leave_type": ("in", leave_type)},
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

	for e_leave_type in e_leave_types:
		leave_allocations = get_leave_allocations(today, e_leave_type.name)

		for allocation in leave_allocations:
			if not allocation.leave_policy_assignment and not allocation.leave_policy:
				continue

			leave_policy = (
				allocation.leave_policy
				if allocation.leave_policy
				else frappe.db.get_value(
					"Leave Policy Assignment", allocation.leave_policy_assignment, ["leave_policy"]
				)
			)

			annual_allocation = frappe.db.get_value(
				"Leave Policy Detail",
				filters={"parent": leave_policy, "leave_type": e_leave_type.name},
				fieldname=["annual_allocation"],
			)
			date_of_joining = frappe.db.get_value("Employee", allocation.employee, "date_of_joining")

			from_date = allocation.from_date

			if e_leave_type.allocate_on_day == "Date of Joining":
				from_date = date_of_joining

			if check_effective_date(
				from_date, today, e_leave_type.earned_leave_frequency, e_leave_type.allocate_on_day
			):
				update_previous_leave_allocation(allocation, annual_allocation, e_leave_type, date_of_joining)


def update_previous_leave_allocation(allocation, annual_allocation, e_leave_type, date_of_joining):
	allocation = frappe.get_doc("Leave Allocation", allocation.name)
	annual_allocation = flt(annual_allocation, allocation.precision("total_leaves_allocated"))

	earned_leaves = get_monthly_earned_leave(
		date_of_joining,
		annual_allocation,
		e_leave_type.earned_leave_frequency,
		e_leave_type.rounding,
	)

	new_allocation = flt(allocation.total_leaves_allocated) + flt(earned_leaves)
	new_allocation_without_cf = flt(
		flt(allocation.get_existing_leave_count()) + flt(earned_leaves),
		allocation.precision("total_leaves_allocated"),
	)

	if new_allocation > e_leave_type.max_leaves_allowed and e_leave_type.max_leaves_allowed > 0:
		new_allocation = e_leave_type.max_leaves_allowed

	if (
		new_allocation != allocation.total_leaves_allocated
		# annual allocation as per policy should not be exceeded
		and new_allocation_without_cf <= annual_allocation
	):
		today_date = frappe.flags.current_date or getdate()

		allocation.db_set("total_leaves_allocated", new_allocation, update_modified=False)
		create_additional_leave_ledger_entry(allocation, earned_leaves, today_date)

		if e_leave_type.allocate_on_day:
			text = _(
				"Allocated {0} leave(s) via scheduler on {1} based on the 'Allocate on Day' option set to {2}"
			).format(
				frappe.bold(earned_leaves), frappe.bold(formatdate(today_date)), e_leave_type.allocate_on_day
			)

		allocation.add_comment(comment_type="Info", text=text)


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
				period_end_date = get_last_day(today_date)
				period_start_date = get_first_day(today_date)

			earned_leaves = calculate_pro_rated_leaves(
				earned_leaves, date_of_joining, period_start_date, period_end_date, is_earned_leave=True
			)

		earned_leaves = round_earned_leaves(earned_leaves, rounding)

	return earned_leaves


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
	return frappe.db.sql(
		"""select name, employee, from_date, to_date, leave_policy_assignment, leave_policy
		from `tabLeave Allocation`
		where
			%s between from_date and to_date and docstatus=1
			and leave_type=%s""",
		(date, leave_type),
		as_dict=1,
	)


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


def check_effective_date(from_date, today, frequency, allocate_on_day):
	from dateutil import relativedelta

	from_date = get_datetime(from_date)
	today = frappe.flags.current_date or get_datetime(today)
	rd = relativedelta.relativedelta(today, from_date)

	expected_date = {
		"First Day": get_first_day(today),
		"Last Day": get_last_day(today),
		"Date of Joining": from_date,
	}[allocate_on_day]

	if expected_date.day == today.day:
		if frequency == "Monthly":
			return True
		elif frequency == "Quarterly" and rd.months % 3:
			return True
		elif frequency == "Half-Yearly" and rd.months % 6:
			return True
		elif frequency == "Yearly" and rd.months % 12:
			return True

	return False


def get_salary_assignments(employee, payroll_period):
	start_date, end_date = frappe.db.get_value(
		"Payroll Period", payroll_period, ["start_date", "end_date"]
	)
	assignments = frappe.db.get_all(
		"Salary Structure Assignment",
		filters={"employee": employee, "docstatus": 1, "from_date": ["between", (start_date, end_date)]},
		fields=["*"],
		order_by="from_date",
	)

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


def get_holidays_for_employee(
	employee, start_date, end_date, raise_exception=True, only_non_weekly=False
):
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
			_("Shared with the user {0} with {1} access").format(user, frappe.bold("submit"), alert=True)
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
	if isinstance(employee, (dict, Document)):
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
):
	"""Returns matching queries for Bank Reconciliation"""
	queries = []
	if transaction.withdrawal > 0:
		if "expense_claim" in document_types:
			ec_amount_matching = get_ec_matching_query(
				bank_account, company, exact_match, from_date, to_date
			)
			queries.extend([ec_amount_matching])

	return queries


def get_ec_matching_query(bank_account, company, exact_match, from_date=None, to_date=None):
	# get matching Expense Claim query
	mode_of_payments = [
		x["parent"]
		for x in frappe.db.get_all(
			"Mode of Payment Account", filters={"default_account": bank_account}, fields=["parent"]
		)
	]

	mode_of_payments = "('" + "', '".join(mode_of_payments) + "' )"
	company_currency = get_company_currency(company)

	filter_by_date = ""
	if from_date and to_date:
		filter_by_date = f"AND posting_date BETWEEN '{from_date}' AND '{to_date}'"
		order_by = "posting_date"

	return f"""
		SELECT
			( CASE WHEN employee = %(party)s THEN 1 ELSE 0 END
			+ 1 ) AS rank,
			'Expense Claim' as doctype,
			name,
			total_sanctioned_amount as paid_amount,
			'' as reference_no,
			'' as reference_date,
			employee as party,
			'Employee' as party_type,
			posting_date,
			{company_currency!r} as currency
		FROM
			`tabExpense Claim`
		WHERE
			total_sanctioned_amount {'= %(amount)s' if exact_match else '> 0.0'}
			AND docstatus = 1
			AND is_paid = 1
			AND ifnull(clearance_date, '') = ""
			AND mode_of_payment in {mode_of_payments}
			{filter_by_date}
	"""
