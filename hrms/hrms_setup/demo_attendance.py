import random
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.utils import add_days, getdate, today


def create_leave_allocations(employees, leave_period, company):
	available_leave_types = frappe.get_all(
		"Leave Type",
		fields=["name", "leave_type_name"],
	)

	if not available_leave_types:
		frappe.publish_realtime("demo_progress", {"message": "No Leave Types found, skipping allocations"})
		return

	leave_type_map = {}
	for lt in available_leave_types:
		name_lower = lt.name.lower()
		if "annual" in name_lower or "earned" in name_lower or "vacation" in name_lower:
			leave_type_map["annual"] = lt.name
		elif "sick" in name_lower:
			leave_type_map["sick"] = lt.name
		elif "personal" in name_lower or "casual" in name_lower:
			leave_type_map["personal"] = lt.name

	allocation_rules = {
		"annual": {"confirmed": 12, "new": 6, "probation": 0, "intern": 0},
		"sick": {"confirmed": 8, "new": 4, "probation": 3, "intern": 0},
		"personal": {"confirmed": 5, "new": 2, "probation": 2, "intern": 0},
	}

	created = 0
	skipped = 0

	leave_period_start = getdate(leave_period.from_date)
	leave_period_end = getdate(leave_period.to_date)
	current_date = getdate()

	for emp in employees:
		emp_doc = frappe.get_doc("Employee", emp.name)
		emp_status = get_employee_status(emp_doc)

		join_date = getdate(emp_doc.date_of_joining)
		if join_date > current_date:
			continue

		for category, leave_type_name in leave_type_map.items():
			full_allocation = allocation_rules.get(category, {}).get(emp_status, 0)
			if full_allocation == 0:
				continue

			months_in_period = calculate_months_in_period(join_date, leave_period_start, leave_period_end)
			if months_in_period <= 0:
				continue

			allocation_count = prorate_leave(full_allocation, months_in_period)
			if allocation_count < 1:
				allocation_count = 1

			existing = frappe.db.exists(
				"Leave Allocation",
				{
					"employee": emp.name,
					"leave_type": leave_type_name,
					"docstatus": ("!=", 2),
				},
			)
			if existing:
				skipped += 1
				continue

			try:
				effective_from = max(join_date, leave_period_start)
				effective_to = min(current_date, leave_period_end)

				allocation = frappe.get_doc(
					{
						"doctype": "Leave Allocation",
						"employee": emp.name,
						"leave_type": leave_type_name,
						"from_date": effective_from,
						"to_date": effective_to,
						"new_leaves_allocated": allocation_count,
						"company": company,
					}
				)
				allocation.insert(ignore_permissions=True)
				allocation.submit()
				created += 1
			except Exception:
				pass

	frappe.publish_realtime(
		"demo_progress",
		{"message": f"Created {created} Leave Allocations, skipped {skipped}"},
	)


def create_leave_applications(employees, leave_period):
	available_leave_types = frappe.get_all(
		"Leave Type",
		fields=["name"],
	)

	if not available_leave_types:
		frappe.publish_realtime("demo_progress", {"message": "No Leave Types found, skipping applications"})
		return

	leave_types = [lt.name for lt in available_leave_types]
	if not leave_types:
		leave_types = ["Sick Leave", "Annual Leave", "Casual Leave", "Personal Leave"]

	leave_period_start = getdate(leave_period.from_date)
	leave_period_end = getdate(leave_period.to_date)
	current_date = getdate()

	statuses = ["Approved", "Pending", "Rejected"]
	status_weights = [0.6, 0.25, 0.15]

	created = 0
	skipped = 0

	for emp in employees:
		emp_doc = frappe.get_doc("Employee", emp.name)
		emp_status = get_employee_status(emp_doc)

		join_date = getdate(emp_doc.date_of_joining)
		if join_date > current_date:
			continue

		emp_start = max(join_date, leave_period_start)
		emp_end = min(current_date, leave_period_end)

		tenure_days = (emp_end - emp_start).days
		if tenure_days < 7:
			continue

		num_leaves = calculate_leaves_for_tenure(emp_start, emp_end, emp_status)
		leave_dates = generate_leaves_across_tenure(num_leaves, emp_start, emp_end, emp.name)

		half_day_date = None
		if leave_dates and random.random() > 0.4:
			half_day_date = random.choice(leave_dates)

		backdated_leave = None
		if random.random() > 0.6:
			backdated_date = current_date - timedelta(days=random.randint(5, 20))
			if emp_start <= backdated_date <= emp_end:
				backdated_leave = backdated_date

		for leave_date in leave_dates:
			leave_type = random.choice(leave_types)
			if emp_status in ["probation", "intern"] and (
				"annual" in leave_type.lower() or "earned" in leave_type.lower()
			):
				leave_type = random.choice(
					[t for t in leave_types if "annual" not in t.lower() and "earned" not in t.lower()]
				)
				if not leave_type:
					leave_type = random.choice(leave_types)

			is_half_day = leave_date == half_day_date
			duration = 0.5 if is_half_day else random.choice([1, 1, 2])

			leave_date_to = add_days(leave_date, duration - 1)
			if leave_date_to > emp_end:
				leave_date_to = emp_end

			existing = frappe.db.exists(
				"Leave Application",
				{
					"employee": emp.name,
					"from_date": ("<=", leave_date_to),
					"to_date": (">=", leave_date),
					"docstatus": ("!=", 2),
				},
			)
			if existing:
				skipped += 1
				continue

			try:
				status = random.choices(statuses, weights=status_weights)[0]
				if emp_status == "probation" and random.random() > 0.4:
					status = "Rejected"
				elif emp_status == "intern":
					status = random.choices(statuses, weights=[0.3, 0.5, 0.2])[0]

				application = frappe.get_doc(
					{
						"doctype": "Leave Application",
						"employee": emp.name,
						"leave_type": leave_type,
						"from_date": leave_date,
						"to_date": leave_date_to,
						"status": status,
						"company": emp_doc.company,
						"half_day": 1 if is_half_day else 0,
						"half_day_date": leave_date if is_half_day else None,
					}
				)
				application.insert(ignore_permissions=True)

				if status == "Approved":
					application.submit()
				created += 1
			except Exception:
				pass

		if backdated_leave:
			existing = frappe.db.exists(
				"Leave Application",
				{
					"employee": emp.name,
					"from_date": ("<=", backdated_leave),
					"to_date": (">=", backdated_leave),
					"docstatus": ("!=", 2),
				},
			)
			if not existing:
				try:
					leave_type = random.choice(leave_types)
					application = frappe.get_doc(
						{
							"doctype": "Leave Application",
							"employee": emp.name,
							"leave_type": leave_type,
							"from_date": backdated_leave,
							"to_date": backdated_leave,
							"status": "Approved",
							"company": emp_doc.company,
							"reason": "Medical emergency",
						}
					)
					application.insert(ignore_permissions=True)
					application.submit()
					created += 1
				except Exception:
					pass

	frappe.publish_realtime(
		"demo_progress",
		{"message": f"Created {created} Leave Applications, skipped {skipped}"},
	)


