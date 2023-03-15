# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from frappe.utils.nestedset import NestedSet

from hrms.hr.doctype.appraisal.appraisal import update_progress_in_appraisal


class Goal(NestedSet):
	def validate(self):
		self.set_status()
		self.validate_parent_fields()
		self.validate_from_to_dates(self.start_date, self.end_date)

	def on_update(self):
		update_progress_in_appraisal(self)

	def validate_parent_fields(self):
		if not self.parent_goal:
			return

		parent_details = frappe.db.get_value("Goal", self.parent_goal, ["employee", "kra"], as_dict=True)
		if self.employee != parent_details.employee:
			frappe.throw(
				_("Goal should be owned by the same employee as its parent goal."), title=_("Not Allowed")
			)
		if self.kra != parent_details.kra:
			frappe.throw(
				_("Goal should be aligned with the same KRA as its parent goal."), title=_("Not Allowed")
			)

	def set_status(self, status=None):
		if self.status != "Archived":
			if flt(self.progress) == 0:
				self.status = "Pending"
			elif flt(self.progress) == 100:
				self.status = "Completed"
			elif flt(self.progress) < 100:
				self.status = "In Progress"


@frappe.whitelist()
def get_children(doctype, parent, is_root=False, **filters):
	conditions = [["status", "!=", "Archived"]]

	if filters.get("goal"):
		conditions.append(["parent_goal", "=", filters.get("goal")])
	elif parent and not is_root:
		# via expand child
		conditions.append(["parent_goal", "=", parent])
	else:
		conditions.append(['ifnull(`parent_goal`, "")', "=", ""])

	if filters.get("appraisal_cycle"):
		conditions.append(["appraisal_cycle", "=", filters.get("appraisal_cycle")])

	if filters.get("employee"):
		conditions.append(["employee", "=", filters.get("employee")])

	goals = frappe.get_list(
		doctype,
		fields=[
			"name as value",
			"goal_name as title",
			"is_group as expandable",
			"status",
			"employee",
			"employee_name",
			"appraisal_cycle",
			"progress",
			"kra",
		],
		filters=conditions,
		order_by="employee",
	)

	for goal in goals:
		if goal.expandable:  # group node
			total_goals = frappe.db.count("Goal", dict(parent_goal=goal.value))

			if total_goals > 0:
				completed = frappe.db.count("Goal", {"parent_goal": goal.value, "status": "Completed"}) or 0
				# set completion status of group node
				goal["completion_count"] = _("{0} of {1} Completed").format(completed, total_goals)

	return goals


@frappe.whitelist()
def update_progress(progress, goal):
	goal = frappe.get_doc("Goal", goal)
	goal.progress = progress
	goal.save()

	return progress
