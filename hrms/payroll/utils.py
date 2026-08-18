import unicodedata
from datetime import date

import frappe
from frappe import _
from frappe.model import numeric_fieldtypes
from frappe.model.create_new import get_new_doc
from frappe.model.document import Document
from frappe.utils import (
	ceil,
	floor,
	flt,
	get_first_day,
	get_last_day,
	get_link_to_form,
	getdate,
	rounded,
)


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


SALARY_COMPONENT_VALUES = "salary_component_values"


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


BASE_PRECISION = 2
CTC_SOLVER_TOLERANCE = 0.01
CTC_SOLVER_BRACKET_EXPANSIONS = 20
CTC_SOLVER_MAX_ITERATIONS = 60


def solve_base_for_ctc(
	assignment, target_ctc: float, tolerance: float = CTC_SOLVER_TOLERANCE
) -> tuple[float, float]:
	"""Find the ``base`` that makes ``assignment`` cost ``target_ctc`` per year.

	Returns ``(base, achieved_ctc)``. ``achieved_ctc`` is always the CTC the
	returned base actually produces, which differs from ``target_ctc`` when the
	target is unreachable -- component rounding makes CTC a staircase, so most
	arbitrary targets have no exact base. Callers should store the achieved value
	rather than the requested one.

	CTC(base) is measured, not derived from the formulas. Two probes fit a line,
	which is solved and then **verified against the real evaluator**; a miss means
	the answer crossed a statutory cap (``min(BS, 15000) * 0.12``), a condition
	switching a component off, or a rounding step, and the search falls back to
	bisection. Parsing the formulas instead would require choosing a branch of
	``min`` before ``base`` is known, and would be a second evaluator to keep in
	step with the first.

	Where a plateau makes several bases produce the same CTC, the smallest is
	returned so that repeated recomputation is stable.
	"""
	from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
		PERIODS_PER_YEAR,
	)

	target_ctc = flt(target_ctc)
	if target_ctc <= 0:
		return 0.0, 0.0

	def ctc_at(base: float) -> float:
		assignment.base = flt(base, BASE_PRECISION)
		assignment.calculate_ctc_and_gross()
		return flt(assignment.ctc)

	frequency = frappe.get_cached_value("Salary Structure", assignment.salary_structure, "payroll_frequency")
	scale = target_ctc / PERIODS_PER_YEAR.get(frequency, 12)

	low_probe, high_probe = scale / 2, scale
	low_ctc, high_ctc = ctc_at(low_probe), ctc_at(high_probe)
	slope = (high_ctc - low_ctc) / (high_probe - low_probe)

	if slope <= 0:
		base = flt(low_probe, BASE_PRECISION)
		return base, ctc_at(base)

	intercept = low_ctc - slope * low_probe
	candidate = flt((target_ctc - intercept) / slope, BASE_PRECISION)
	if candidate >= 0:
		achieved = ctc_at(candidate)
		if abs(achieved - target_ctc) <= tolerance:
			return candidate, achieved

	return _bisect_base_for_ctc(ctc_at, target_ctc, scale, tolerance)


def _bisect_base_for_ctc(ctc_at, target_ctc: float, scale: float, tolerance: float) -> tuple[float, float]:
	low, high = 0.0, scale or 1.0

	for _expansion in range(CTC_SOLVER_BRACKET_EXPANSIONS):
		if ctc_at(high) >= target_ctc:
			break
		low, high = high, high * 2
	else:
		base = flt(high, BASE_PRECISION)
		return base, ctc_at(base)

	for _iteration in range(CTC_SOLVER_MAX_ITERATIONS):
		if high - low <= tolerance:
			break
		mid = (low + high) / 2
		if ctc_at(mid) < target_ctc:
			low = mid
		else:
			high = mid

	base = flt(high, BASE_PRECISION)
	return base, ctc_at(base)


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
