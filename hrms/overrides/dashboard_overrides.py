# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from frappe import _


def get_dashboard_for_employee(data):
	data["transactions"].extend(
		[
			{"label": _("Attendance"), "items": ["Attendance", "Attendance Request", "Employee Checkin"]},
			{
				"label": _("Leave"),
				"items": ["Leave Application", "Leave Allocation", "Leave Policy Assignment"],
			},
			{
				"label": _("Lifecycle"),
				"items": [
					"Employee Onboarding",
					"Employee Transfer",
					"Employee Promotion",
					"Employee Grievance",
				],
			},
			{
				"label": _("Exit"),
				"items": ["Employee Separation", "Exit Interview", "Full and Final Statement"],
			},
			{"label": _("Shift"), "items": ["Shift Request", "Shift Assignment"]},
			{"label": _("Expense"), "items": ["Expense Claim", "Travel Request", "Employee Advance"]},
			{"label": _("Benefit"), "items": ["Employee Benefit Application", "Employee Benefit Claim"]},
			{
				"label": _("Payroll"),
				"items": [
					"Salary Structure Assignment",
					"Salary Slip",
					"Additional Salary",
					"Timesheet",
					"Employee Incentive",
					"Retention Bonus",
					"Bank Account",
				],
			},
			{
				"label": _("Training"),
				"items": ["Training Event", "Training Result", "Training Feedback", "Employee Skill Map"],
			},
			{"label": _("Evaluation"), "items": ["Appraisal"]},
		]
	)

	data["non_standard_fieldnames"].update(
		{"Bank Account": "party", "Employee Grievance": "raised_by"}
	)
	data.update(
		{
			"heatmap": True,
			"heatmap_message": _("This is based on the attendance of this Employee"),
			"fieldname": "employee",
			"method": "hrms.overrides.employee_master.get_timeline_data",
		}
	)
	return data


def get_dashboard_for_holiday_list(data):
	data["non_standard_fieldnames"].update({"Leave Period": "optional_holiday_list"})

	data["transactions"].append({"items": ["Leave Period", "Shift Type"]})

	return data


def get_dashboard_for_timesheet(data):
	data["transactions"].append({"label": _("Payroll"), "items": ["Salary Slip"]})

	return data


def get_dashboard_for_project(data):
	data["transactions"].append(
		{"label": _("Claims"), "items": ["Expense Claim"]},
	)

	return data
