# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.naming import set_name_from_naming_options
from frappe.utils import get_link_to_form, getdate
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
			self.route = frappe.scrub(self.job_title).replace("_", "-")
		self.validate_dates()
		self.validate_current_vacancies()
		self.update_job_requisition_status()

	def on_update(self):
		old_doc = self.get_doc_before_save()
		if not old_doc:
			return

		if old_doc.status == "Open" and self.status == "Closed":
			today = getdate()
			self.closes_on = None
			if not self.closed_on:
				self.closed_on = today
			self.save()

		elif old_doc.status == "Closed" and self.status == "Open":
			self.closed_on = None
			self.save()

	def validate_dates(self):
		self.validate_past_future("posted_on", True)
		if self.status == "Open":
			self.validate_past_future("closes_on", False)
		if self.status == "Closed":
			self.validate_from_to_dates("posted_on", "closed_on")
			self.validate_past_future("closed_on", True)

	def validate_past_future(self, field, is_past):
		date = self.get(field)
		label = self.meta.get_label(field)
		today = getdate()
		if is_past:
			if getdate(date) > today:
				frappe.throw(_(f"{frappe.bold(label)} cannot be a future date"))
		else:
			if getdate(date) < today:
				frappe.throw(_(f"{frappe.bold(label)} cannot be a past date"))

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
			staffing_plan_company = frappe.db.get_value("Staffing Plan", self.staffing_plan, "company")

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
		context.parents = [{"route": "jobs", "title": _("All Jobs")}]


def get_list_context(context):
	context.title = _("Jobs")
	context.introduction = _("Current Job Openings")
	context.get_list = get_job_openings


def get_job_openings(
	doctype, txt=None, filters=None, limit_start=0, limit_page_length=20, order_by=None
):
	fields = [
		"name",
		"status",
		"job_title",
		"description",
		"publish_salary_range",
		"lower_range",
		"upper_range",
		"currency",
		"job_application_route",
		"salary_type",
	]

	filters = filters or {}
	filters.update({"status": "Open"})

	if txt:
		filters.update(
			{"job_title": ["like", "%{0}%".format(txt)], "description": ["like", "%{0}%".format(txt)]}
		)

	return frappe.get_all(
		doctype, filters, fields, start=limit_start, page_length=limit_page_length, order_by=order_by
	)


def close_expired_job_openings():
	today = getdate()
	for d in frappe.get_all(
		"Job Opening",
		filters={"Status": "Open", "closes_on": ["<=", today]},
		fields=["name", "closes_on"],
	):
		frappe.set_value("Job Opening", d.name, "status", "Closed")
