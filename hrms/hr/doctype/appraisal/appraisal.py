# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Avg
from frappe.utils import flt, get_link_to_form, now

from hrms.hr.utils import validate_active_employee


class Appraisal(Document):
	def validate(self):
		if not self.status:
			self.status = "Draft"

		self.set_kra_evaluation_method()

		validate_active_employee(self.employee)
		self.validate_duplicate()

		self.set_goal_score()
		self.calculate_total_score()
		self.calculate_self_appraisal_score()
		self.calculate_avg_feedback_score()

	def validate_duplicate(self):
		Appraisal = frappe.qb.DocType("Appraisal")
		duplicate = (
			frappe.qb.from_(Appraisal)
			.select(Appraisal.name)
			.where(
				(Appraisal.employee == self.employee)
				& (Appraisal.docstatus != 2)
				& (Appraisal.name != self.name)
				& (
					(Appraisal.appraisal_cycle == self.appraisal_cycle)
					| (
						(Appraisal.start_date.between(self.start_date, self.end_date))
						| (Appraisal.end_date.between(self.start_date, self.end_date))
						| ((self.start_date >= Appraisal.start_date) & (self.start_date <= Appraisal.end_date))
						| ((self.end_date >= Appraisal.start_date) & (self.end_date <= Appraisal.end_date))
					)
				)
			)
		).run()
		duplicate = duplicate[0][0] if duplicate else 0

		if duplicate:
			frappe.throw(
				_(
					"Appraisal {0} already exists for Employee {1} for this Appraisal Cycle or overlapping period"
				).format(
					get_link_to_form("Appraisal", duplicate), frappe.bold(self.employee_name)
				),
				exc=frappe.DuplicateEntryError,
				title=_("Duplicate Entry"),
			)

	@frappe.whitelist()
	def set_kra_evaluation_method(self):
		if (
			self.is_new()
			and self.appraisal_cycle
			and (
				frappe.db.get_value("Appraisal Cycle", self.appraisal_cycle, "kra_evaluation_method")
				== "Manual Rating"
			)
		):
			self.rate_goals_manually = 1

	@frappe.whitelist()
	def set_appraisal_template(self):
		"""Sets appraisal template from Appraisee table in Cycle"""
		if not self.appraisal_cycle:
			return

		appraisal_template = frappe.db.get_value(
			"Appraisee",
			{
				"employee": self.employee,
				"parent": self.appraisal_cycle,
			},
			"appraisal_template",
		)

		if appraisal_template:
			self.appraisal_template = appraisal_template
			self.set_kras_and_rating_criteria()

	@frappe.whitelist()
	def set_kras_and_rating_criteria(self):
		if not self.appraisal_template:
			return

		self.set("appraisal_kra", [])
		self.set("ratings", [])

		template = frappe.get_doc("Appraisal Template", self.appraisal_template)

		for entry in template.goals:
			table_name = "goals" if self.rate_goals_manually else "appraisal_kra"

			self.append(
				table_name,
				{
					"kra": entry.kra,
					"per_weightage": entry.per_weightage,
				},
			)

		for entry in template.rating_criteria:
			self.append(
				"ratings",
				{
					"criteria": entry.criteria,
					"per_weightage": entry.per_weightage,
				},
			)

		return self

	def calculate_total_score(self):
		total_weightage, total, goal_score_percentage = 0, 0, 0
		table = ""

		if self.rate_goals_manually:
			table = _("Goals")
			for entry in self.goals:
				entry.score_earned = flt(entry.score) * flt(entry.per_weightage) / 100
				total += flt(entry.score_earned)
				total_weightage += flt(entry.per_weightage)
		else:
			table = _("KRAs")
			for entry in self.appraisal_kra:
				goal_score_percentage += flt(entry.goal_score)
				total_weightage += flt(entry.per_weightage)

			self.goal_score_percentage = flt(goal_score_percentage, self.precision("goal_score_percentage"))
			# convert goal score percentage to total score out of 5
			total = flt(goal_score_percentage) / 20

		if total_weightage and flt(total_weightage, 2) != 100.0:
			frappe.throw(
				_("Total weightage for all {0} must add up to 100. Currently, it is {1}%").format(
					table, total_weightage
				),
				title=_("Incorrect Weightage Allocation"),
			)

		self.total_score = flt(total, self.precision("total_score"))

	def calculate_self_appraisal_score(self):
		total = 0
		for entry in self.ratings:
			score = flt(entry.rating) * 5 * flt(entry.per_weightage / 100)
			total += flt(score)

		self.self_score = total

	def calculate_avg_feedback_score(self, update=False):
		avg_feedback_score = frappe.qb.avg(
			"Employee Performance Feedback",
			"total_score",
			{"employee": self.employee, "appraisal": self.name},
		)

		self.avg_feedback_score = flt(avg_feedback_score, self.precision("avg_feedback_score"))

		if update:
			self.db_update()

	@frappe.whitelist()
	def add_feedback(self, feedback, feedback_ratings):
		feedback = frappe.get_doc(
			{
				"doctype": "Employee Performance Feedback",
				"appraisal": self.name,
				"employee": self.employee,
				"added_on": now(),
				"feedback": feedback,
				"reviewer": frappe.db.get_value("Employee", {"user_id": frappe.session.user}),
			}
		)

		for entry in feedback_ratings:
			feedback.append(
				"feedback_ratings",
				{
					"criteria": entry["criteria"],
					"rating": entry["rating"],
					"per_weightage": entry["per_weightage"],
				},
			)

		feedback.insert()

		return feedback

	@frappe.whitelist()
	def edit_feedback(self, feedback, name):
		doc = frappe.get_doc("Employee Performance Feedback", name)
		doc.update({"feedback": feedback})
		doc.flags.ignore_mandatory = True
		doc.save()

		return doc

	@frappe.whitelist()
	def delete_feedback(self, name):
		frappe.delete_doc("Employee Performance Feedback", name)
		return name

	def set_goal_score(self, update=False):
		for kra in self.appraisal_kra:
			# update progress for all goals as KRA linked could be removed or changed
			Goal = frappe.qb.DocType("Goal")
			avg_goal_completion = (
				frappe.qb.from_(Goal)
				.select(Avg(Goal.progress).as_("avg_goal_completion"))
				.where(
					(Goal.kra == kra.kra)
					& (Goal.employee == self.employee)
					# archived goals should not contribute to progress
					& (Goal.status != "Archived")
					& ((Goal.parent_goal == "") | (Goal.parent_goal.isnull()))
				)
			).run()[0][0]

			kra.goal_completion = flt(avg_goal_completion, kra.precision("goal_completion"))
			kra.goal_score = flt(kra.goal_completion * kra.per_weightage / 100, kra.precision("goal_score"))

			if update:
				kra.db_update()

		if update:
			self.calculate_total_score()
			self.db_update()

		return self


