# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, date_diff, flt, get_link_to_form, getdate

from hrms.payroll.doctype.payroll_period.payroll_period import get_payroll_period
from hrms.payroll.doctype.salary_structure.salary_structure import validate_max_benefit_for_flexible_benefit
from hrms.payroll.utils import (
	COMPONENT_EVAL_GLOBALS,
	_safe_eval,
	get_component_eval_context,
	sanitize_expression,
	throw_error_message,
)

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

PERIODS_PER_YEAR = {
	"Monthly": 12,
	"Fortnightly": 26,
	"Bimonthly": 24,
	"Weekly": 52,
	"Daily": 365,
}


class DuplicateAssignment(frappe.ValidationError):
	pass


class SalaryStructureAssignment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.payroll.doctype.employee_benefit_detail.employee_benefit_detail import EmployeeBenefitDetail
		from hrms.payroll.doctype.employee_cost_center.employee_cost_center import EmployeeCostCenter

		amended_from: DF.Link | None
		annual_gross_earning: DF.Currency
		base: DF.Currency
		company: DF.Link
		ctc: DF.Currency
		currency: DF.Link
		department: DF.Link | None
		designation: DF.Link | None
		employee: DF.Link
		employee_benefits: DF.Table[EmployeeBenefitDetail]
		employee_name: DF.Data | None
		from_date: DF.Date
		grade: DF.Link | None
		income_tax_slab: DF.Link | None
		leave_encashment_amount_per_day: DF.Currency
		max_benefits: DF.Currency
		payroll_cost_centers: DF.Table[EmployeeCostCenter]
		payroll_payable_account: DF.Link | None
		salary_structure: DF.Link
		tax_deducted_till_date: DF.Currency
		taxable_earnings_till_date: DF.Currency
		variable: DF.Currency
	# end: auto-generated types

	def validate(self):
		self.validate_dates()
		self.validate_company()
		self.validate_income_tax_slab()
		self.set_payroll_payable_account()
		validate_max_benefit_for_flexible_benefit(self.employee_benefits, self.max_benefits)

		if not self.get("payroll_cost_centers"):
			self.set_payroll_cost_centers()

		self.validate_cost_centers()
		self.warn_about_missing_opening_entries()
		self.calculate_ctc_and_gross()

	def on_update_after_submit(self):
		self.validate_cost_centers()

	def validate_dates(self):
		joining_date, relieving_date = frappe.db.get_value(
			"Employee", self.employee, ["date_of_joining", "relieving_date"]
		)

		if self.from_date:
			if frappe.db.exists(
				"Salary Structure Assignment",
				{"employee": self.employee, "from_date": self.from_date, "docstatus": 1},
			):
				frappe.throw(
					_("Salary Structure Assignment for Employee already exists"), DuplicateAssignment
				)

			if joining_date and getdate(self.from_date) < joining_date:
				frappe.throw(
					_("From Date {0} cannot be before employee's joining Date {1}").format(
						self.from_date, joining_date
					)
				)

			# flag - old_employee is for migrating the old employees data via patch
			if relieving_date and getdate(self.from_date) > relieving_date and not self.flags.old_employee:
				frappe.throw(
					_("From Date {0} cannot be after employee's relieving Date {1}").format(
						self.from_date, relieving_date
					)
				)

	def validate_company(self):
		salary_structure_company = frappe.db.get_value(
			"Salary Structure", self.salary_structure, "company", cache=True
		)
		if self.company != salary_structure_company:
			frappe.throw(
				_("Salary Structure {0} does not belong to company {1}").format(
					frappe.bold(self.salary_structure), frappe.bold(self.company)
				)
			)

	def validate_income_tax_slab(self):
		tax_component = get_tax_component(self.salary_structure)
		if tax_component and not self.income_tax_slab:
			frappe.throw(
				_(
					"Income Tax Slab is mandatory since the Salary Structure {0} has a tax component {1}"
				).format(
					get_link_to_form("Salary Structure", self.salary_structure), frappe.bold(tax_component)
				),
				exc=frappe.MandatoryError,
				title=_("Missing Mandatory Field"),
			)

		if not self.income_tax_slab:
			return

		income_tax_slab_currency = frappe.db.get_value("Income Tax Slab", self.income_tax_slab, "currency")
		if self.currency != income_tax_slab_currency:
			frappe.throw(
				_("Currency of selected Income Tax Slab should be {0} instead of {1}").format(
					self.currency, income_tax_slab_currency
				)
			)

	def set_payroll_payable_account(self):
		if not self.payroll_payable_account:
			payroll_payable_account = frappe.db.get_value(
				"Company", self.company, "default_payroll_payable_account"
			)
			if not payroll_payable_account:
				payroll_payable_account = frappe.db.get_value(
					"Account",
					{
						"account_name": _("Payroll Payable"),
						"company": self.company,
						"account_currency": frappe.db.get_value("Company", self.company, "default_currency"),
						"is_group": 0,
					},
				)
			self.payroll_payable_account = payroll_payable_account

	@frappe.whitelist()
	def set_payroll_cost_centers(self) -> None:
		self.payroll_cost_centers = []
		default_payroll_cost_center = self.get_payroll_cost_center()
		if default_payroll_cost_center:
			self.append(
				"payroll_cost_centers", {"cost_center": default_payroll_cost_center, "percentage": 100}
			)

	def get_payroll_cost_center(self):
		payroll_cost_center = frappe.db.get_value("Employee", self.employee, "payroll_cost_center")
		if not payroll_cost_center and self.department:
			payroll_cost_center = frappe.db.get_value("Department", self.department, "payroll_cost_center")

		return payroll_cost_center

	def validate_cost_centers(self):
		if not self.get("payroll_cost_centers"):
			return

		total_percentage = 0
		for entry in self.payroll_cost_centers:
			company = frappe.db.get_value("Cost Center", entry.cost_center, "company")
			if company != self.company:
				frappe.throw(
					_("Row {0}: Cost Center {1} does not belong to Company {2}").format(
						entry.idx, frappe.bold(entry.cost_center), frappe.bold(self.company)
					),
					title=_("Invalid Cost Center"),
				)

			total_percentage += flt(entry.percentage)

		if total_percentage != 100:
			frappe.throw(_("Total percentage against cost centers should be 100"))

	def warn_about_missing_opening_entries(self):
		if (
			self.are_opening_entries_required()
			and not self.taxable_earnings_till_date
			and not self.tax_deducted_till_date
		):
			msg = _(
				"Please specify {0} and {1} (if any), for the correct tax calculation in future salary slips."
			).format(
				frappe.bold(_("Taxable Earnings Till Date")),
				frappe.bold(_("Tax Deducted Till Date")),
			)
			frappe.msgprint(
				msg,
				indicator="orange",
				title=_("Missing Opening Entries"),
			)

	def get_evaluated_components(self) -> frappe._dict:
		"""Evaluate all salary structure components for this assignment and return
		fully-evaluated rows the salary slip can consume directly.

		Earnings, deductions and employer contributions are evaluated in one
		shared pass (so a deduction formula can reference an earning abbr), each
		row carrying its full-cycle ``default_amount`` plus the flags the slip
		needs. This is period-independent: the (period-dependent) timesheet wage
		is built by the salary slip itself, not here. The slip consumes
		``default_amount`` directly and applies payment-days proration / tax on
		top (it re-evaluates each formula once against its prorated context for
		the actual ``amount``).
		"""
		_data, rows_by_type = self._evaluate_all_components()

		return frappe._dict(
			earnings=rows_by_type["earnings"],
			deductions=rows_by_type["deductions"],
			employer_contributions=rows_by_type["employer_contributions"],
		)

	def get_timesheet_config(self) -> frappe._dict:
		"""Lightweight read of the linked structure's timesheet settings, needed
		by the slip early (before component evaluation runs)."""
		ss = (
			frappe.get_cached_value(
				"Salary Structure",
				self.salary_structure,
				["salary_slip_based_on_timesheet", "hour_rate", "salary_component"],
				as_dict=True,
			)
			or frappe._dict()
		)
		return frappe._dict(
			based_on_timesheet=cint(ss.salary_slip_based_on_timesheet),
			hour_rate=flt(ss.hour_rate),
			timesheet_component=ss.salary_component,
		)

	def calculate_ctc_and_gross(self) -> None:
		if not self.base or not self.salary_structure:
			self.annual_gross_earning = 0
			self.ctc = 0
			return

		salary_structure = frappe.get_cached_doc("Salary Structure", self.salary_structure)
		periods = PERIODS_PER_YEAR.get(salary_structure.payroll_frequency, 12)

		data, rows_by_type = self._evaluate_all_components()

		# Reuse the per-period gross already computed in the eval context: payable
		# earnings only (excludes statistical and do_not_include_in_total), matching
		# the salary slip's gross_pay.
		gross_per_period = flt(data.get("gross_pay"))

		# CTC also includes costs that are part of CTC but not payable: do_not_include_in_total
		# earnings (shown on the slip, excluded from gross) and employer contributions (off-slip).
		non_payable_earnings_per_period = sum(
			flt(r.default_amount)
			for r in rows_by_type["earnings"]
			if not r.statistical_component and r.do_not_include_in_total
		)
		employer_per_period = sum(
			flt(r.default_amount)
			for r in rows_by_type["employer_contributions"]
			if not r.statistical_component
		)

		self.annual_gross_earning = flt(gross_per_period * periods, self.precision("annual_gross_earning"))
		self.ctc = flt(
			(gross_per_period + non_payable_earnings_per_period + employer_per_period) * periods,
			self.precision("ctc"),
		)

	def _evaluate_all_components(self) -> tuple[frappe._dict, dict]:
		"""Single shared-context pass over earnings -> deductions ->
		employer_contributions. Returns the final context and evaluated rows by
		type. Does not mutate the cached salary structure doc."""
		salary_structure = frappe.get_cached_doc("Salary Structure", self.salary_structure)
		data = self._get_component_eval_context()

		rows_by_type = {}
		rows_by_type["earnings"] = self._evaluate_component_table(
			salary_structure.get("earnings") or [], data
		)

		# Expose full-cycle gross_pay so deduction / employer-contribution formulas can
		# reference it (e.g. PF, ESI), mirroring how the salary slip sets gross_pay after
		# earnings and before deductions.
		data["gross_pay"] = sum(
			flt(r.default_amount)
			for r in rows_by_type["earnings"]
			if not r.statistical_component and not r.do_not_include_in_total
		)

		rows_by_type["deductions"] = self._evaluate_component_table(
			salary_structure.get("deductions") or [], data
		)
		rows_by_type["employer_contributions"] = self._evaluate_component_table(
			salary_structure.get("employer_contributions") or [], data
		)
		return data, rows_by_type

	def _get_component_eval_context(self) -> frappe._dict:
		from hrms.payroll.doctype.payroll_entry.payroll_entry import get_start_end_dates

		data = get_component_eval_context(self.employee, self.as_dict())

		# The SSA has no salary slip, so formulas referencing slip period fields (e.g.
		# start_date) would raise NameError. Seed a full cycle -- the period containing
		# from_date -- with no LWP/absence so proration-based formulas yield full-cycle
		# values (payment_days == total_working_days, ratio 1).
		frequency = frappe.get_cached_value("Salary Structure", self.salary_structure, "payroll_frequency")
		dates = get_start_end_dates(frequency, self.from_date, self.company)
		period_days = date_diff(dates.end_date, dates.start_date) + 1
		data.start_date = dates.start_date
		data.end_date = dates.end_date
		data.payment_days = period_days
		data.total_working_days = period_days
		data.leave_without_pay = 0
		data.absent_days = 0
		return data

	def _evaluate_component_table(self, rows, data: frappe._dict) -> list:
		"""Evaluate one component table against the shared ``data`` (mutating it
		with each component's full-cycle amount). Returns fresh ``frappe._dict``
		rows (cache-safe copies). Raises a clear error on a bad formula/condition.
		Rows whose condition is falsey are skipped (not added to the slip)."""
		evaluated_components = []
		for struct_row in rows:
			condition = sanitize_expression(struct_row.condition)
			formula = sanitize_expression(struct_row.formula)
			amount = flt(struct_row.amount)

			try:
				if condition and not _safe_eval(condition, COMPONENT_EVAL_GLOBALS.copy(), data):
					continue
				if struct_row.amount_based_on_formula and formula:
					default_amount = flt(
						_safe_eval(formula, COMPONENT_EVAL_GLOBALS.copy(), data),
						struct_row.precision("amount"),
					)
				else:
					default_amount = amount
			except NameError as ne:
				throw_error_message(
					struct_row,
					ne,
					title=_("Name error"),
					description=_("This error can be due to missing or deleted field."),
				)
			except SyntaxError as se:
				throw_error_message(
					struct_row,
					se,
					title=_("Syntax error"),
					description=_("This error can be due to invalid syntax."),
				)
			except Exception as exc:
				throw_error_message(
					struct_row,
					exc,
					title=_("Error in formula or condition"),
					description=_("This error can be due to invalid formula or condition."),
				)
				raise

			data[struct_row.abbr] = default_amount

			evaluated_component_row = frappe._dict(
				default_amount=default_amount,
				amount=amount,
				condition=condition,
				formula=formula,
				precision=struct_row.precision("amount"),
			)
			for field in SALARY_COMPONENT_FLAGS:
				evaluated_component_row[field] = struct_row.get(field)
			evaluated_components.append(evaluated_component_row)

		return evaluated_components

	@frappe.whitelist()
	def are_opening_entries_required(self) -> bool:
		if not get_tax_component(self.salary_structure):
			return False

		payroll_period = get_payroll_period(self.from_date, self.from_date, self.company)
		if payroll_period and getdate(self.from_date) <= getdate(payroll_period.start_date):
			return False

		return True


