# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.query_builder.functions import Sum
from frappe.utils import cint, flt, get_link_to_form, get_weekday, get_weekdays, nowdate


class JobOffer(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.job_offer_component.job_offer_component import JobOfferComponent
		from hrms.hr.doctype.job_offer_leave.job_offer_leave import JobOfferLeave
		from hrms.hr.doctype.job_offer_term.job_offer_term import JobOfferTerm

		amended_from: DF.Link | None
		applicant_email: DF.Data
		applicant_name: DF.Data
		base: DF.Currency
		branch: DF.Link | None
		calculate_component_amount_from: DF.Literal["", "Base and Variable", "CTC"]
		company: DF.Link
		ctc: DF.Currency
		ctc_breakup: DF.Table[JobOfferComponent]
		currency: DF.Link | None
		date_of_joining: DF.Date | None
		department: DF.Link | None
		designation: DF.Link
		employment_type: DF.Link | None
		grade: DF.Link | None
		gross: DF.Currency
		holiday_list: DF.Link | None
		job_applicant: DF.Link | None
		job_offer_term_template: DF.Link | None
		leave_allocations: DF.Table[JobOfferLeave]
		leave_policy: DF.Link | None
		letter_head: DF.Link | None
		notice_number_of_days: DF.Int
		notice_period_during_probation: DF.Int
		offer_date: DF.Date
		offer_terms: DF.Table[JobOfferTerm]
		offer_valid_till: DF.Date | None
		probation_period_days: DF.Int
		reports_to: DF.Link | None
		salary_structure: DF.Link | None
		select_print_heading: DF.Link | None
		select_terms: DF.Link | None
		total_public_holidays: DF.Int
		status: DF.Literal["Awaiting Response", "Accepted", "Rejected", "Cancelled"]
		terms: DF.TextEditor | None
		variable: DF.Currency
		weekly_off_days: DF.Data | None
		working_hours: DF.Float
	# end: auto-generated types

	def onload(self):
		employee = frappe.db.get_value("Employee", {"job_offer": self.name}, "name") or ""
		self.set_onload("employee", employee)

	def validate(self):
		self.validate_vacancies()
		self.validate_duplicate_job_offer()
		self.set_compensation()
		self.set_leave_details()

	def set_leave_details(self):
		self.set("leave_allocations", get_leave_allocations(self.leave_policy))

		summary = get_holiday_summary(self.holiday_list)
		self.weekly_off_days = summary["weekly_off_days"]
		self.total_public_holidays = summary["total_public_holidays"]

	def validate_duplicate_job_offer(self):
		duplicate = frappe.db.exists(
			"Job Offer",
			{
				"applicant_email": self.applicant_email,
				"docstatus": ["!=", 2],
				"status": ["not in", ["Rejected", "Cancelled"]],
				"name": ["!=", self.name],
			},
		)
		if duplicate:
			frappe.throw(
				_("Job Offer {0} already exists for {1}").format(
					get_link_to_form("Job Offer", duplicate), frappe.bold(self.applicant_email)
				)
			)

	def set_compensation(self):
		if not self.salary_structure or not self.calculate_component_amount_from:
			self.ctc = 0
			self.gross = 0
			self.set("ctc_breakup", [])
			return

		if not self.compensation_inputs_changed():
			return

		details = compute_compensation(self)

		self.base = details["base"]
		self.ctc = details["ctc"]
		self.gross = details["gross"]
		self.set("ctc_breakup", details["components"])

	def compensation_inputs_changed(self) -> bool:
		if not self.ctc_breakup:
			return True

		previous = self.get_doc_before_save()
		if not previous:
			self.load_doc_before_save()
			previous = self.get_doc_before_save()

		if not previous:
			return True

		driver = "ctc" if self.calculate_component_amount_from == "CTC" else "base"
		fieldnames = (*COMPENSATION_INPUTS, driver, *shared_regional_fieldnames(self))

		return any(not _same_input(self.get(f), previous.get(f)) for f in fieldnames)

	def validate_vacancies(self):
		staffing_plan = get_staffing_plan_detail(self.designation, self.company, self.offer_date)
		check_vacancies = frappe.get_single("HR Settings").check_vacancies
		if staffing_plan and check_vacancies:
			job_offers = self.get_job_offer(staffing_plan.from_date, staffing_plan.to_date)
			if not staffing_plan.get("vacancies") or cint(staffing_plan.vacancies) - len(job_offers) <= 0:
				error_variable = "for " + frappe.bold(self.designation)
				if staffing_plan.get("parent"):
					error_variable = frappe.bold(get_link_to_form("Staffing Plan", staffing_plan.parent))

				frappe.throw(_("There are no vacancies under staffing plan {0}").format(error_variable))

	def on_change(self):
		update_job_applicant(self.status, self.job_applicant)

	def get_job_offer(self, from_date, to_date):
		"""Returns job offer created during a time period"""
		return frappe.get_all(
			"Job Offer",
			filters={
				"offer_date": ["between", (from_date, to_date)],
				"designation": self.designation,
				"company": self.company,
				"docstatus": 1,
			},
			fields=["name"],
		)

	def on_discard(self):
		self.db_set("status", "Cancelled")


def update_job_applicant(status, job_applicant):
	if job_applicant and status in ("Accepted", "Rejected"):
		frappe.set_value("Job Applicant", job_applicant, "status", status)


def get_staffing_plan_detail(designation, company, offer_date):
	spd = frappe.qb.DocType("Staffing Plan Detail")
	sp = frappe.qb.DocType("Staffing Plan")

	detail = (
		frappe.qb.from_(spd)
		.inner_join(sp)
		.on(spd.parent == sp.name)
		.select(
			spd.parent,
			sp.from_date.as_("from_date"),
			sp.to_date.as_("to_date"),
			sp.name,
			Sum(spd.vacancies).as_("vacancies"),
			spd.designation,
		)
		.distinct()
		.where(
			(sp.docstatus == 1)
			& (spd.designation == designation)
			& (sp.company == company)
			& (sp.from_date <= offer_date)
			& (offer_date <= sp.to_date)
		)
		.groupby(spd.parent, sp.from_date, sp.to_date, sp.name, spd.designation)
	).run(as_dict=1)

	return frappe._dict(detail[0]) if (detail and detail[0].parent) else None


@frappe.whitelist()
def make_employee(source_name: str, target_doc: str | Document | None = None):
	def set_missing_values(source, target):
		target.personal_email = source.applicant_email
		target.first_name = source.applicant_name
		target.job_offer = source.name

	doc = get_mapped_doc(
		"Job Offer",
		source_name,
		{
			"Job Offer": {
				"doctype": "Employee",
				"field_map": {"applicant_name": "employee_name", "offer_date": "scheduled_confirmation_date"},
			}
		},
		target_doc,
		set_missing_values,
	)
	return doc


def build_prospective_assignment(offer):
	structure_currency = frappe.get_cached_value("Salary Structure", offer.salary_structure, "currency")
	from_date = offer.date_of_joining or offer.offer_date or nowdate()

	prospective_employee = frappe.new_doc("Employee")
	prospective_employee.company = offer.company
	prospective_employee.department = offer.department
	prospective_employee.designation = offer.designation
	prospective_employee.grade = offer.grade
	prospective_employee.branch = offer.branch
	prospective_employee.employment_type = offer.employment_type
	prospective_employee.date_of_joining = from_date

	assignment = frappe.new_doc("Salary Structure Assignment")
	assignment.employee = prospective_employee
	assignment.salary_structure = offer.salary_structure
	assignment.company = offer.company
	assignment.currency = offer.currency or structure_currency
	assignment.variable = flt(offer.variable)
	assignment.from_date = from_date
	assignment.department = offer.department
	assignment.designation = offer.designation
	assignment.grade = offer.grade

	copy_regional_config(offer, assignment)

	return assignment


def _same_input(current, previous) -> bool:
	if isinstance(current, int | float) or isinstance(previous, int | float):
		return flt(current) == flt(previous)

	return str(current or "") == str(previous or "")


COMPENSATION_INPUTS = (
	"salary_structure",
	"calculate_component_amount_from",
	"variable",
	"company",
	"grade",
	"branch",
	"employment_type",
	"department",
	"designation",
	"date_of_joining",
	"offer_date",
)


def shared_regional_fieldnames(offer) -> list[str]:
	offer_fieldnames = {df.fieldname for df in offer.meta.fields}

	return [
		df.fieldname
		for df in frappe.get_meta("Salary Structure Assignment").get("fields", {"is_custom_field": 1})
		if df.fieldtype not in frappe.model.no_value_fields and df.fieldname in offer_fieldnames
	]


def copy_regional_config(offer, assignment) -> None:
	for fieldname in shared_regional_fieldnames(offer):
		assignment.set(fieldname, offer.get(fieldname))


def get_breakup_rows(assignment, periods: int, total_ctc: float) -> list[dict]:
	rows_by_type = assignment.get_evaluated_components()

	def row(label, per_cycle: float, is_summary: int) -> dict:
		return {
			"fixed_components": label,
			"per_cycle": flt(per_cycle),
			"yearly": flt(per_cycle * periods),
			"currency": assignment.currency,
			"is_summary": is_summary,
		}

	def payable(component_type) -> list:
		return [
			r for r in rows_by_type[component_type] if not r.statistical_component and flt(r.default_amount)
		]

	earnings = payable("earnings")
	employer_contributions = payable("employer_contributions")

	if not earnings and not employer_contributions:
		return []

	gross = flt(assignment.annual_gross_earning) / periods
	deductions = sum(flt(r.default_amount) for r in payable("deductions"))

	breakup = [row(r.salary_component, flt(r.default_amount), 0) for r in earnings]
	breakup.append(row(_("Gross Pay"), gross, 1))
	breakup += [row(r.salary_component, flt(r.default_amount), 0) for r in employer_contributions]
	breakup.append(row(_("Total Cost to Company (CTC)"), flt(total_ctc) / periods, 1))
	breakup.append(row(_("Take Home* (Income Tax applicable as per IT Act)"), gross - deductions, 1))

	return breakup


def compute_compensation(offer) -> dict:
	from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
		PERIODS_PER_YEAR,
	)
	from hrms.payroll.utils import CTC_SOLVER_TOLERANCE

	empty = {
		"base": flt(offer.base),
		"ctc": 0.0,
		"gross": 0.0,
		"components": [],
		"ctc_adjusted": False,
	}
	if not offer.salary_structure or not offer.calculate_component_amount_from:
		return empty

	assignment = build_prospective_assignment(offer)

	ctc_adjusted = False

	if offer.calculate_component_amount_from == "CTC":
		target_ctc = flt(offer.ctc)
		if target_ctc <= 0:
			return empty

		base, total_ctc = _resolve_base_for_target(assignment, flt(offer.base), target_ctc)
		ctc_adjusted = abs(total_ctc - target_ctc) > CTC_SOLVER_TOLERANCE
	else:
		base = flt(offer.base)
		if not base:
			return empty

		assignment.base = base
		assignment.calculate_ctc_and_gross()
		total_ctc = flt(assignment.ctc)

	assignment.base = base
	frequency = frappe.get_cached_value("Salary Structure", offer.salary_structure, "payroll_frequency")
	periods = PERIODS_PER_YEAR.get(frequency, 12)

	return {
		"base": base,
		"ctc": total_ctc,
		"gross": flt(assignment.annual_gross_earning) / periods,
		"components": get_breakup_rows(assignment, periods, total_ctc),
		"ctc_adjusted": ctc_adjusted,
	}


