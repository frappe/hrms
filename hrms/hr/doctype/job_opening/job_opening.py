# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.naming import set_name_from_naming_options
from frappe.query_builder.functions import Count
from frappe.utils import cint, get_link_to_form, getdate, pretty_date, strip_html
from frappe.website.website_generator import WebsiteGenerator

from hrms.hr.doctype.staffing_plan.staffing_plan import (
	get_active_staffing_plan_details,
	get_designation_counts,
)


class JobOpening(WebsiteGenerator):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		closed_on: DF.Date | None
		closes_on: DF.Date | None
		company: DF.Link
		currency: DF.Link | None
		department: DF.Link | None
		description: DF.TextEditor | None
		designation: DF.Link
		employment_type: DF.Link | None
		job_application_route: DF.Data | None
		job_opening_template: DF.Link | None
		job_requisition: DF.Link | None
		job_title: DF.Data
		location: DF.Link | None
		lower_range: DF.Currency
		planned_vacancies: DF.Int
		posted_on: DF.Datetime | None
		prevent_duplicate_applicant: DF.Check
		publish: DF.Check
		publish_applications_received: DF.Check
		publish_salary_range: DF.Check
		route: DF.Data | None
		salary_per: DF.Literal["Month", "Year"]
		staffing_plan: DF.Link | None
		status: DF.Literal["Open", "Closed"]
		upper_range: DF.Currency
		vacancies: DF.Int
	# end: auto-generated types

	website = frappe._dict(
		template="templates/generators/job_opening.html",
		condition_field="publish",
		page_title_field="job_title",
	)

	def autoname(self):
		set_name_from_naming_options(frappe.get_meta(self.doctype).autoname, self)

	def validate(self):
		if not self.route:
			self.route = f"jobs/{frappe.scrub(self.company)}/{frappe.scrub(self.job_title).replace('_', '-')}"
		self.update_closing_date()
		self.validate_dates()
		self.validate_current_vacancies()
		self.validate_published_details()

	def validate_published_details(self):
		"""Publishing an opening needs the details the careers page shows. Checked when it goes live
		(published, or reopened while published), so an older live opening still saves and closes."""
		previous = self.get_doc_before_save()
		was_live = previous and previous.publish and previous.status != "Closed"
		if not self.publish or self.status == "Closed" or was_live:
			return

		has_value = {
			"department": self.department,
			"location": self.location,
			"employment_type": self.employment_type,
			"description": strip_html(self.description or "").strip(),
		}
		missing = [self.meta.get_label(field) for field, value in has_value.items() if not value]
		if missing:
			frappe.throw(
				_("Add {0} before publishing this opening on the website.").format(
					frappe.utils.comma_and([frappe.bold(_(label)) for label in missing])
				),
				title=_("Missing details"),
			)

	def on_update(self):
		self.update_job_requisition_status()

	def update_closing_date(self):
		old_doc = self.get_doc_before_save()
		if not old_doc:
			return

		if old_doc.status == "Open" and self.status == "Closed":
			self.closes_on = None
			if not self.closed_on:
				self.closed_on = getdate()

		elif old_doc.status == "Closed" and self.status == "Open":
			self.closed_on = None

	def validate_dates(self):
		if self.status == "Open":
			self.validate_from_to_dates("posted_on", "closes_on")
		if self.status == "Closed":
			self.validate_from_to_dates("posted_on", "closed_on")

	@frappe.whitelist()
	def get_close_warning(self):
		if not self.is_opening_being_closed():
			return

		if not self.staffing_plan:
			return

		return _(
			"Closing this Job Opening for {1} may not be according to the Staffing Plan {0}.<br><br>"
			"Do you want to close this Job Opening?"
		).format(
			frappe.bold(get_link_to_form("Staffing Plan", self.staffing_plan)),
			frappe.bold(self.designation),
		)

	def validate_current_vacancies(self):
		if self.status == "Closed":
			return

		if not self.staffing_plan:
			staffing_plan = get_active_staffing_plan_details(self.company, self.designation)
			if staffing_plan:
				self.staffing_plan = staffing_plan[0].name
				self.planned_vacancies = staffing_plan[0].vacancies
		elif not self.planned_vacancies:
			self.planned_vacancies = frappe.db.get_value(
				"Staffing Plan Detail",
				{"parent": self.staffing_plan, "designation": self.designation},
				"vacancies",
			)

		if self.staffing_plan and self.planned_vacancies:
			designation_counts = get_designation_counts(self.designation, self.company, self.name)
			current_count = designation_counts["employee_count"] + designation_counts["job_openings"]

			number_of_positions = frappe.db.get_value(
				"Staffing Plan Detail",
				{"parent": self.staffing_plan, "designation": self.designation},
				"number_of_positions",
			)

			if number_of_positions <= current_count:
				frappe.throw(
					_(
						"Job Openings for the designation {0} are already open or the hiring is complete as per the Staffing Plan {1}"
					).format(
						frappe.bold(self.designation), get_link_to_form("Staffing Plan", self.staffing_plan)
					),
					title=_("All vacancies filled"),
				)

	def is_opening_being_closed(self):
		if self.is_new() or self.status != "Closed":
			return False

		return frappe.db.get_value(self.doctype, self.name, "status") == "Open"

	def get_hired_count(self) -> int:
		Applicant = frappe.qb.DocType("Job Applicant")
		Offer = frappe.qb.DocType("Job Offer")
		return (
			frappe.qb.from_(Applicant)
			.join(Offer)
			.on(Offer.job_applicant == Applicant.name)
			.select(Count(Applicant.name).distinct())
			.where((Applicant.job_title == self.name) & (Offer.docstatus == 1) & (Offer.status == "Accepted"))
		).run()[0][0]

	def update_job_requisition_status(self):
		if self.status == "Closed" and self.job_requisition:
			job_requisition = frappe.get_doc("Job Requisition", self.job_requisition)
			if self.get_hired_count() < cint(job_requisition.no_of_positions):
				return

			job_requisition.status = "Filled"
			job_requisition.completed_on = self.closed_on or job_requisition.completed_on or getdate()
			job_requisition.flags.ignore_permissions = True
			job_requisition.flags.ignore_mandatory = True
			job_requisition.save()

	def get_context(self, context):
		context.no_of_applications = frappe.db.count("Job Applicant", {"job_title": self.name})
		context.parents = [{"route": "jobs", "title": _("All Jobs")}]
		context.posted_on = pretty_date(self.posted_on)


def close_expired_job_openings():
	today = getdate()

	Opening = frappe.qb.DocType("Job Opening")
	openings = (
		frappe.qb.from_(Opening)
		.select(Opening.name)
		.where((Opening.status == "Open") & (Opening.closes_on.isnotnull()) & (Opening.closes_on < today))
	).run(pluck=True)

	for d in openings:
		doc = frappe.get_doc("Job Opening", d)
		doc.status = "Closed"
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.save()
