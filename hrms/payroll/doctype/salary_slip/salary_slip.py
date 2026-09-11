# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import datetime
from functools import cached_property

import frappe
from frappe import _, msgprint
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.query_builder import Order
from frappe.query_builder.functions import Count, Sum
from frappe.utils import (
	add_days,
	ceil,
	cint,
	cstr,
	date_diff,
	floor,
	flt,
	format_datetime,
	formatdate,
	get_first_day,
	get_last_day,
	get_link_to_form,
	getdate,
	money_in_words,
	rounded,
)
from frappe.utils.background_jobs import enqueue

import erpnext
from erpnext.accounts.utils import get_fiscal_year
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
from erpnext.utilities.transaction_base import TransactionBase

import hrms
from hrms.hr.utils import validate_active_employee
from hrms.payroll.doctype.additional_salary.additional_salary import get_additional_salaries
from hrms.payroll.doctype.employee_benefit_ledger.employee_benefit_ledger import (
	create_employee_benefit_ledger_entry,
	delete_employee_benefit_ledger_entry,
)
from hrms.payroll.doctype.income_tax_slab.income_tax_slab import calculate_tax_by_tax_slab
from hrms.payroll.doctype.payroll_entry.payroll_entry import get_salary_withholdings, get_start_end_dates
from hrms.payroll.doctype.payroll_period.payroll_period import (
	get_payroll_period,
	get_period_factor,
)
from hrms.payroll.doctype.salary_slip.salary_slip_benefits import BenefitsMixin
from hrms.payroll.doctype.salary_slip.salary_slip_exemptions import ExemptionsMixin
from hrms.payroll.doctype.salary_slip.salary_slip_income_tax import IncomeTaxMixin
from hrms.payroll.doctype.salary_slip.salary_slip_leave import LeaveMixin
from hrms.payroll.doctype.salary_slip.salary_slip_loan_utils import (
	cancel_loan_repayment_entry,
	make_loan_repayment_entry,
	process_loan_interest_accrual_and_demand,
	set_loan_repayment,
)
from hrms.payroll.doctype.salary_slip.salary_slip_payment_days import PaymentDaysMixin
from hrms.payroll.doctype.salary_slip.salary_slip_taxable_income import TaxableIncomeMixin
from hrms.payroll.doctype.salary_slip.salary_slip_timesheet import TimesheetMixin
from hrms.payroll.doctype.salary_slip.salary_slip_totals import TotalsMixin
from hrms.payroll.doctype.salary_slip.salary_slip_utils import (
	SystemFormattedDate,
	SystemFormattedDatetime,
	format_dates_in_system_format,
	generate_password_for_pdf,
	get_benefits_details_parent,
	get_lwp_or_ppl_for_date_range,
	get_payroll_payable_account,
	verify_lwp_days_corrected,
)
from hrms.payroll.utils import (
	COMPONENT_EVAL_GLOBALS,
	COMPONENT_PARENTFIELDS,
	HOLIDAYS_BETWEEN_DATES,
	LEAVE_TYPE_MAP,
	SALARY_COMPONENT_FLAGS,
	SALARY_COMPONENT_VALUES,
	TAX_COMPONENTS_BY_COMPANY,
	_safe_eval,
	get_component_eval_context,
	get_salary_component_data,
	payable_earnings,
	sanitize_expression,
	throw_error_message,
)
from hrms.utils.holiday_list import get_holiday_dates_between

CACHED_PROPERTIES = ("evaluated_components", "remaining_sub_periods")


