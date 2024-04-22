# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.naming import set_name_from_naming_options
from frappe.utils import get_link_to_form, getdate, pretty_date
from frappe.website.website_generator import WebsiteGenerator

from hrms.hr.doctype.staffing_plan.staffing_plan import (
	get_active_staffing_plan_details,
	get_designation_counts,
)


class JobOpening(WebsiteGenerator):
	website = frappe._dict(
		template="templates/generators/job_opening.html",
		condition_field="publish",
		page_title_field="job_title",
	)

	def autoname(self):
		self.name = set_name_from_naming_options(frappe.get_meta(self.doctype).autoname, self)

	def validate(self):
		if not self.route:
			self.route = f"jobs/{frappe.scrub(self.company)}/{frappe.scrub(self.job_title).replace('_', '-')}"
		self.update_closing_date()
		self.validate_dates()
		self.validate_current_vacancies()

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

	def validate_current_vacancies(self):
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
					title=_("Vacancies fulfilled"),
				)

	def update_job_requisition_status(self):
		if self.status == "Closed" and self.job_requisition:
			job_requisition = frappe.get_doc("Job Requisition", self.job_requisition)
			job_requisition.status = "Filled"
			job_requisition.completed_on = getdate()
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
