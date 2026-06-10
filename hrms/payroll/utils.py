import unicodedata
from datetime import date

import frappe
from frappe import _
from frappe.utils import ceil, floor, get_first_day, get_last_day, get_link_to_form, getdate, rounded


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


def get_component_abbr_map() -> dict:
	"""Cached {salary_component_abbr: 0} map, seeded into the formula eval context
	so any component abbreviation referenced in a formula resolves (default 0).

	Cache key matches salary_slip.SALARY_COMPONENT_VALUES (shared entry, invalidated
	on Salary Component save)."""

	def _fetch_component_values():
		return {abbr: 0 for abbr in frappe.get_all("Salary Component", pluck="salary_component_abbr")}

	return frappe.cache().get_value("salary_component_values", generator=_fetch_component_values)


def get_component_eval_context(employee: str, ssa_as_dict: dict) -> frappe._dict:
	"""Build the base evaluation context for salary component formulas.

	Merges component abbreviation defaults, Salary Structure Assignment fields
	(base, variable, ...) and employee fields so that formulas can reference any
	of them by name.
	"""
	data = frappe._dict()
	data.update(get_component_abbr_map())
	data.update(ssa_as_dict)
	data.update(frappe.get_cached_doc("Employee", employee).as_dict())
	return data


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
