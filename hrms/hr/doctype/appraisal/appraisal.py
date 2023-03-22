# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.functions import Avg
from frappe.utils import flt, now

from hrms.hr.utils import validate_active_employee


class Appraisal(Document):
	def before_insert(self):
		self.validate_duplicate()

	def validate(self):
		if not self.status:
			self.status = "Draft"

		validate_active_employee(self.employee)

		self.calculate_total_score()
		self.calculate_self_appraisal_score()
		self.calculate_avg_feedback_score()

	def validate_duplicate(self):
		duplicate = frappe.db.exists(
			"Appraisal",
			{
				"employee": self.employee,
				"docstatus": ["!=", 2],
				"appraisal_cycle": self.appraisal_cycle,
			},
		)

		if duplicate:
			frappe.throw(
				_("Appraisal {0} already created for Employee {1} for this Appraisal Cycle").format(
					duplicate, self.employee_name
				),
				exc=frappe.DuplicateEntryError,
				title=_("Duplicate Entry"),
			)

	@frappe.whitelist()
	def set_kras_and_rating_criteria(self):
		if not self.appraisal_template:
			return

		self.set("appraisal_kra", [])
		self.set("ratings", [])

		template = frappe.get_doc("Appraisal Template", self.appraisal_template)

		for entry in template.goals:
			self.append(
				"appraisal_kra",
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
		total = 0
		for entry in self.appraisal_kra:
			total += flt(entry.goal_score)

		self.total_score = total

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

		return feedback.name

	@frappe.whitelist()
	def edit_feedback(self, feedback, name):
		doc = frappe.get_doc("Employee Performance Feedback", name)
		doc.update({"feedback": feedback})
		doc.save()

		return doc.name

	@frappe.whitelist()
	def delete_feedback(self, name):
		frappe.delete_doc("Employee Performance Feedback", name)
		return name

	def update_goal_progress(self, goal):
		for kra in self.appraisal_kra:
			if kra.kra != goal.kra:
				continue

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

			kra.db_update()

			return kra.goal_score


@frappe.whitelist()
def get_feedback_history(employee, appraisal):
	data = frappe._dict()
	data.feedback_history = frappe.get_list(
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