def _resolve_base_for_target(assignment, base: float, target_ctc: float) -> tuple[float, float]:
	from hrms.payroll.utils import CTC_SOLVER_TOLERANCE, solve_base_for_ctc

	if base:
		assignment.base = base
		assignment.calculate_ctc_and_gross()
		if abs(flt(assignment.ctc) - target_ctc) <= CTC_SOLVER_TOLERANCE:
			return base, flt(assignment.ctc)

	return solve_base_for_ctc(assignment, target_ctc)


@frappe.whitelist()
def get_compensation_details(offer: str | dict) -> dict:
	frappe.has_permission("Job Offer", throw=True)

	offer = frappe.parse_json(offer)
	offer["doctype"] = "Job Offer"

	return compute_compensation(frappe.get_doc(offer))


@frappe.whitelist()
def get_offer_acceptance_rate(company: str | None = None, department: str | None = None):
	frappe.has_permission("Job Offer", throw=True)

	filters = {"docstatus": 1}
	if company:
		filters["company"] = company
	if department:
		filters["department"] = department

	total_offers = frappe.db.count("Job Offer", filters=filters)

	filters["status"] = "Accepted"
	total_accepted = frappe.db.count("Job Offer", filters=filters)

	return {
		"value": flt(total_accepted) / flt(total_offers) * 100 if total_offers else 0,
		"fieldtype": "Percent",
	}


@frappe.whitelist()
def get_leave_allocations(leave_policy: str | None = None) -> list[dict]:
	frappe.has_permission("Job Offer", throw=True)

	if not leave_policy:
		return []

	return frappe.get_all(
		"Leave Policy Detail",
		filters={"parent": leave_policy, "parenttype": "Leave Policy"},
		fields=["leave_type", "annual_allocation"],
		order_by="idx",
	)


@frappe.whitelist()
def get_holiday_summary(holiday_list: str | None = None) -> dict:
	frappe.has_permission("Job Offer", throw=True)

	if not holiday_list:
		return {"weekly_off_days": "", "total_public_holidays": 0}

	holidays = frappe.get_all(
		"Holiday",
		filters={"parent": holiday_list, "parenttype": "Holiday List"},
		fields=["holiday_date", "weekly_off"],
	)
	weekdays = get_weekdays()
	off_days = {get_weekday(holiday.holiday_date) for holiday in holidays if holiday.weekly_off}

	return {
		"weekly_off_days": ", ".join(_(day) for day in sorted(off_days, key=weekdays.index)),
		"total_public_holidays": sum(1 for holiday in holidays if not holiday.weekly_off),
	}