@frappe.whitelist()
def get_feedback_history(employee, appraisal):
	data = frappe._dict()
	data.feedback_history = frappe.get_all(
		"Employee Performance Feedback",
		filters={"employee": employee, "appraisal": appraisal},
		fields=[
			"feedback",
			"reviewer",
			"user",
			"owner",
			"reviewer_name",
			"reviewer_designation",
			"added_on",
			"employee",
			"total_score",
			"name",
		],
		order_by="added_on desc",
	)

	# get percentage of reviews per rating
	reviews_per_rating = []

	for i in range(1, 6):
		count = frappe.db.count(
			"Employee Performance Feedback",
			filters={
				"appraisal": appraisal,
				"employee": employee,
				"total_score": ("between", [i, i + 0.99]),
			},
		)

		percent = flt((count / len(data.feedback_history) or 1) * 100, 0) if count else 0
		reviews_per_rating.append(percent)

	data.reviews_per_rating = reviews_per_rating

	return data


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_kras_for_employee(doctype, txt, searchfield, start, page_len, filters):
	appraisal = frappe.db.get_value(
		"Appraisal",
		{
			"appraisal_cycle": filters.get("appraisal_cycle"),
			"employee": filters.get("employee"),
		},
		"name",
	)

	return frappe.get_all(
		"Appraisal KRA",
		filters={"parent": appraisal, "kra": ("like", "{0}%".format(txt))},
		fields=["kra"],
		as_list=1,
	)
