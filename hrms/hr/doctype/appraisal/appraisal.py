# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, now

from hrms.hr.utils import validate_active_employee


class Appraisal(Document):
	def validate(self):
		if not self.status:
			self.status = "Draft"

		validate_active_employee(self.employee)
		self.validate_existing_appraisal()
		self.calculate_total_score()
		self.calculate_self_appraisal_score()
		self.calculate_avg_feedback_score()
		self.feedbacks = len(self.feedbacks_table)

	def validate_existing_appraisal(self):
		duplicate = frappe.db.sql(
			"""select name from `tabAppraisal` where employee=%s
			and (status='Submitted' or status='Completed')
			and (appraisal_cycle=%s)""",
			(self.employee, self.appraisal_cycle),
		)
		if duplicate:
			frappe.throw(
				_("Appraisal {0} already created for Employee {1} for this Appraisal Cycle").format(
					duplicate[0][0], self.employee_name
				)
			)

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
		self.avg_feedback_score = (
			frappe.db.sql(
				"""
			select avg(total_score) from `tabPerformance Feedback`
			where for_employee=%s
			""",
				(self.employee,),
				as_list=1,
			)[0][0]
			or 0
		)

	@frappe.whitelist()
	def add_feedback(self, feedback, kra_rating):
		perf = frappe.new_doc("Performance Feedback")
		perf.update(
			{
				"for_employee": self.employee,
				"added_on": now(),
				"feedback": feedback,
				"given_by": frappe.db.get_value("Employee", {"user_id": frappe.session.user}),
				"user": frappe.session.user,
			}
		)
		for kra in kra_rating:
			perf.append(
				"kra_rating",
				{
					"kra": kra["kra"],
					"rating": kra["rating"],
					"per_weightage": kra["per_weightage"],
				},
			)

		perf.save()
		self.calculate_avg_feedback_score()
		self.save()
		# self.append(
		# 	"feedbacks_table",
		# 	{
		# 		"feedback": feedback,
		# 		"given_by": frappe.db.get_value("Employee", {"user_id": frappe.session.user}),
		# 		"user": frappe.session.user,
		# 		"added_on": now(),
		# 		"for_employee": self.employee,
		# 	},
		# )
		# self.save()

	@frappe.whitelist()
	def edit_feedback(self, feedback, row_id):
		for d in self.feedbacks_table:
			if cstr(d.name) == row_id:
				d.feedback = feedback
				d.db_update()
		self.calculate_avg_feedback_score()
		self.save()

	@frappe.whitelist()
	def delete_feedback(self, row_id):
		frappe.delete_doc("Performance Feedback", row_id)
		self.calculate_avg_feedback_score()
		self.save()
		# for d in self.feedbacks_table:
		# 	if cstr(d.name) == row_id:
		# 		self.remove(d)
		# 		break
		# self.save()


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
def get_feedbacks(employee):
	return frappe.db.get_all(
		"Performance Feedback",
		filters={"for_employee": employee},
		fields=[
			"feedback",
			"given_by",
			"user",
			"owner",
			"given_by_name",
			"added_on",
			"for_employee",
			"total_score",
			"name",
		],
	)
