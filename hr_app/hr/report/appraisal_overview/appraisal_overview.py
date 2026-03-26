# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters: dict | None = None) -> tuple:
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart_data(data)

	return columns, data, None, chart


def get_columns() -> list[dict]:
	return [
		{
			"fieldname": "employee",
			"fieldtype": "Link",
			"label": _("Employee"),
			"options": "Employee",
			"width": 100,
		},
		{"fieldname": "employee_name", "fieldtype": "Data", "label": _("Employee Name"), "width": 0},
		{
			"fieldname": "designation",
			"fieldtype": "Link",
			"label": _("Designation"),
			"options": "Designation",
			"width": 100,
		},
		{
			"fieldname": "appraisal_cycle",
			"fieldtype": "Link",
			"label": _("Appraisal Cycle"),
			"options": "Appraisal Cycle",
			"width": 100,
		},
		{
			"fieldname": "appraisal",
			"fieldtype": "Link",
			"label": _("Appraisal"),
			"options": "Appraisal",
			"width": 0,
		},
		{"fieldname": "feedback_count", "fieldtype": "Int", "label": _("Feedback Count"), "width": 0},
		{
			"fieldname": "avg_feedback_score",
			"fieldtype": "Float",
			"label": _("Avg Feedback Score"),
			"width": 0,
		},
		{"fieldname": "goal_score", "fieldtype": "Float", "label": _("Goal Score"), "width": 0},
		{"fieldname": "self_score", "fieldtype": "Float", "label": _("Self Score"), "width": 0},
		{"fieldname": "final_score", "fieldtype": "Float", "label": _("Final Score"), "width": 0},
		{
			"fieldname": "department",
			"fieldtype": "Link",
			"label": _("Department"),
			"options": "Department",
			"width": 150,
		},
	]


def get_data(filters: dict | None = None) -> list[dict]:
	Appraisal = frappe.qb.DocType("Appraisal")
	query = (
		frappe.qb.from_(Appraisal)
		.select(
			Appraisal.employee,
			Appraisal.employee_name,
			Appraisal.designation,
			Appraisal.department,
			Appraisal.appraisal_cycle,
			Appraisal.name.as_("appraisal"),
			Appraisal.avg_feedback_score,
			Appraisal.total_score.as_("goal_score"),
			Appraisal.self_score,
			Appraisal.final_score,
		)
		.where(Appraisal.docstatus != 2)
	)

	for condition in ["appraisal_cycle", "employee", "department", "designation", "company"]:
		if filters.get(condition):
			query = query.where(Appraisal[condition] == filters.get(condition))

	query = query.orderby(Appraisal.appraisal_cycle)
	query = query.orderby(Appraisal.final_score, order=frappe.qb.desc)
	appraisals = query.run(as_dict=True)

	for row in appraisals:
		row["feedback_count"] = frappe.db.count(
			"Employee Performance Feedback", {"appraisal": row.appraisal, "docstatus": 1}
		)

	return appraisals


def get_chart_data(data: list[dict]) -> dict:
	labels = []
	goal_score = []
	self_score = []
	feedback_score = []
	final_score = []

	# show only top 10 in the chart for better readability
	for row in data[:10]:
		labels.append(row.employee_name)
		goal_score.append(row.goal_score)
		self_score.append(row.self_score)
		feedback_score.append(row.avg_feedback_score)
		final_score.append(row.final_score)

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("Goal Score"), "values": goal_score},
				{"name": _("Self Score"), "values": self_score},
				{"name": _("Feedback Score"), "values": feedback_score},
				{"name": _("Final Score"), "values": final_score},
			],
		},
		"type": "bar",
		"barOptions": {"spaceRatio": 0.7},
		"height": 250,
	}