class SalarySlip(
	PaymentDaysMixin,
	LeaveMixin,
	TimesheetMixin,
	BenefitsMixin,
	TaxableIncomeMixin,
	ExemptionsMixin,
	IncomeTaxMixin,
	TotalsMixin,
	TransactionBase,
):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.payroll.doctype.employee_benefit_detail.employee_benefit_detail import EmployeeBenefitDetail
		from hrms.payroll.doctype.salary_detail.salary_detail import SalaryDetail
		from hrms.payroll.doctype.salary_slip_leave.salary_slip_leave import SalarySlipLeave
		from hrms.payroll.doctype.salary_slip_timesheet.salary_slip_timesheet import SalarySlipTimesheet

		absent_days: DF.Float
		accrued_benefits: DF.Table[EmployeeBenefitDetail]
		amended_from: DF.Link | None
		annual_taxable_amount: DF.Currency
		bank_account_no: DF.Data | None
		bank_name: DF.Data | None
		base_gross_pay: DF.Currency
		base_gross_year_to_date: DF.Currency
		base_hour_rate: DF.Currency
		base_month_to_date: DF.Currency
		base_net_pay: DF.Currency
		base_rounded_total: DF.Currency
		base_total_deduction: DF.Currency
		base_total_in_words: DF.Data | None
		base_year_to_date: DF.Currency
		branch: DF.Link | None
		company: DF.Link
		ctc: DF.Currency
		currency: DF.Link
		current_month_income_tax: DF.Currency
		current_payroll_period: DF.Link | None
		deduct_tax_for_unsubmitted_tax_exemption_proof: DF.Check
		deductions: DF.Table[SalaryDetail]
		deductions_before_tax_calculation: DF.Currency
		department: DF.Link | None
		designation: DF.Link | None
		earnings: DF.Table[SalaryDetail]
		employee: DF.Link
		employee_name: DF.ReadOnly
		employer_contributions: DF.Table[SalaryDetail]
		end_date: DF.Date | None
		exchange_rate: DF.Float
		future_income_tax_deductions: DF.Currency
		gross_pay: DF.Currency
		gross_year_to_date: DF.Currency
		hour_rate: DF.Currency
		income_from_other_sources: DF.Currency
		income_tax_deducted_till_date: DF.Currency
		journal_entry: DF.Link | None
		leave_details: DF.Table[SalarySlipLeave]
		leave_without_pay: DF.Float
		letter_head: DF.Link | None
		mode_of_payment: DF.Literal[None]
		month_to_date: DF.Currency
		net_pay: DF.Currency
		non_taxable_earnings: DF.Currency
		payment_days: DF.Float
		payroll_entry: DF.Link | None
		payroll_frequency: DF.Literal["", "Monthly", "Fortnightly", "Bimonthly", "Weekly", "Daily"]
		posting_date: DF.Date
		rounded_total: DF.Currency
		salary_slip_based_on_timesheet: DF.Check
		salary_structure: DF.Link
		salary_withholding: DF.Link | None
		salary_withholding_cycle: DF.Data | None
		standard_tax_exemption_amount: DF.Currency
		start_date: DF.Date | None
		status: DF.Literal["Draft", "Submitted", "Cancelled", "Withheld"]
		tax_exemption_declaration: DF.Currency
		timesheets: DF.Table[SalarySlipTimesheet]
		total_deduction: DF.Currency
		total_earnings: DF.Currency
		total_in_words: DF.Data | None
		total_income_tax: DF.Currency
		total_working_days: DF.Float
		total_working_hours: DF.Float
		unmarked_days: DF.Float
		year_to_date: DF.Currency
	# end: auto-generated types

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.whitelisted_globals = COMPONENT_EVAL_GLOBALS.copy()

	@property
	def default_series(self):
		return f"Sal Slip/{self.employee}/.#####"

	def autoname(self):
		if not self.has_custom_naming_series:
			self.name = make_autoname(self.default_series)

	@property
	def has_custom_naming_series(self):
		return frappe.db.exists(
			"Property Setter",
			{
				"doc_type": "Salary Slip",
				"property": "autoname",
			},
		)

	@property
	def joining_date(self):
		return frappe.get_cached_value(
			"Employee",
			self.employee,
			"date_of_joining",
		)

	@property
	def relieving_date(self):
		return frappe.get_cached_value(
			"Employee",
			self.employee,
			"relieving_date",
		)

	@property
	def payroll_period(self):
		return get_payroll_period(self.start_date, self.end_date, self.company)

	@property
	def actual_start_date(self):
		if self.joining_date and getdate(self.start_date) < self.joining_date <= getdate(self.end_date):
			return self.joining_date

		return self.start_date

	@property
	def actual_end_date(self):
		if self.relieving_date and getdate(self.start_date) <= self.relieving_date < getdate(self.end_date):
			return self.relieving_date

		return self.end_date

	def clear_cached_properties(self) -> None:
		for name in CACHED_PROPERTIES:
			self.__dict__.pop(name, None)

	def load_from_db(self):
		super().load_from_db()
		self.clear_cached_properties()

	def validate(self):
		self.check_salary_withholding()
		self.status = self.get_status()
		validate_active_employee(self.employee)
		self.validate_dates()
		self.check_existing()

		if self.payroll_frequency:
			self.get_date_details()

		if not (len(self.get("earnings")) or len(self.get("deductions"))):
			# get details from salary structure
			self.get_emp_and_working_day_details()
		else:
			self.get_working_days_details(lwp=self.leave_without_pay)

		self.set_salary_structure_assignment()
		self.calculate_net_pay()
		self.compute_year_to_date()
		self.compute_month_to_date()
		self.compute_component_wise_year_to_date()

		self.add_leave_balances()

		max_working_hours = frappe.db.get_single_value(
			"Payroll Settings", "max_working_hours_against_timesheet"
		)
		if max_working_hours:
			if self.salary_slip_based_on_timesheet and (self.total_working_hours > int(max_working_hours)):
				frappe.msgprint(
					_("Total working hours should not be greater than max working hours {0}").format(
						max_working_hours
					),
					alert=True,
				)

		if self.payroll_period and not self.current_payroll_period:
			self.current_payroll_period = self.payroll_period.name

	def check_salary_withholding(self):
		withholding = get_salary_withholdings(self.start_date, self.end_date, self.employee)
		if withholding:
			self.salary_withholding = withholding[0].salary_withholding
			self.salary_withholding_cycle = withholding[0].salary_withholding_cycle
		else:
			self.salary_withholding = None

	def on_update(self):
		self.publish_update()

	def on_submit(self):
		if self.net_pay < 0:
			frappe.throw(_("Net Pay cannot be less than 0"))
		else:
			self.set_status()
			self.update_status(self.name)

			make_loan_repayment_entry(self)

			if not frappe.flags.via_payroll_entry and not frappe.flags.in_patch:
				email_salary_slip = cint(
					frappe.db.get_single_value("Payroll Settings", "email_salary_slip_to_employee")
				)
				if email_salary_slip:
					self.email_salary_slip()

		self.update_payment_status_for_gratuity_and_leave_encashment()
		self.create_benefits_ledger_entry()

	def update_payment_status_for_gratuity_and_leave_encashment(self):
		additional_salary_docs = frappe.db.get_all(
			"Additional Salary",
			filters={
				"payroll_date": ("between", [self.start_date, self.end_date]),
				"employee": self.employee,
				"ref_doctype": ["in", ["Gratuity", "Leave Encashment"]],
				"docstatus": 1,
			},
			fields=["ref_doctype", "ref_docname", "name"],
		)

		if not additional_salary_docs:
			return

		status = "Paid" if self.docstatus == 1 else "Unpaid"
		earnings = {entry.additional_salary for entry in self.earnings}

		for additional_salary in additional_salary_docs:
			if additional_salary.name in earnings:
				frappe.db.set_value(
					additional_salary.ref_doctype, additional_salary.ref_docname, "status", status
				)

	def on_cancel(self):
		self.set_status()
		self.update_status()
		self.update_payment_status_for_gratuity_and_leave_encashment()
		delete_employee_benefit_ledger_entry("salary_slip", self.name)

		cancel_loan_repayment_entry(self)
		self.publish_update()

	def publish_update(self):
		employee_user = frappe.db.get_value("Employee", self.employee, "user_id", cache=True)
		frappe.publish_realtime(
			event="hrms:update_salary_slips",
			message={"employee": self.employee},
			user=employee_user,
			after_commit=True,
		)

	def on_trash(self):
		from frappe.model.naming import revert_series_if_last

		if not self.has_custom_naming_series:
			revert_series_if_last(self.default_series, self.name)

		delete_employee_benefit_ledger_entry("salary_slip", self.name)

	def get_status(self):
		if self.docstatus == 2:
			return "Cancelled"
		else:
			if self.salary_withholding:
				return "Withheld"
			elif self.docstatus == 0:
				return "Draft"
			elif self.docstatus == 1:
				return "Submitted"

	def validate_dates(self):
		self.validate_from_to_dates("start_date", "end_date")

		if not self.joining_date:
			frappe.throw(
				_("Please set the Date Of Joining for employee {0}").format(frappe.bold(self.employee_name))
			)

		if date_diff(self.end_date, self.joining_date) < 0:
			frappe.throw(_("Cannot create Salary Slip for Employee joining after Payroll Period"))

		if self.relieving_date and date_diff(self.relieving_date, self.start_date) < 0:
			frappe.throw(_("Cannot create Salary Slip for Employee who has left before Payroll Period"))

	def check_existing(self):
		if not self.salary_slip_based_on_timesheet:
			ss = frappe.qb.DocType("Salary Slip")
			query = (
				frappe.qb.from_(ss)
				.select(ss.name)
				.where(
					(ss.start_date == self.start_date)
					& (ss.end_date == self.end_date)
					& (ss.docstatus != 2)
					& (ss.employee == self.employee)
					& (ss.name != self.name)
				)
			)

			if self.payroll_entry:
				query = query.where(ss.payroll_entry == self.payroll_entry)

			ret_exist = query.run()

			if ret_exist:
				frappe.throw(
					_("Salary Slip of employee {0} already created for this period").format(self.employee)
				)
		else:
			for data in self.timesheets:
				if frappe.db.get_value("Timesheet", data.time_sheet, "status") == "Payrolled":
					frappe.throw(
						_("Salary Slip of employee {0} already created for time sheet {1}").format(
							self.employee, data.time_sheet
						)
					)

	def get_date_details(self):
		if not self.end_date:
			date_details = get_start_end_dates(self.payroll_frequency, self.start_date or self.posting_date)
			self.start_date = date_details.start_date
			self.end_date = date_details.end_date

	@frappe.whitelist()
	def get_emp_and_working_day_details(self) -> None:
		"""First time, load all the components from salary structure"""
		if self.employee:
			self.set("earnings", [])
			self.set("deductions", [])
			self.set("employer_contributions", [])
			if hasattr(self, "loans"):
				self.set("loans", [])

			if self.payroll_frequency:
				self.get_date_details()

			self.validate_dates()

			# getin leave details
			self.get_working_days_details()
			struct = self.check_sal_struct()

			if struct:
				from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

				timesheet_config = self._get_ssa_doc().get_timesheet_config()
				self.salary_slip_based_on_timesheet = timesheet_config.based_on_timesheet
				if self.salary_slip_based_on_timesheet:
					self._timesheet_component = timesheet_config.timesheet_component
					self.set_time_sheet()
					self.add_timesheet_earning_component(timesheet_config)
				make_salary_slip(self.salary_structure, self)

			process_loan_interest_accrual_and_demand(self)

	def check_sal_struct(self):
		ss = frappe.qb.DocType("Salary Structure")
		ssa = frappe.qb.DocType("Salary Structure Assignment")

		query = (
			frappe.qb.from_(ssa)
			.join(ss)
			.on(ssa.salary_structure == ss.name)
			.select(ssa.salary_structure)
			.where(
				(ssa.docstatus == 1)
				& (ss.docstatus == 1)
				& (ss.is_active == "Yes")
				& (ssa.employee == self.employee)
				& (
					(ssa.from_date <= self.start_date)
					| (ssa.from_date <= self.end_date)
					| (ssa.from_date <= self.joining_date)
				)
			)
			.orderby(ssa.from_date, order=Order.desc)
			.limit(1)
		)

		if not self.salary_slip_based_on_timesheet and self.payroll_frequency:
			query = query.where(ss.payroll_frequency == self.payroll_frequency)

		st_name = query.run()

		if st_name:
			self.salary_structure = st_name[0][0]
			return self.salary_structure

		else:
			self.salary_structure = None
			frappe.msgprint(
				_("No active or default Salary Structure found for employee {0} for the given dates").format(
					self.employee
				),
				title=_("Salary Structure Missing"),
			)

	def set_salary_structure_assignment(self):
		self._ssa_doc = None
		self.clear_cached_properties()

		self._salary_structure_assignment = frappe.db.get_value(
			"Salary Structure Assignment",
			{
				"employee": self.employee,
				"salary_structure": self.salary_structure,
				"from_date": ("<=", self.actual_start_date),
				"docstatus": 1,
			},
			"*",
			order_by="from_date desc",
			as_dict=True,
		)

		if not self._salary_structure_assignment:
			frappe.throw(
				_(
					"Please assign a Salary Structure for Employee {0} applicable from or before {1} first"
				).format(
					frappe.bold(self.employee_name),
					frappe.bold(formatdate(self.actual_start_date)),
				)
			)

	def calculate_net_pay(self, skip_tax_breakup_computation: bool = False):
		def set_gross_pay_and_base_gross_pay():
			self.gross_pay = self.get_component_totals("earnings", depends_on_payment_days=1)
			self.base_gross_pay = flt(
				flt(self.gross_pay) * flt(self.exchange_rate), self.precision("base_gross_pay")
			)

		if self.salary_structure:
			self.calculate_component_amounts("earnings")

		set_gross_pay_and_base_gross_pay()

		if self.salary_structure:
			self.calculate_component_amounts("deductions")

		set_loan_repayment(self)

		# Region-specific deductions (e.g. India statutory deductions) are injected
		# here so they are reflected in both saved slips and the preview generated
		# by process_salary_structure, before totals are finalised below.
		self.apply_regional_deductions()

		# shown on the slip, but never part of gross, deduction or net pay
		if self.salary_structure:
			self.calculate_component_amounts("employer_contributions")

		self.set_precision_for_component_amounts()
		self.set_net_pay()
		if not skip_tax_breakup_computation:
			self.compute_income_tax_breakup()

	@hrms.allow_regional
	def apply_regional_deductions(self):
		"Hook point for region-specific salary slip deductions."
		pass

	def get_amount_from_formula(self, struct_row, sub_period=1):
		if self.payroll_frequency == "Monthly":
			start_date = frappe.utils.add_months(self.start_date, sub_period)
			end_date = frappe.utils.add_months(self.end_date, sub_period)
			posting_date = frappe.utils.add_months(self.posting_date, sub_period)

		else:
			days_to_add = 0
			if self.payroll_frequency == "Weekly":
				days_to_add = sub_period * 6

			if self.payroll_frequency == "Fortnightly":
				days_to_add = sub_period * 13

			if self.payroll_frequency == "Daily":
				days_to_add = start_date

			start_date = frappe.utils.add_days(self.start_date, days_to_add)
			end_date = frappe.utils.add_days(self.end_date, days_to_add)
			posting_date = start_date

		local_data = self.data.copy()
		local_data.update({"start_date": start_date, "end_date": end_date, "posting_date": posting_date})

		return flt(self.eval_condition_and_formula(struct_row, local_data))

	def calculate_component_amounts(self, component_type):
		if component_type == "earnings":
			self.accrued_benefits = []
			self.benefit_ledger_components = []

		self.add_structure_components(component_type)

		if component_type == "employer_contributions":
			# additional salary, tax and flexi benefits are earning/deduction only
			return

		self.add_additional_salary_components(component_type)
		if component_type == "earnings":
			self.add_employee_benefits()
		else:
			self.add_tax_components()

	@cached_property
	def evaluated_components(self) -> frappe._dict:
		"""Every structure component evaluated once at full payment days, giving each
		row its period-independent default_amount.

		The context is this slip's own, with proration neutralised, so a formula sees
		real employee and slip fields rather than a stand-in for them.
		"""
		data, _default_data = self.get_data_for_eval()
		data.update(
			payment_days=self.total_working_days,
			leave_without_pay=0,
			absent_days=0,
			unmarked_days=0,
		)

		return self.evaluate_structure(data)

	def evaluate_structure(self, data: frappe._dict) -> frappe._dict:
		"""Walk earnings -> deductions -> employer contributions against one shared,
		mutating context, so a deduction formula can reference an earning's abbr."""
		structure = frappe.get_cached_doc("Salary Structure", self.salary_structure)

		rows_by_type = {"earnings": self.evaluate_component_table(structure.get("earnings") or [], data)}

		data["gross_pay"] = payable_earnings(rows_by_type["earnings"])

		rows_by_type["deductions"] = self.evaluate_component_table(structure.get("deductions") or [], data)
		rows_by_type["employer_contributions"] = self.evaluate_component_table(
			structure.get("employer_contributions") or [], data
		)

		# the assignment still owns this hook: india_payroll registers it by module path
		self._get_ssa_doc().apply_regional_ctc_components(rows_by_type, data)

		return frappe._dict(**rows_by_type)

	def evaluate_component_table(self, rows, data: frappe._dict) -> list:
		"""Evaluate one component table, returning cache-safe copies of each row.
		Rows whose condition is falsey are skipped."""
		evaluated = []

		for struct_row in rows:
			condition = sanitize_expression(struct_row.condition)
			formula = sanitize_expression(struct_row.formula)
			amount = flt(struct_row.amount)

			if condition and not self.eval_component_expression(struct_row, condition, data):
				continue

			if struct_row.amount_based_on_formula and formula:
				amount = flt(
					self.eval_component_expression(struct_row, formula, data),
					struct_row.precision("amount"),
				)

			row = frappe._dict(
				condition=condition,
				formula=formula,
				amount=flt(struct_row.amount),
				default_amount=amount,
				precision=struct_row.precision("amount"),
			)
			for field in SALARY_COMPONENT_FLAGS:
				row[field] = struct_row.get(field)

			data[struct_row.abbr] = amount
			evaluated.append(row)

		return evaluated

	def eval_component_expression(self, row, code: str, data: frappe._dict):
		try:
			return _safe_eval(code, COMPONENT_EVAL_GLOBALS.copy(), data)
		except NameError as ne:
			throw_error_message(
				row,
				ne,
				title=_("Name error"),
				description=_("This error can be due to missing or deleted field."),
			)
		except SyntaxError as se:
			throw_error_message(
				row,
				se,
				title=_("Syntax error"),
				description=_("This error can be due to invalid syntax."),
			)
		except Exception as exc:
			throw_error_message(
				row,
				exc,
				title=_("Error in formula or condition"),
				description=_("This error can be due to invalid formula or condition."),
			)
			raise

	def _get_ssa_doc(self):
		if not getattr(self, "_ssa_doc", None):
			if not hasattr(self, "_salary_structure_assignment"):
				self.set_salary_structure_assignment()
			self._ssa_doc = frappe.get_cached_doc(
				"Salary Structure Assignment", self._salary_structure_assignment.name
			)
		return self._ssa_doc

	def set_prospective_context(self, assignment, employee) -> None:
		"""Evaluate a package for someone with no submitted assignment and no Employee
		record, as a Job Offer does. Neither document has to be saved.

		An unhired candidate cannot have attendance, so the cycle is always full.
		"""
		self._ssa_doc = assignment
		self._salary_structure_assignment = assignment.as_dict()
		self._employee_doc = employee
		self.clear_cached_properties()

		self.salary_structure = assignment.salary_structure
		self.company = assignment.company
		self.currency = assignment.currency
		self.payroll_frequency = frappe.get_cached_value(
			"Salary Structure", assignment.salary_structure, "payroll_frequency"
		)
		self.start_date = self.start_date or assignment.from_date
		self.get_date_details()

		# a full cycle is paid at the end of it
		self.posting_date = self.end_date

		period_days = date_diff(self.end_date, self.start_date) + 1
		self.total_working_days = period_days
		self.payment_days = period_days
		self.leave_without_pay = 0
		self.absent_days = 0
		self.unmarked_days = 0

	def add_structure_components(self, component_type):
		self.data, self.default_data = self.get_data_for_eval()

		for struct_row in self.evaluated_components[component_type]:
			self.add_structure_component(struct_row, component_type)

	def add_structure_component(self, struct_row, component_type):
		# the timesheet wage component is added separately (hour_rate * hours) in
		# add_timesheet_earning_component, so skip it here to avoid double-adding
		if self.salary_slip_based_on_timesheet and struct_row.salary_component == getattr(
			self, "_timesheet_component", None
		):
			return

		# struct_row is a resolved row from the Salary Structure Assignment carrying the
		# component's formula/condition/flags. The slip evaluates it against its own context:
		#   - self.data:         payment-days prorated values -> the actual `amount`
		#   - self.default_data: full-cycle values            -> the `default_amount`
		# (proration cascades through dependent formulas, e.g. SA = BS * 0.5 inherits BS's proration).
		amount = self.eval_condition_and_formula(struct_row, self.data)
		if struct_row.statistical_component or struct_row.accrual_component:
			# update statistical component amount in reference data based on payment days
			# since row for statistical component is not added to salary slip
			self.default_data[struct_row.abbr] = flt(amount)
			if struct_row.depends_on_payment_days:
				amount = (
					flt(amount) * flt(self.payment_days) / cint(self.total_working_days)
					if self.total_working_days
					else 0
				)
				self.data[struct_row.abbr] = flt(amount, struct_row.precision)

			is_accrual_component = (
				component_type == "earnings"
				and struct_row.accrual_component
				and hasattr(self, "benefit_ledger_components")
			)
			if is_accrual_component:
				self.append(
					"accrued_benefits",
					{
						"salary_component": struct_row.salary_component,
						"amount": amount,
					},
				)
				self.benefit_ledger_components.append(
					{
						"salary_component": struct_row.salary_component,
						"amount": amount,
						"is_accrual": 1,
						"transaction_type": "Accrual",
						"flexible_benefit": 0,
						"remarks": "Accrual Component assigned via salary structure",
					}
				)
		else:
			# default behavior, the system does not add if component amount is zero
			# if remove_if_zero_valued is unchecked, then ask system to add component row
			remove_if_zero_valued = frappe.get_cached_value(
				"Salary Component", struct_row.salary_component, "remove_if_zero_valued"
			)

			default_amount = 0

			if (
				amount
				or (struct_row.amount_based_on_formula and amount is not None)
				or (not remove_if_zero_valued and amount is not None and not self.data[struct_row.abbr])
			):
				# full-cycle default comes from SSA (period-independent); the slip only
				# computes the prorated `amount` above (proration is a period concern)
				default_amount = flt(struct_row.default_amount)
				self.update_component_row(
					struct_row,
					amount,
					component_type,
					data=self.data,
					default_amount=default_amount,
					remove_if_zero_valued=remove_if_zero_valued,
				)

	def get_data_for_eval(self):
		"""Returns data for evaluating formula"""
		if not hasattr(self, "_salary_structure_assignment"):
			self.set_salary_structure_assignment()

		employee = getattr(self, "_employee_doc", None) or self.employee
		data = get_component_eval_context(employee, self._salary_structure_assignment)
		# Overlay salary-slip fields (payment_days, gross_pay, start_date, …) last, so the
		# actual period context wins on a name collision with an Employee field (e.g. a saved
		# payslip keeps its own department/branch snapshot, not the employee's current one).
		slip_data = self.as_dict()
		# Exception: ctc is computed later by compute_ctc(), so it's still 0/unset here
		# drop it instead of overwriting the real value from Employee/SSA.
		slip_data.pop("ctc", None)
		data.update(slip_data)

		# shallow copy to store default amounts (without payment-days proration) for tax calculation
		default_data = data.copy()

		for key in COMPONENT_PARENTFIELDS:
			for d in self.get(key):
				default_data[d.abbr] = d.default_amount or 0
				data[d.abbr] = d.amount or 0

		return data, default_data

	def eval_condition_and_formula(self, struct_row, data):
		try:
			condition, formula, amount = struct_row.condition, struct_row.formula, struct_row.amount
			if condition and not _safe_eval(condition, self.whitelisted_globals, data):
				return None
			if struct_row.amount_based_on_formula and formula:
				# struct_row is a evaluated row (frappe._dict) from the SSA; precision is carried as an int
				amount = flt(_safe_eval(formula, self.whitelisted_globals, data), struct_row.precision)
			if amount:
				data[struct_row.abbr] = amount

			return amount

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

	def add_additional_salary_components(self, component_type):
		additional_salaries = get_additional_salaries(
			self.employee, self.start_date, self.end_date, component_type
		)

		for additional_salary in additional_salaries:
			component_data = get_salary_component_data(additional_salary.component)
			remove_if_zero_valued = frappe.get_cached_value(
				"Salary Component", additional_salary.component, "remove_if_zero_valued"
			)
			if flt(additional_salary.amount) == 0 and remove_if_zero_valued:
				continue
			self.update_component_row(
				component_data,
				additional_salary.amount,
				component_type,
				additional_salary,
				is_recurring=additional_salary.is_recurring,
			)

			if component_type == "earnings" and hasattr(self, "benefit_ledger_components"):
				if (
					additional_salary.ref_doctype == "Employee Benefit Claim"
					and component_data.is_flexible_benefit
				) or component_data.accrual_component:
					# track benefit claim or accrual component payout to record in Employee Benefit Ledger
					if additional_salary.ref_doctype == "Employee Benefit Claim":
						remarks = f"Payout against Employee Benefit Claim {additional_salary.ref_docname}"
						flexible_benefit = 1
					else:
						remarks = "Accrual Component payout via Additional Salary"
						flexible_benefit = 0

					self.benefit_ledger_components.append(
						{
							"salary_component": additional_salary.component,
							"amount": additional_salary.amount,
							"is_accrual": 0,
							"transaction_type": "Payout",
							"flexible_benefit": flexible_benefit,
							"remarks": remarks,
						}
					)

	def update_component_row(
		self,
		component_data,
		amount,
		component_type,
		additional_salary=None,
		is_recurring=0,
		data=None,
		default_amount=None,
		remove_if_zero_valued=None,
	):
		component_row = None
		for d in self.get(component_type):
			if d.salary_component != component_data.salary_component:
				continue

			if (not d.additional_salary and (not additional_salary or additional_salary.overwrite)) or (
				additional_salary and additional_salary.name == d.additional_salary
			):
				component_row = d
				break

		if additional_salary and additional_salary.overwrite:
			# Additional Salary with overwrite checked, remove default rows of same component
			self.set(
				component_type,
				[
					d
					for d in self.get(component_type)
					if d.salary_component != component_data.salary_component
					or (d.additional_salary and additional_salary.name != d.additional_salary)
					or d == component_row
				],
			)

		if not component_row:
			if not (amount or default_amount) and remove_if_zero_valued:
				return

			component_row = self.append(component_type)
			for attr in (
				"depends_on_payment_days",
				"salary_component",
				"abbr",
				"do_not_include_in_total",
				"do_not_include_in_accounts",
				"accrual_component",
				"is_tax_applicable",
				"is_flexible_benefit",
				"variable_based_on_taxable_salary",
				"exempted_from_income_tax",
			):
				component_row.set(attr, component_data.get(attr))

		if additional_salary:
			if additional_salary.overwrite:
				component_row.additional_amount = flt(
					flt(amount) - flt(component_row.get("default_amount", 0)),
					component_row.precision("additional_amount"),
				)
			else:
				component_row.default_amount = 0
				component_row.additional_amount = amount

			component_row.is_recurring_additional_salary = is_recurring
			component_row.additional_salary = additional_salary.name
			component_row.deduct_full_tax_on_selected_payroll_date = (
				additional_salary.deduct_full_tax_on_selected_payroll_date
			)
		else:
			component_row.default_amount = default_amount or amount
			component_row.additional_amount = 0
			component_row.deduct_full_tax_on_selected_payroll_date = (
				component_data.deduct_full_tax_on_selected_payroll_date
			)

		component_row.amount = amount

		# Skip payment days adjustment for:
		# 1. Arrear/Payroll Correction additional salary - already calculated based on LWP days in previous cycles
		# 2. Employee Benefit Claim - payout often includes amount for previous cycles
		# 2. Accrual components - paid based on accrual amounts from previous cycles
		skip_payment_days_adjustment = (
			additional_salary
			and additional_salary.get("ref_doctype")
			in ["Arrear", "Payroll Correction", "Employee Benefit Claim"]
		) or component_row.accrual_component
		if not skip_payment_days_adjustment:
			self.update_component_amount_based_on_payment_days(component_row, remove_if_zero_valued)

		if data:
			data[component_row.abbr] = component_row.amount

	def update_component_amount_based_on_payment_days(self, component_row, remove_if_zero_valued=None):
		component_row.amount = self.get_amount_based_on_payment_days(component_row)[0]

		# remove 0 valued components that have been updated later
		if component_row.amount == 0 and remove_if_zero_valued:
			self.remove(component_row)

	def set_precision_for_component_amounts(self):
		for component_type in COMPONENT_PARENTFIELDS:
			for component_row in self.get(component_type):
				component_row.amount = flt(component_row.amount, component_row.precision("amount"))

	def get_amount_based_on_payment_days(self, row):
		amount, additional_amount = row.amount, row.additional_amount
		timesheet_component = getattr(self, "_timesheet_component", None)

		if not row.additional_salary and not row.default_amount:
			amount, additional_amount = amount, additional_amount
		elif (
			self.salary_structure
			and cint(row.depends_on_payment_days)
			and cint(self.total_working_days)
			and not (
				row.additional_salary and row.default_amount
			)  # to identify overwritten additional salary
			and (
				row.salary_component != timesheet_component
				or getdate(self.start_date) < self.joining_date
				or (self.relieving_date and getdate(self.end_date) > self.relieving_date)
			)
		):
			additional_amount = flt(
				(flt(row.additional_amount) * flt(self.payment_days) / cint(self.total_working_days)),
				row.precision("additional_amount"),
			)
			amount = (
				flt(
					(flt(row.default_amount) * flt(self.payment_days) / cint(self.total_working_days)),
					row.precision("amount"),
				)
				+ additional_amount
			)

		elif (
			not self.payment_days
			and row.salary_component != timesheet_component
			and cint(row.depends_on_payment_days)
		):
			amount, additional_amount = 0, 0
		elif not row.amount and row.additional_amount:
			amount = flt(row.additional_amount)

		# apply rounding
		if frappe.db.get_value(
			"Salary Component", row.salary_component, "round_to_the_nearest_integer", cache=True
		):
			amount, additional_amount = rounded(amount or 0), rounded(additional_amount or 0)

		return amount, additional_amount

	def email_salary_slip(self):
		receiver = frappe.db.get_value("Employee", self.employee, "prefered_email", cache=True)
		payroll_settings = frappe.get_single("Payroll Settings")

		subject = f"Salary Slip - from {self.start_date} to {self.end_date}"
		message = _("Please see attachment")
		if payroll_settings.email_template:
			email_template = frappe.get_doc("Email Template", payroll_settings.email_template)
			context = self.as_dict()
			subject = frappe.render_template(email_template.subject, context)
			message = frappe.render_template(email_template.response, context)

		password = None
		if payroll_settings.encrypt_salary_slips_in_emails:
			password = generate_password_for_pdf(payroll_settings.password_policy, self.employee)
			if not payroll_settings.email_template:
				message += "<br>" + _(
					"Note: Your salary slip is password protected, the password to unlock the PDF is of the format {0}."
				).format(payroll_settings.password_policy)

		if receiver:
			posting_date = getdate(self.posting_date)
			email_args = {
				"sender": payroll_settings.sender_email,
				"recipients": [receiver],
				"message": message,
				"subject": subject,
				"attachments": [
					frappe.attach_print(self.doctype, self.name, file_name=self.name, password=password)
				],
				"reference_doctype": self.doctype,
				"reference_name": self.name,
				"send_after": posting_date if posting_date > getdate() else None,
			}
			if not frappe.flags.in_test:
				enqueue(method=frappe.sendmail, queue="short", timeout=300, is_async=True, **email_args)
			else:
				frappe.sendmail(**email_args)
		else:
			msgprint(_("{0}: Employee email not found, hence email not sent").format(self.employee_name))

	def update_status(self, salary_slip=None):
		for data in self.timesheets:
			if data.time_sheet:
				timesheet = frappe.get_doc("Timesheet", data.time_sheet)
				timesheet.salary_slip = salary_slip
				timesheet.flags.ignore_validate_update_after_submit = True
				timesheet.set_status()
				timesheet.save()

	def set_status(self, status=None):
		"""Get and update status"""
		if not status:
			status = self.get_status()
		self.db_set("status", status)

	def process_salary_structure(self, for_preview=0, lwp_days_corrected=None):
		"""Calculate salary after salary structure details have been updated"""
		if self.payroll_frequency:
			self.get_date_details()
		self.pull_emp_details()
		self.get_working_days_details(for_preview=for_preview, lwp_days_corrected=lwp_days_corrected)
		self.calculate_net_pay()

	def pull_emp_details(self):
		account_details = frappe.get_cached_value(
			"Employee", self.employee, ["bank_name", "bank_ac_no", "salary_mode"], as_dict=1
		)
		if account_details:
			self.mode_of_payment = account_details.salary_mode
			self.bank_name = account_details.bank_name
			self.bank_account_no = account_details.bank_ac_no

	@frappe.whitelist()
	def process_salary_based_on_working_days(self) -> None:
		self.get_working_days_details(lwp=self.leave_without_pay)
		self.calculate_net_pay()

	# calculate total working hours, earnings based on hourly wages and totals

	def add_leave_balances(self):
		self.set("leave_details", [])

		if frappe.db.get_single_value("Payroll Settings", "show_leave_balances_in_salary_slip"):
			from hrms.hr.doctype.leave_application.leave_application import get_leave_details

			leave_details = get_leave_details(self.employee, self.end_date, True)

			for leave_type, leave_values in leave_details["leave_allocation"].items():
				self.append(
					"leave_details",
					{
						"leave_type": leave_type,
						"total_allocated_leaves": flt(leave_values.get("total_leaves")),
						"expired_leaves": flt(leave_values.get("expired_leaves")),
						"used_leaves": flt(leave_values.get("leaves_taken")),
						"pending_leaves": flt(leave_values.get("leaves_pending_approval")),
						"available_leaves": flt(leave_values.get("remaining_leaves")),
					},
				)

	def on_discard(self):
		self.db_set("status", "Cancelled")


