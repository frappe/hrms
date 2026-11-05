# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, nowdate
from frappe.utils.nestedset import get_descendants_of


class SubsidiaryCompanyError(frappe.ValidationError):
	pass


class ParentCompanyError(frappe.ValidationError):
	pass


class StaffingPlan(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.staffing_plan_detail.staffing_plan_detail import StaffingPlanDetail

		amended_from: DF.Link | None
		company: DF.Link
		department: DF.Link | None
		from_date: DF.Date
		staffing_details: DF.Table[StaffingPlanDetail]
		to_date: DF.Date
		total_estimated_budget: DF.Currency
	# end: auto-generated types

	def validate(self):
		self.validate_period()
		self.validate_duplicate_designations()
		self.set_total_estimated_budget()
		self.validate_details()

	def validate_period(self):
		# Validate Dates
		if self.from_date and self.to_date and self.from_date > self.to_date:
			frappe.throw(_("From Date cannot be greater than To Date"))

	def validate_duplicate_designations(self):
		designations = set()
		for detail in self.get("staffing_details"):
			if detail.designation in designations:
				frappe.throw(
					_("Row {0}: Designation {1} is already added in this Staffing Plan").format(
						detail.idx, frappe.bold(detail.designation)
					),
					frappe.DuplicateEntryError,
				)
			designations.add(detail.designation)

	def validate_details(self):
		for detail in self.get("staffing_details"):
			self.validate_current_openings(detail)
			self.validate_overlap(detail)
			self.validate_with_subsidiary_plans(detail)
			self.validate_with_parent_plan(detail)

	def set_total_estimated_budget(self):
		self.total_estimated_budget = 0

		for detail in self.get("staffing_details"):
			# Set readonly fields
			designation_counts = get_designation_counts(detail.designation, self.company)
			detail.current_count = designation_counts["employee_count"]
			detail.current_openings = designation_counts["job_openings"]
			self.set_number_of_positions(detail)
			detail.total_estimated_cost = 0
			if detail.number_of_positions > 0:
				if detail.vacancies and detail.estimated_cost_per_position:
					detail.total_estimated_cost = cint(detail.vacancies) * flt(
						detail.estimated_cost_per_position
					)

			self.total_estimated_budget += detail.total_estimated_cost

	def validate_current_openings(self, detail):
		if cint(detail.vacancies) < cint(detail.current_openings):
			frappe.throw(
				_("Row {0}: Vacancies for {1} cannot be lower than the current openings ({2})").format(
					detail.idx, frappe.bold(detail.designation), cint(detail.current_openings)
				)
			)

	def set_number_of_positions(self, detail):
		detail.number_of_positions = cint(detail.vacancies) + cint(detail.current_count)

	def validate_overlap(self, staffing_plan_detail):
		# Validate if any submitted Staffing Plan exist for any Designations in this plan
		# and spd.vacancies>0 ?
		spd = frappe.qb.DocType("Staffing Plan Detail")
		sp = frappe.qb.DocType("Staffing Plan")
		overlap = (
			frappe.qb.from_(spd)
			.join(sp)
			.on(spd.parent == sp.name)
			.select(spd.parent)
			.where(
				(spd.designation == staffing_plan_detail.designation)
				& (sp.docstatus == 1)
				& (sp.to_date >= self.from_date)
				& (sp.from_date <= self.to_date)
				& (sp.company == self.company)
			)
		).run()
		if overlap and overlap[0][0]:
			frappe.throw(
				_("Staffing Plan {0} already exist for designation {1}").format(
					overlap[0][0], staffing_plan_detail.designation
				)
			)

	def validate_with_parent_plan(self, staffing_plan_detail):
		if not frappe.get_cached_value("Company", self.company, "parent_company"):
			return  # No parent, nothing to validate

		# Get staffing plan applicable for the company (Parent Company)
		parent_plan_details = get_active_staffing_plan_details(
			self.company, staffing_plan_detail.designation, self.from_date, self.to_date
		)
		if not parent_plan_details:
			return  # no staffing plan for any parent Company in hierarchy

		# Fetch parent company which owns the staffing plan. NOTE: Parent could be higher up in the hierarchy
		parent_company = frappe.db.get_value("Staffing Plan", parent_plan_details[0].name, "company")
		# Parent plan available, validate with parent, siblings as well as children of staffing plan Company
		if cint(staffing_plan_detail.vacancies) > cint(parent_plan_details[0].vacancies) or flt(
			staffing_plan_detail.total_estimated_cost
		) > flt(parent_plan_details[0].total_estimated_cost):
			frappe.throw(
				_(
					"You can only plan for upto {0} vacancies and budget {1} for {2} as per staffing plan {3} for parent company {4}."
				).format(
					cint(parent_plan_details[0].vacancies),
					parent_plan_details[0].total_estimated_cost,
					frappe.bold(staffing_plan_detail.designation),
					parent_plan_details[0].name,
					parent_company,
				),
				ParentCompanyError,
			)

		all_sibling_details = self.get_planned_for_subsidiaries(
			parent_company, staffing_plan_detail.designation
		)

		if (
			cint(parent_plan_details[0].vacancies)
			< (cint(staffing_plan_detail.vacancies) + cint(all_sibling_details.vacancies))
		) or (
			flt(parent_plan_details[0].total_estimated_cost)
			< (flt(staffing_plan_detail.total_estimated_cost) + flt(all_sibling_details.total_estimated_cost))
		):
			frappe.throw(
				_(
					"{0} vacancies and {1} budget for {2} already planned for subsidiary companies of {3}. You can only plan for upto {4} vacancies and and budget {5} as per staffing plan {6} for parent company {3}."
				).format(
					cint(all_sibling_details.vacancies),
					all_sibling_details.total_estimated_cost,
					frappe.bold(staffing_plan_detail.designation),
					parent_company,
					cint(parent_plan_details[0].vacancies),
					parent_plan_details[0].total_estimated_cost,
					parent_plan_details[0].name,
				)
			)

	def validate_with_subsidiary_plans(self, staffing_plan_detail):
		children_details = self.get_planned_for_subsidiaries(self.company, staffing_plan_detail.designation)

		if cint(staffing_plan_detail.vacancies) < cint(children_details.vacancies) or flt(
			staffing_plan_detail.total_estimated_cost
		) < flt(children_details.total_estimated_cost):
			frappe.throw(
				_(
					"Subsidiary companies have already planned for {1} vacancies at a budget of {2}. Staffing Plan for {0} should allocate more vacancies and budget for {3} than planned for its subsidiary companies"
				).format(
					self.company,
					cint(children_details.vacancies),
					children_details.total_estimated_cost,
					frappe.bold(staffing_plan_detail.designation),
				),
				SubsidiaryCompanyError,
			)

	def get_planned_for_subsidiaries(self, company, designation):
		lft, rgt = frappe.get_cached_value("Company", company, ["lft", "rgt"])
		spd = frappe.qb.DocType("Staffing Plan Detail")
		sp = frappe.qb.DocType("Staffing Plan")
		Company = frappe.qb.DocType("Company")
		plans = (
			frappe.qb.from_(spd)
			.join(sp)
			.on(spd.parent == sp.name)
			.join(Company)
			.on(sp.company == Company.name)
			.select(Company.lft, Company.rgt, spd.vacancies, spd.total_estimated_cost)
			.where(
				(spd.designation == designation)
				& (sp.docstatus == 1)
				& (sp.to_date >= self.from_date)
				& (sp.from_date <= self.to_date)
				& (Company.lft > lft)
				& (Company.rgt < rgt)
			)
		).run(as_dict=True)

		planned_companies = [(d.lft, d.rgt) for d in plans]
		if company != self.company:
			planned_companies.append(tuple(frappe.get_cached_value("Company", self.company, ["lft", "rgt"])))

		totals = frappe._dict(vacancies=0, total_estimated_cost=0)
		for d in plans:
			if any(p_lft < d.lft and p_rgt > d.rgt for p_lft, p_rgt in planned_companies):
				continue
			totals.vacancies += cint(d.vacancies)
			totals.total_estimated_cost += flt(d.total_estimated_cost)

		return totals

	@frappe.whitelist()
	def set_job_requisitions(self, job_reqs: list[str]) -> Document:
		if job_reqs:
			requisitions = frappe.db.get_list(
				"Job Requisition",
				filters={"name": ["in", job_reqs]},
				fields=["designation", "no_of_positions", "expected_compensation"],
			)

			self.staffing_details = []
			for req in requisitions:
				if row := next((d for d in self.staffing_details if d.designation == req.designation), None):
					total_cost = cint(row.vacancies) * flt(row.estimated_cost_per_position) + cint(
						req.no_of_positions
					) * flt(req.expected_compensation)
					row.vacancies = cint(row.vacancies) + cint(req.no_of_positions)
					row.number_of_positions = cint(row.number_of_positions) + cint(req.no_of_positions)
					row.estimated_cost_per_position = total_cost / row.vacancies if row.vacancies else 0
					continue

				current_count = get_designation_counts(req.designation, self.company)["employee_count"]
				self.append(
					"staffing_details",
					{
						"designation": req.designation,
						"vacancies": req.no_of_positions,
						"estimated_cost_per_position": req.expected_compensation,
						"number_of_positions": cint(current_count) + cint(req.no_of_positions),
					},
				)

		return self


@frappe.whitelist()
def get_designation_counts(designation: str, company: str, job_opening: str | None = None) -> dict | bool:
	if not (frappe.has_permission("Staffing Plan", "read") or frappe.has_permission("Job Opening", "read")):
		frappe.throw_permission_error()

	if not designation:
		return False

	company_set = get_descendants_of("Company", company)
	company_set.append(company)

	employee_count = frappe.db.count(
		"Employee", {"designation": designation, "status": "Active", "company": ("in", company_set)}
	)

	filters = {"designation": designation, "status": "Open", "company": ("in", company_set)}
	if job_opening:
		filters["name"] = ("!=", job_opening)

	job_openings = frappe.db.count("Job Opening", filters)

	return {"employee_count": employee_count, "job_openings": job_openings}


@frappe.whitelist()
def get_active_staffing_plan_details(
	company: str,
	designation: str,
	from_date: str | datetime.date | None = None,
	to_date: str | datetime.date | None = None,
) -> list[dict] | None:
	frappe.has_permission("Staffing Plan", "read", throw=True)

	if from_date is None:
		from_date = getdate(nowdate())
	if to_date is None:
		to_date = getdate(nowdate())
	if not company or not designation:
		frappe.throw(_("Please select Company and Designation"))

	spd = frappe.qb.DocType("Staffing Plan Detail")
	sp = frappe.qb.DocType("Staffing Plan")
	staffing_plan = (
		frappe.qb.from_(spd)
		.join(sp)
		.on(spd.parent == sp.name)
		.select(sp.name, spd.vacancies, spd.total_estimated_cost)
		.where(
			(sp.company == company)
			& (spd.designation == designation)
			& (sp.docstatus == 1)
			& (sp.to_date >= from_date)
			& (sp.from_date <= to_date)
		)
		.run(as_dict=1)
	)

	if not staffing_plan:
		parent_company = frappe.get_cached_value("Company", company, "parent_company")
		if parent_company:
			staffing_plan = get_active_staffing_plan_details(parent_company, designation, from_date, to_date)

	# Only a single staffing plan can be active for a designation on given date
	return staffing_plan if staffing_plan else None
