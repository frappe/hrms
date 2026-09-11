import unicodedata
from datetime import date

import frappe
from frappe import _
from frappe.model import numeric_fieldtypes
from frappe.model.create_new import get_new_doc
from frappe.model.document import Document
from frappe.utils import ceil, floor, flt, get_first_day, get_last_day, get_link_to_form, getdate, rounded


def sanitize_expression(string: str | None = None) -> str | None:
	"""
	Removes leading and trailing whitespace and merges multiline strings into a single line.

	Args:
	    string (str, None): The string expression to be sanitized. Defaults to None.

	Returns:
	    str or None: The sanitized string expression or None if the input string is None.

	Example:
	    expression = "\r\n    gross_pay > 10000\n    "
	    sanitized_expr = sanitize_expression(expression)

	"""

	if not string:
		return None

	parts = string.strip().splitlines()
	string = " ".join(parts)

	return string


# Fields copied from the salary structure component row onto each evaluated row
# handed to the salary slip. The slip reads these to build/identify slip rows.
SALARY_COMPONENT_FLAGS = (
	"salary_component",
	"abbr",
	"amount_based_on_formula",
	"statistical_component",
	"accrual_component",
	"depends_on_payment_days",
	"do_not_include_in_total",
	"do_not_include_in_accounts",
	"is_tax_applicable",
	"is_flexible_benefit",
	"variable_based_on_taxable_salary",
	"exempted_from_income_tax",
	"deduct_full_tax_on_selected_payroll_date",
)


COMPONENT_PARENTFIELDS = ("earnings", "deductions", "employer_contributions")

COMPONENT_TYPE_TO_PARENTFIELD = {
	"Earning": "earnings",
	"Deduction": "deductions",
	"Employer Contribution": "employer_contributions",
}


COMPONENT_EVAL_GLOBALS = {
	"int": int,
	"float": float,
	"long": int,
	"round": round,
	"rounded": rounded,
	"date": date,
	"getdate": getdate,
	"get_first_day": get_first_day,
	"get_last_day": get_last_day,
	"ceil": ceil,
	"floor": floor,
	"min": min,
	"max": max,
}


# cache keys
HOLIDAYS_BETWEEN_DATES = "holidays_between_dates"
LEAVE_TYPE_MAP = "leave_type_map"
SALARY_COMPONENT_VALUES = "salary_component_values"
TAX_COMPONENTS_BY_COMPANY = "tax_components_by_company"


def payable_earnings(rows) -> float:
	"""Per-cycle gross: earnings that are actually paid, which is what the salary
	slip reports as gross_pay. Statistical rows exist only to feed other formulas,
	and do_not_include_in_total rows are a cost to the company rather than pay."""
	return sum(
		flt(row.default_amount)
		for row in rows
		if not row.statistical_component and not row.do_not_include_in_total
	)


def get_component_abbr_map() -> dict:
	"""Cached {salary_component_abbr: 0} map, seeded into the formula eval context
	so any component abbreviation referenced in a formula resolves (default 0).

	Invalidated on Salary Component save."""

	def _fetch_component_values():
		return {abbr: 0 for abbr in frappe.get_all("Salary Component", pluck="salary_component_abbr")}

	return frappe.cache().get_value(SALARY_COMPONENT_VALUES, generator=_fetch_component_values)


def get_salary_slip_field_defaults() -> dict:
	defaults = get_new_doc("Salary Slip", as_dict=True)

	for df in frappe.get_meta("Salary Slip").fields:
		if df.fieldtype in numeric_fieldtypes and defaults.get(df.fieldname) is None:
			defaults[df.fieldname] = 0

	return defaults


def get_component_eval_context(employee: "str | Document | None", ssa_as_dict: dict) -> frappe._dict:
	"""Build the base evaluation context for salary component formulas.

	Merges component abbreviation defaults, Salary Structure Assignment fields
	(base, variable, ...) and employee fields so that formulas can reference any
	of them by name.

	``employee`` may be an unsaved Employee document, so a prospective package can
	be evaluated for someone with no Employee record yet.
	"""
	data = frappe._dict()
	data.update(get_component_abbr_map())
	data.update(get_salary_slip_field_defaults())
	data.update(ssa_as_dict)

	if employee:
		employee_doc = (
			employee if isinstance(employee, Document) else frappe.get_cached_doc("Employee", employee)
		)
		data.update(employee_doc.as_dict())

	return data


def _check_attributes(code: str) -> None:
	import ast

	from frappe.utils.safe_exec import UNSAFE_ATTRIBUTES

	unsafe_attrs = set(UNSAFE_ATTRIBUTES).union(["__"]) - {"format"}

	for attribute in unsafe_attrs:
		if attribute in code:
			raise SyntaxError(f'Illegal rule {frappe.bold(code)}. Cannot use "{attribute}"')

	BLOCKED_NODES = (ast.NamedExpr, ast.Lambda)

	tree = ast.parse(code, mode="eval")
	for node in ast.walk(tree):
		if isinstance(node, BLOCKED_NODES):
			raise SyntaxError(f"Operation not allowed: line {node.lineno} column {node.col_offset}")
		if isinstance(node, ast.Attribute) and isinstance(node.attr, str) and node.attr in UNSAFE_ATTRIBUTES:
			raise SyntaxError(f'Illegal rule {frappe.bold(code)}. Cannot use "{node.attr}"')


def _safe_eval(code: str, eval_globals: dict | None = None, eval_locals: dict | None = None):
	"""Safe eval for **trusted** salary component conditions and formulas only.

	Uses AST-based attribute checking instead of frappe.safe_eval to avoid
	recursion limit issues with the large/deeply-nested formulas some countries'
	payroll needs. It is a lighter (denylist-based) sandbox than frappe.safe_eval,
	so it is safe only for admin-authored salary-structure formulas, not arbitrary
	or end-user input. For anything else, use frappe.safe_eval.
	"""
	code = unicodedata.normalize("NFKC", code)

	_check_attributes(code)

	whitelisted_globals = {"int": int, "float": float, "long": int, "round": round}
	if not eval_globals:
		eval_globals = {}

	eval_globals["__builtins__"] = {}
	eval_globals.update(whitelisted_globals)
	return eval(code, eval_globals, eval_locals)  # nosemgrep


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


@frappe.whitelist()
def get_payroll_settings_for_payment_days() -> dict:
	return frappe.get_cached_value(
		"Payroll Settings",
		None,
		[
			"payroll_based_on",
			"consider_unmarked_attendance_as",
			"include_holidays_in_total_working_days",
			"consider_marked_attendance_on_holidays",
		],
		as_dict=True,
	)


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
			"do_not_include_in_accounts",
			"is_tax_applicable",
			"is_flexible_benefit",
			"variable_based_on_taxable_salary",
			"accrual_component",
			"exempted_from_income_tax",
		),
		as_dict=1,
		cache=True,
	)
