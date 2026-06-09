import unicodedata
from datetime import date

import frappe
from frappe import _
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


def get_component_eval_context(employee: str, ssa_as_dict: dict, abbr_map: dict) -> frappe._dict:
	"""Build the base evaluation context for salary component formulas.

	Merges component abbreviation defaults, SSA fields (base, variable) and
	employee fields so that formulas can reference any of them by name.
	SSA fields are applied before employee fields so that employee attributes
	(employment_type, date_of_joining, …) take precedence over any same-named
	SSA fields.  base and variable are pinned last to guarantee correct values.
	"""
	data = frappe._dict()
	data.update(abbr_map)
	data.update(ssa_as_dict)
	data.update(frappe.get_cached_doc("Employee", employee).as_dict())
	data["base"] = flt(ssa_as_dict.get("base") or 0)
	data["variable"] = flt(ssa_as_dict.get("variable") or 0)
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
	"""Safe eval for salary component conditions and formulas.

	Uses AST-based attribute checking instead of frappe.safe_eval to avoid
	recursion limit issues with deeply nested formulas.
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
