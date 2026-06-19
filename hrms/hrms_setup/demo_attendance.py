import random

import frappe
from frappe.utils import add_days, getdate


def generate_attendance(employees, leave_period):
	current_date = getdate()
	three_months_ago = add_days(current_date, -90)

	for emp in employees:
		emp_doc = frappe.get_doc("Employee", emp.name)
		join_date = getdate(emp_doc.date_of_joining)

		if join_date > current_date:
			continue

		emp_start = max(join_date, three_months_ago)
		emp_end = current_date

		emp_approved_leaves = get_employee_leaves(emp.name, emp_start, emp_end, "Approved")
		holidays = get_employee_holidays(emp.name, emp_start, emp_end)

		current_day = emp_start
		days_since_start = 0
		consecutive_absences = 0

		while current_day <= emp_end:
			date_str = current_day.strftime("%Y-%m-%d")

			if date_str in holidays:
				consecutive_absences = 0
				current_day = add_days(current_day, 1)
				days_since_start += 1
				continue
			elif date_str in emp_approved_leaves:
				leave_type = emp_approved_leaves[date_str]
				if leave_type == "Half Day":
					status = "Half Day"
				else:
					status = "On Leave"
				consecutive_absences = 0
			else:
				rand = random.random()

				if days_since_start < 3:
					status = "Present"
					consecutive_absences = 0
				elif consecutive_absences >= 3:
					if random.random() > 0.3:
						status = "Present"
						consecutive_absences = 0
					else:
						status = "Absent"
						consecutive_absences += 1
				elif rand < 0.85:
					status = "Present"
					consecutive_absences = 0
				elif rand < 0.93:
					status = "Absent"
					consecutive_absences += 1
				else:
					status = "Half Day"
					consecutive_absences = 0

			existing = frappe.db.exists(
				"Attendance",
				{
					"employee": emp.name,
					"attendance_date": date_str,
				},
			)

			if not existing:
				try:
					attendance = frappe.get_doc(
						{
							"doctype": "Attendance",
							"employee": emp.name,
							"attendance_date": date_str,
							"status": status,
							"company": emp_doc.company,
						}
					)
					attendance.insert(ignore_permissions=True)
					attendance.submit()
				except Exception:
					log_demo_attendance_error(
						{
							"doctype": "Attendance",
							"employee": emp.name,
							"attendance_date": date_str,
							"status": status,
							"company": emp_doc.company,
						}
					)

			current_day = add_days(current_day, 1)
			days_since_start += 1


def get_employee_leaves(employee, from_date, to_date, status="Approved"):
	leaves = {}

	leave_applications = frappe.get_all(
		"Leave Application",
		filters={
			"employee": employee,
			"from_date": ("<=", to_date),
			"to_date": (">=", from_date),
			"status": status,
			"docstatus": 1,
		},
		fields=["from_date", "to_date", "leave_type", "half_day", "half_day_date"],
	)

	for leave in leave_applications:
		current = getdate(leave.from_date)
		while current <= getdate(leave.to_date):
			date_key = current.strftime("%Y-%m-%d")
			if leave.half_day and leave.half_day_date:
				if current == getdate(leave.half_day_date):
					leaves[date_key] = "Half Day"
			else:
				leaves[date_key] = leave.leave_type
			current = add_days(current, 1)

	return leaves


def get_employee_holidays(employee, from_date, to_date):
	holidays = {}

	employee_doc = frappe.get_doc("Employee", employee)
	branch = employee_doc.branch

	holiday_lists = frappe.get_all(
		"Holiday List",
		filters={"from_date": ("<=", to_date), "to_date": (">=", from_date)},
		fields=["name", "holiday_list_name"],
	)

	branch_holidays = [h for h in holiday_lists if branch and branch in h.holiday_list_name]
	if not branch_holidays:
		branch_holidays = holiday_lists[:1] if holiday_lists else []

	for hl in branch_holidays:
		holiday_list_doc = frappe.get_doc("Holiday List", hl.name)
		for holiday in holiday_list_doc.holidays:
			hd = getdate(holiday.holiday_date)
			if from_date <= hd <= to_date:
				holidays[holiday.holiday_date.strftime("%Y-%m-%d")] = True

	return holidays


def log_demo_attendance_error(record):
	frappe.log_error(
		title=f"Failed to create HR demo {record.get('doctype')}",
		message=frappe.get_traceback(),
	)