def unlink_ref_doc_from_salary_slip(doc, method=None):
	"""Unlinks accrual Journal Entry from Salary Slips on cancellation"""
	linked_ss = frappe.get_all(
		"Salary Slip", filters={"journal_entry": doc.name, "docstatus": ["<", 2]}, pluck="name"
	)

	if linked_ss:
		for ss in linked_ss:
			ss_doc = frappe.get_doc("Salary Slip", ss)
			frappe.db.set_value("Salary Slip", ss_doc.name, "journal_entry", "")


@frappe.whitelist()
def make_salary_slip_from_timesheet(source_name: str, target_doc: str | Document | None = None) -> Document:
	frappe.has_permission("Timesheet", "read", source_name, throw=True)
	target = frappe.new_doc("Salary Slip")
	set_missing_values(source_name, target)
	if not target.check_sal_struct():
		frappe.throw(
			_("Cannot create Salary Slip: no active Salary Structure is assigned to employee {0}.").format(
				frappe.bold(target.employee_name)
			)
		)

	timesheet_config = frappe.get_cached_value(
		"Salary Structure",
		target.salary_structure,
		["salary_slip_based_on_timesheet", "salary_component"],
		as_dict=True,
	)
	if not timesheet_config or not timesheet_config.salary_slip_based_on_timesheet:
		frappe.throw(
			_(
				"The Assigned Salary Structure {0} for the employee {1} is not configured for Salary Slip based on Timesheet."
			).format(frappe.bold(target.salary_structure), frappe.bold(target.employee_name))
		)
	if not timesheet_config.salary_component:
		frappe.throw(
			_(
				"The Assigned Salary Structure {0} for the employee {1} does not have a Salary Component configured for Salary Slip based on Timesheet."
			).format(frappe.bold(target.salary_structure), frappe.bold(target.employee_name))
		)
	target.run_method("get_emp_and_working_day_details")

	return target


