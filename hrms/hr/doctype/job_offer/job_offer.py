# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.query_builder.functions import Sum
from frappe.utils import cint, flt, get_link_to_form, nowdate


class JobOffer(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.job_offer_component.job_offer_component import JobOfferComponent
		from hrms.hr.doctype.job_offer_term.job_offer_term import JobOfferTerm

		amended_from: DF.Link | None
		applicant_email: DF.Data | None
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
		holiday_list: DF.Link | None
		job_applicant: DF.Link
		job_offer_term_template: DF.Link | None
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
		status: DF.Literal["Awaiting Response", "Accepted", "Rejected", "Cancelled"]
		terms: DF.TextEditor | None
		variable: DF.Currency
		working_hours: DF.Float
	# end: auto-generated types

	def onload(self):
		employee = frappe.db.get_value("Employee", {"job_applicant": self.job_applicant}, "name") or ""
		self.set_onload("employee", employee)

	def validate(self):
		self.validate_vacancies()
		job_offer = frappe.db.exists(
			"Job Offer", {"job_applicant": self.job_applicant, "docstatus": ["!=", 2]}
		)
		if job_offer and job_offer != self.name:
			frappe.throw(
				_("Job Offer: {0} is already for Job Applicant: {1}").format(
					frappe.bold(job_offer), frappe.bold(self.job_applicant)
				)
			)
		self.set_compensation()

	def set_compensation(self):
		"""Rebuild the CTC break-up server-side so the offer is correct however it was
		saved -- the form is not the only way in (REST, data import, and the Employee
		override that auto-submits the offer all bypass it)."""
		if not self.salary_structure or not self.calculate_component_amount_from:
			self.ctc = 0
			self.set("ctc_breakup", [])
			return

		details = compute_compensation(self)

		self.base = details["base"]
		self.ctc = details["ctc"]
		self.set("ctc_breakup", details["components"])

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
	if status in ("Accepted", "Rejected"):
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
		target.personal_email, target.first_name = frappe.db.get_value(
			"Job Applicant", source.job_applicant, ["email_id", "applicant_name"]
		)

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
	"""An unsaved Salary Structure Assignment carrying an unsaved Employee, so the offer
	and payroll share one evaluator.

	Component formulas routinely reference employee fields (employment_type, grade, ...),
	so those are seeded from the offer itself. Neither document is ever saved. ``base`` is
	left to the caller, which varies it while solving for a target CTC.
	"""
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


def copy_regional_config(offer, assignment) -> None:
	"""Carry an offer's regional payroll configuration onto the prospective assignment.

	Statutory settings that change the employer's cost (india_payroll's ``epf_applicable``
	and ``contribute_on_actual_pf_wage``, for instance) live on the Salary Structure
	Assignment as Custom Fields, and the regional CTC hook reads them from there. A regional
	app opts an offer in simply by adding the same fieldname to Job Offer; nothing here
	names a region-specific field.

	Only Custom Fields are considered, so a standard field can never be clobbered by a
	same-named field that means something different on the other doctype.
	"""
	offer_fieldnames = {df.fieldname for df in offer.meta.fields}

	for df in frappe.get_meta("Salary Structure Assignment").get("fields", {"is_custom_field": 1}):
		if df.fieldtype in frappe.model.no_value_fields:
			continue
		if df.fieldname in offer_fieldnames:
			assignment.set(df.fieldname, offer.get(df.fieldname))


def get_breakup_rows(assignment, periods: int, total_ctc: float) -> list[dict]:
	"""The components that make up CTC -- every non-statistical earning and employer
	contribution -- closed by a CTC row and a Take Home row.

	Deductions are paid out of CTC, not added to it, so they never appear here. Take Home
	is CTC less the employer's own off-slip cost; it does not net off employee deductions
	or tax, so it is the value of the package to the candidate rather than a payslip
	figure.

	The two closing rows carry ``is_summary`` because this table is printed on the offer
	letter, and a consumer must be able to tell a total from a component without matching
	label text that has already been translated.
	"""
	rows_by_type = assignment.get_evaluated_components()

	breakup = []
	employer_yearly = 0.0

	for component_type in ("earnings", "employer_contributions"):
		for row in rows_by_type[component_type]:
			if row.statistical_component:
				continue

			per_cycle = flt(row.default_amount)
			yearly = flt(per_cycle * periods)
			if component_type == "employer_contributions":
				employer_yearly += yearly

			breakup.append(
				{
					"fixed_components": row.salary_component,
					"per_cycle": per_cycle,
					"yearly": yearly,
					"currency": assignment.currency,
					"is_summary": 0,
				}
			)

	if not breakup:
		return breakup

	for label, yearly in (
		(_("Total Cost to Company (CTC)"), total_ctc),
		(_("Take Home"), flt(total_ctc - employer_yearly)),
	):
		breakup.append(
			{
				"fixed_components": label,
				"per_cycle": flt(yearly / periods),
				"yearly": yearly,
				"currency": assignment.currency,
				"is_summary": 1,
			}
		)

	return breakup


def compute_compensation(offer) -> dict:
	"""Resolve base, CTC and the break-up for one offer.

	Takes the Job Offer document itself, saved or not, rather than a list of field values:
	a regional app can then influence the result purely by adding fields to Job Offer, with
	no change to this signature, the whitelisted endpoint or the client.

	In ``Base and Variable`` mode the structure is evaluated at the offered base. In
	``CTC`` mode the base that produces the target CTC is solved for instead; a target
	that no base can reach (component rounding makes CTC a staircase) yields the closest
	achievable figure with ``ctc_adjusted`` set, so the caller can say so rather than
	storing a CTC payroll cannot reproduce.
	"""
	from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
		PERIODS_PER_YEAR,
	)
	from hrms.payroll.utils import CTC_SOLVER_TOLERANCE

	empty = {"base": flt(offer.base), "ctc": 0.0, "components": [], "ctc_adjusted": False}
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

	return {
		"base": base,
		"ctc": total_ctc,
		"components": get_breakup_rows(assignment, PERIODS_PER_YEAR.get(frequency, 12), total_ctc),
		"ctc_adjusted": ctc_adjusted,
	}


def _resolve_base_for_target(assignment, base: float, target_ctc: float) -> tuple[float, float]:
	"""Skip the search when the base already on the offer still produces the target -- the
	common case on re-save, and one evaluation instead of a full solve."""
	from hrms.payroll.utils import CTC_SOLVER_TOLERANCE, solve_base_for_ctc

	if base:
		assignment.base = base
		assignment.calculate_ctc_and_gross()
		if abs(flt(assignment.ctc) - target_ctc) <= CTC_SOLVER_TOLERANCE:
			return base, flt(assignment.ctc)

	return solve_base_for_ctc(assignment, target_ctc)


@frappe.whitelist()
def get_compensation_details(offer: str | dict) -> dict:
	"""Preview the break-up for an offer the user is still editing.

	The document arrives from the form unsaved, so it is rebuilt in memory and never
	written. Nothing here is authoritative: ``validate`` recomputes from the stored
	document on save.
	"""
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
