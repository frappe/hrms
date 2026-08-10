# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.query_builder.functions import Sum
from frappe.utils import cint, flt, get_link_to_form


class JobOffer(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.job_offer_term.job_offer_term import JobOfferTerm

		amended_from: DF.Link | None
		applicant_email: DF.Data | None
		applicant_name: DF.Data
		base: DF.Currency
		branch: DF.Link | None
		company: DF.Link
		ctc: DF.Currency
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