def set_missing_values(time_sheet, target):
	doc = frappe.get_doc("Timesheet", time_sheet)
	target.employee = doc.employee
	target.employee_name = doc.employee_name
	target.salary_slip_based_on_timesheet = 1
	target.start_date = doc.start_date
	target.end_date = doc.end_date
	target.posting_date = doc.modified
	target.total_working_hours = doc.total_hours
	target.append("timesheets", {"time_sheet": doc.name, "working_hours": doc.total_hours})


def on_doctype_update():
	frappe.db.add_index("Salary Slip", ["employee", "start_date", "end_date"])


@frappe.whitelist(methods=["POST"])
def enqueue_email_salary_slips(names: list | str) -> None:
	"""enqueue bulk emailing salary slips"""
	import json

	if isinstance(names, str):
		names = json.loads(names)

	for name in names:
		frappe.has_permission("Salary Slip", "read", name, throw=True)

	frappe.enqueue("hrms.payroll.doctype.salary_slip.salary_slip.email_salary_slips", names=names)
	frappe.msgprint(
		_("Salary slip emails have been enqueued for sending. Check {0} for status.").format(
			f"""<a href='{frappe.utils.get_url_to_list("Email Queue")}' target='blank'>Email Queue</a>"""
		)
	)


def email_salary_slips(names) -> None:
	for name in names:
		salary_slip = frappe.get_doc("Salary Slip", name)
		salary_slip.email_salary_slip()