def generate_attendance(employees, leave_period):
	leave_period_start = getdate(leave_period.from_date)
	leave_period_end = getdate(leave_period.to_date)
	current_date = getdate()

	created = 0

	for emp in employees:
		emp_doc = frappe.get_doc("Employee", emp.name)
		join_date = getdate(emp_doc.date_of_joining)

		if join_date > current_date:
			continue

		emp_start = max(join_date, leave_period_start)
		emp_end = min(current_date, leave_period_end)

		emp_approved_leaves = get_employee_leaves(emp.name, emp_start, emp_end, "Approved")
		holidays = get_employee_holidays(emp.name, emp_start, emp_end)

		current_day = emp_start
		days_since_start = 0
		consecutive_absences = 0

		while current_day <= emp_end:
			date_str = current_day.strftime("%Y-%m-%d")

			if date_str in holidays:
				status = "Holiday"
				consecutive_absences = 0
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
					created += 1
				except Exception:
					pass

			current_day = add_days(current_day, 1)
			days_since_start += 1

	frappe.publish_realtime(
		"demo_progress",
		{"message": f"Generated {created} Attendance records"},
	)


def get_employee_status(emp_doc):
	if emp_doc.employment_type == "Intern":
		return "intern"

	if emp_doc.final_confirmation_date:
		doj = getdate(emp_doc.date_of_joining)
		confirm = getdate(emp_doc.final_confirmation_date)
		months = (confirm.year - doj.year) * 12 + confirm.month - doj.month
		if months >= 6:
			return "confirmed"

	if emp_doc.scheduled_confirmation_date:
		return "probation"

	doj = getdate(emp_doc.date_of_joining)
	months = (getdate().year - doj.year) * 12 + getdate().month - doj.month
	if months >= 6:
		return "confirmed"

	return "new"


def calculate_months_in_period(join_date, period_start, period_end):
	if join_date > period_end:
		return 0
	if join_date < period_start:
		join_date = period_start

	months = (period_end.year - join_date.year) * 12 + period_end.month - join_date.month
	return max(0, months)


def prorate_leave(full_allocation, months):
	if months >= 12:
		return full_allocation
	return max(1, int((months / 12) * full_allocation))


def calculate_leaves_for_tenure(emp_start, emp_end, emp_status):
	tenure_days = (emp_end - emp_start).days
	tenure_months = tenure_days / 30

	if emp_status == "confirmed":
		num_leaves = min(15, int(tenure_months * 1.2))
	elif emp_status == "new":
		num_leaves = min(8, int(tenure_months * 1.0))
	elif emp_status == "probation":
		num_leaves = min(4, int(tenure_months * 0.8))
	else:
		num_leaves = min(2, int(tenure_months * 0.5))

	return max(2, num_leaves)


def generate_leaves_across_tenure(num_leaves, from_date, to_date, employee):
	dates = []
	date_range = (to_date - from_date).days

	if date_range < 7 or num_leaves <= 0:
		return dates

	gap = date_range // (num_leaves + 1) if num_leaves > 0 else date_range

	for i in range(1, num_leaves + 1):
		base_offset = i * gap
		variation = random.randint(-int(gap * 0.3), int(gap * 0.3))
		offset = max(0, min(date_range - 1, base_offset + variation))

		leave_start = add_days(from_date, offset)

		if leave_start > to_date:
			continue

		weekday = leave_start.weekday()
		if weekday >= 5:
			continue

		too_close = False
		for existing in dates:
			if abs((leave_start - existing).days) < 2:
				too_close = True
				break

		if not too_close:
			dates.append(leave_start)

	return dates


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
