# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
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
		# self.feedback_count = len(self.feedback_table)

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
				frappe.DuplicateEntryError,
			)

	@frappe.whitelist()
	def set_kras(self):
		if not self.appraisal_template:
			return

		self.set("appraisal_kra", [])
		self.set("kra_rating", [])

		template = frappe.get_doc("Appraisal Template", self.appraisal_template)
		for kra in template.goals:
			row = {
				"kra": kra.kra,
				"per_weightage": kra.per_weightage,
			}

			self.append("appraisal_kra", row)
			self.append("kra_rating", row)

		return self

	def calculate_total_score(self):
		total = 0
		for entry in self.appraisal_kra:
			total += flt(entry.goal_score)

		self.total_score = total

	def calculate_self_appraisal_score(self):
		total = 0
		for entry in self.kra_rating:
			score = flt(entry.rating) * 5 * flt(entry.per_weightage / 100)
			total += flt(score)

		self.self_score = total

	def calculate_avg_feedback_score(self):
		avg_feedback_score = frappe.db.get_all(
			"Performance Feedback",
			filters={"employee": self.employee, "appraisal": self.name},
			fields=["avg(total_score) as avg_feedback_score"],
		)[0].avg_feedback_score

		self.avg_feedback_score = flt(avg_feedback_score, self.precision("avg_feedback_score"))

	@frappe.whitelist()
	def add_feedback(self, feedback, kra_rating):
		feedback = frappe.get_doc(
			{
				"doctype": "Performance Feedback",
				"appraisal": self.name,
				"employee": self.employee,
				"added_on": now(),
				"feedback": feedback,
				"reviewer": frappe.db.get_value("Employee", {"user_id": frappe.session.user}),
			}
		)

		for kra in kra_rating:
			feedback.append(
				"kra_rating",
				{
					"kra": kra["kra"],
					"rating": kra["rating"],
					"per_weightage": kra["per_weightage"],
				},
			)

		feedback.insert()

		return feedback.name

	@frappe.whitelist()
	def edit_feedback(self, feedback, name):
		doc = frappe.get_doc("Performance Feedback", name)
		doc.update({"feedback": feedback})
		doc.save()

		return doc.name

	@frappe.whitelist()
	def delete_feedback(self, name):
		frappe.delete_doc("Performance Feedback", name)
		return name


def update_progress_in_appraisal(goal):
	appraisal = frappe.db.exists(
		"Appraisal", {"employee": goal.employee, "appraisal_cycle": goal.appraisal_cycle}
	)
	if not appraisal:
		return

	doc = frappe.get_doc("Appraisal", appraisal)
	for kra in doc.appraisal_kra:
		total_goals = frappe.db.count(
			"Goal", {"kra": kra.kra, "employee": doc.employee, "status": ("!=", "Archived")}
		)
		completed_goals = frappe.db.count(
			"Goal",
			{
				"kra": kra.kra,
				"status": "Completed",
				"employee": doc.employee,
			},
		)
		kra.goal_completion = (
			flt(completed_goals / total_goals * 100, kra.precision("goal_completion")) if total_goals else 0
		)
		kra.goal_score = flt(kra.goal_completion * kra.per_weightage / 100, kra.precision("goal_score"))

	doc.save()


@frappe.whitelist()
def get_feedback_history(employee, appraisal):
	data = frappe._dict()
	data.feedback_history = frappe.get_list(
		"Performance Feedback",
		filters={"employee": employee},
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
			"Performance Feedback",
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
