import frappe
from frappe.query_builder import Order
from frappe.utils import getdate


@frappe.whitelist()
def get_current_user_info() -> dict:
	current_user = frappe.session.user
	return frappe.db.get_value(
		"User", current_user, ["first_name", "full_name", "user_image"], as_dict=True
	)


@frappe.whitelist()
def get_current_employee_info() -> dict:
	current_user = frappe.session.user
	employee = frappe.db.get_value(
		"Employee",
		{"user_id": current_user},
		["name", "employee_name", "designation", "department", "company", "reports_to", "user_id"],
		as_dict=True,
	)
	return employee


# Leaves and Holidays
@frappe.whitelist()
def get_leave_applications(filters: dict) -> list[dict]:
	doctype = "Leave Application"
	leave_applications = frappe.get_list(
		"Leave Application",
		fields=[
			"name",
			"employee",
			"employee_name",
			"leave_type",
			"status",
			"from_date",
			"to_date",
			"half_day",
			"half_day_date",
			"description",
			"total_leave_days",
			"leave_balance",
			"leave_approver",
			"posting_date",
		],
		filters=filters,
		order_by="from_date desc",
	)

	for leave in leave_applications:
		leave.can_cancel = frappe.has_permission(doctype, "cancel", user=frappe.session.user)
		leave.can_delete = frappe.has_permission(doctype, "delete", user=frappe.session.user)

	return leave_applications


@frappe.whitelist()
def get_employee_leave_applications(employee: str) -> list[dict]:
	filters = {"employee": employee, "status": ["!=", "Cancelled"]}

	return get_leave_applications(filters)


@frappe.whitelist()
def get_team_leave_applications(employee: str, user_id: str) -> list[dict]:
	filters = {
		"employee": ["!=", employee],
		"leave_approver": user_id,
		"status": "Open",
		"docstatus": 0,
	}

	return get_leave_applications(filters)


@frappe.whitelist()
def get_leave_balance_map(employee: str) -> dict[str, dict[str, float]]:
	"""
	Returns a map of leave type and balance details like:
	{
	        'Casual Leave': {'allocated_leaves': 10.0, 'balance_leaves': 5.0},
	        'Earned Leave': {'allocated_leaves': 3.0, 'balance_leaves': 3.0},
	}
	"""
	from hrms.hr.doctype.leave_application.leave_application import get_leave_details

	date = getdate()
	leave_map = {}

	leave_details = get_leave_details(employee, date)
	allocation = leave_details["leave_allocation"]

	for leave_type, details in allocation.items():
		leave_map[leave_type] = {
			"allocated_leaves": details.get("total_leaves"),
			"balance_leaves": details.get("remaining_leaves"),
		}

	return leave_map


@frappe.whitelist()
def get_holidays_for_employee(employee: str) -> list[dict]:
	from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee

	holiday_list = get_holiday_list_for_employee(employee, raise_exception=False)
	if not holiday_list:
		return []

	Holiday = frappe.qb.DocType("Holiday")
	return (
		frappe.qb.from_(Holiday)
		.select(Holiday.name, Holiday.holiday_date, Holiday.description)
		.where((Holiday.parent == holiday_list) & (Holiday.weekly_off == 0))
		.orderby(Holiday.holiday_date, order=Order.asc)
	).run(as_dict=True)


@frappe.whitelist()
def get_leave_approval_details(employee: str) -> dict:
	leave_approver, department = frappe.get_cached_value(
		"Employee",
		employee,
		["leave_approver", "department"],
	)

	if not leave_approver and department:
		leave_approver = frappe.db.get_value(
			"Department Approver",
			{"parent": department, "parentfield": "leave_approvers", "idx": 1},
			"approver",
		)

	leave_approver_name = frappe.db.get_value("User", leave_approver, "full_name", cache=True)
	department_approvers = get_department_approvers(department)

	if leave_approver and leave_approver not in [approver.name for approver in department_approvers]:
		department_approvers.append({"name": leave_approver, "full_name": leave_approver_name})

	return dict(
		leave_approver=leave_approver,
		leave_approver_name=leave_approver_name,
		department_approvers=department_approvers,
		is_mandatory=frappe.db.get_single_value(
			"HR Settings", "leave_approver_mandatory_in_leave_application"
		),
	)


def get_department_approvers(department: str) -> list[str]:
	if not department:
		return []

	department_details = frappe.db.get_value("Department", department, ["lft", "rgt"], as_dict=True)
	departments = frappe.db.get_all(
		"Department",
		filters={
			"lft": ("<=", department_details.lft),
			"rgt": (">=", department_details.rgt),
			"disabled": 0,
		},
		pluck="name",
	)

	Approver = frappe.qb.DocType("Department Approver")
	User = frappe.qb.DocType("User")
	department_approvers = (
		frappe.qb.from_(User)
		.join(Approver)
		.on(Approver.approver == User.name)
		.select(User.name.as_("name"), User.full_name.as_("full_name"))
		.where((Approver.parent.isin(departments)) & (Approver.parentfield == "leave_approvers"))
	).run(as_dict=True)

	return department_approvers


@frappe.whitelist()
def get_leave_types(employee: str, date: str) -> list:
	from hrms.hr.doctype.leave_application.leave_application import get_leave_details

	date = date or getdate()

	leave_details = get_leave_details(employee, date)
	leave_types = list(leave_details["leave_allocation"].keys()) + leave_details["lwps"]

	return leave_types


# Expense Claims
@frappe.whitelist()
def get_expense_claim_summary(employee: str) -> dict:
	from frappe.query_builder.functions import Sum

	Claim = frappe.qb.DocType("Expense Claim")

	pending_claims_case = (
		frappe.qb.terms.Case()
		.when(Claim.approval_status == "Draft", Claim.total_claimed_amount)
		.else_(0)
	)
	sum_pending_claims = Sum(pending_claims_case).as_("total_pending_amount")

	approved_claims_case = (
		frappe.qb.terms.Case()
		.when(Claim.approval_status == "Approved", Claim.total_sanctioned_amount)
		.else_(0)
	)
	sum_approved_claims = Sum(approved_claims_case).as_("total_approved_amount")

	rejected_claims_case = (
		frappe.qb.terms.Case()
		.when(Claim.approval_status == "Rejected", Claim.total_sanctioned_amount)
		.else_(0)
	)
	sum_rejected_claims = Sum(rejected_claims_case).as_("total_rejected_amount")

	summary = (
		frappe.qb.from_(Claim)
		.select(
			sum_pending_claims,
			sum_approved_claims,
			sum_rejected_claims,
			Claim.company,
		)
		.where((Claim.docstatus != 2) & (Claim.employee == employee))
	).run(as_dict=True)[0]

	currency = frappe.db.get_value("Company", summary.company, "default_currency")
	symbol = frappe.db.get_value("Currency", currency, "symbol")
	summary["currency"] = symbol or currency

	return summary


# Form View APIs
@frappe.whitelist()
def get_doctype_fields(doctype: str) -> list[dict]:
	return frappe.get_meta(doctype).fields


@frappe.whitelist()
def get_link_field_options(doctype: str) -> list:
	fields = ["name as value"]
	title_field = frappe.db.get_value("DocType", doctype, "title_field", cache=1)

	if title_field:
		fields.append(f"{title_field} as label")

	link_options = frappe.get_all(doctype, fields=fields)
	return link_options
