# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Avg
from frappe.utils import flt, get_link_to_form, now

from hrms.hr.doctype.appraisal_cycle.appraisal_cycle import validate_active_appraisal_cycle
from hrms.hr.utils import validate_active_employee


class Appraisal(Document):
	def validate(self):
		if not self.status:
			self.status = "Draft"

		self.set_kra_evaluation_method()

		validate_active_employee(self.employee)
		validate_active_appraisal_cycle(self.appraisal_cycle)
		self.validate_duplicate()

		self.set_goal_score()
		self.calculate_self_appraisal_score()
		self.calculate_avg_feedback_score()
		self.calculate_final_score()

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
		self.set("self_ratings", [])
		self.set("goals", [])

		template = frappe.get_doc("Appraisal Template", self.appraisal_template)

		for entry in template.goals:
			table_name = "goals" if self.rate_goals_manually else "appraisal_kra"

			self.append(
				table_name,
				{
					"kra": entry.key_result_area,
					"per_weightage": entry.per_weightage,
				},
			)

		for entry in template.rating_criteria:
			self.append(
				"self_ratings",
				{
					"criteria": entry.criteria,
					"per_weightage": entry.per_weightage,
				},
			)

		return self

	def calculate_total_score(self):
		total_weightage, total, goal_score_percentage = 0, 0, 0

		if self.rate_goals_manually:
			table = _("Goals")
			for entry in self.goals:
				if flt(entry.score) > 5:
					frappe.throw(_("Row {0}: Goal Score cannot be greater than 5").format(entry.idx))

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
		for entry in self.self_ratings:
			score = flt(entry.rating) * 5 * flt(entry.per_weightage / 100)
			total += flt(score)

		self.self_score = flt(total, self.precision("self_score"))

	def calculate_avg_feedback_score(self, update=False):
		avg_feedback_score = frappe.qb.avg(
			"Employee Performance Feedback",
			"total_score",
			{"employee": self.employee, "appraisal": self.name, "docstatus": 1},
		)

		self.avg_feedback_score = flt(avg_feedback_score, self.precision("avg_feedback_score"))

		if update:
			self.calculate_final_score()
			self.db_update()

	def calculate_final_score(self):
		final_score = (flt(self.total_score) + flt(self.avg_feedback_score) + flt(self.self_score)) / 3

		self.final_score = flt(final_score, self.precision("final_score"))

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
					"criteria": entry.get("criteria"),
					"rating": entry.get("rating"),
					"per_weightage": entry.get("per_weightage"),
				},
			)

		feedback.submit()

		return feedback

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
					& (Goal.appraisal_cycle == self.appraisal_cycle)
				)
			).run()[0][0]

			kra.goal_completion = flt(avg_goal_completion, kra.precision("goal_completion"))
			kra.goal_score = flt(kra.goal_completion * kra.per_weightage / 100, kra.precision("goal_score"))

			if update:
				kra.db_update()

		self.calculate_total_score()

		if update:
			self.calculate_final_score()
			self.db_update()

		return self


@frappe.whitelist()
def get_feedback_history(employee, appraisal):
	data = frappe._dict()
	data.feedback_history = frappe.get_list(
		"Employee Performance Feedback",
		filters={"employee": employee, "appraisal": appraisal, "docstatus": 1},
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

	feedback_count = frappe.db.count(
		"Employee Performance Feedback",
		filters={
			"appraisal": appraisal,
			"employee": employee,
			"docstatus": 1,
		},
	)

	for i in range(1, 6):
		count = frappe.db.count(
			"Employee Performance Feedback",
			filters={
				"appraisal": appraisal,
				"employee": employee,
				"total_score": ("between", [i, i + 0.99]),
				"docstatus": 1,
			},
		)

		percent = flt((count / feedback_count) * 100, 0) if feedback_count else 0
		reviews_per_rating.append(percent)

	data.reviews_per_rating = reviews_per_rating
	data.avg_feedback_score = frappe.db.get_value("Appraisal", appraisal, "avg_feedback_score")

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