def get_assigned_salary_structure(employee, on_date):
	if not employee or not on_date:
		return None

	salary_structure_assignment = frappe.qb.DocType("Salary Structure Assignment")

	query = (
		frappe.qb.from_(salary_structure_assignment)
		.select(salary_structure_assignment.salary_structure)
		.where(salary_structure_assignment.employee == employee)
		.where(salary_structure_assignment.docstatus == 1)
		.where(on_date >= salary_structure_assignment.from_date)
		.orderby(salary_structure_assignment.from_date, order=frappe.qb.desc)
		.limit(1)
	)

	result = query.run()
	return result[0][0] if result else None


@frappe.whitelist()
def get_employee_currency(employee: str) -> str:
	frappe.has_permission("Employee", "read", employee, throw=True)
	employee_currency = frappe.db.get_value("Salary Structure Assignment", {"employee": employee}, "currency")
	if not employee_currency:
		frappe.throw(
			_("There is no Salary Structure assigned to {0}. First assign a Salary Structure.").format(
				employee
			)
		)
	return employee_currency


def get_tax_component(salary_structure: str) -> str | None:
	salary_structure = frappe.get_cached_doc("Salary Structure", salary_structure)
	for d in salary_structure.deductions:
		if cint(d.variable_based_on_taxable_salary) and not d.formula and not flt(d.amount):
			return d.salary_component
	return None
