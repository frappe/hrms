import random

import frappe
from frappe.utils import add_days, getdate


def create_leave_allocations(employees, leave_period, company):
	employee_names = {employee.name for employee in employees}
	leave_period_start = getdate(leave_period.from_date)
	leave_period_end = getdate(leave_period.to_date)

	for record in get_demo_records("leave_allocation"):
		if record.get("employee") not in employee_names:
			continue

		if record.get("company") != company:
			continue

		from_date = getdate(record.get("from_date"))
		to_date = getdate(record.get("to_date"))
		if from_date < leave_period_start or to_date > leave_period_end:
			continue

		if frappe.db.exists(
			"Leave Allocation",
			{
				"employee": record.get("employee"),
				"leave_type": record.get("leave_type"),
				"from_date": record.get("from_date"),
				"docstatus": 1,
			},
		):
			continue

		create_and_submit_doc(record)


def create_leave_applications(employees, leave_period):
	employee_names = {employee.name for employee in employees}
	leave_period_start = getdate(leave_period.from_date)
	leave_period_end = getdate(leave_period.to_date)

	for record in get_leave_application_records():
		if record.get("employee") not in employee_names:
			continue

		from_date = getdate(record.get("from_date"))
		to_date = getdate(record.get("to_date"))
		if from_date < leave_period_start or to_date > leave_period_end:
			continue

		create_leave_application(record)


def get_leave_application_records():
	return get_demo_records("leave_application")


def get_demo_records(doctype):
	from hrms.hrms_setup.demo import get_demo_records as get_records

	return get_records(doctype)


def create_and_submit_doc(record):
	previous_in_import = getattr(frappe.flags, "in_import", False)
	if record.get("name"):
		frappe.flags.in_import = True

	try:
		doc = frappe.get_doc(record)
		doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
		if doc.docstatus == 0:
			doc.submit()
	except Exception:
		log_demo_attendance_error(record)
	finally:
		frappe.flags.in_import = previous_in_import


def create_leave_application(record):
	if record.get("name") and frappe.db.exists("Leave Application", record["name"]):
		return

	if not has_leave_days(record):
		return

	previous_in_import = getattr(frappe.flags, "in_import", False)
	if record.get("name"):
		frappe.flags.in_import = True

	try:
		application = frappe.get_doc(record)
		application.insert(ignore_permissions=True, ignore_if_duplicate=True)

		if application.status in ["Approved", "Rejected"] and application.docstatus == 0:
			application.submit()
	except Exception:
		log_demo_attendance_error(record)
	finally:
		frappe.flags.in_import = previous_in_import


def has_leave_days(record):
	from hrms.hr.doctype.leave_application.leave_application import get_number_of_leave_days

	return (
		get_number_of_leave_days(
			record.get("employee"),
			record.get("leave_type"),
			record.get("from_date"),
			record.get("to_date"),
			record.get("half_day"),
			record.get("half_day_date"),
		)
		> 0
	)


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
