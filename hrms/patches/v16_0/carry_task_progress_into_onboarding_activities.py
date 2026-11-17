import frappe

TASK_STATE = {"Completed": "completed", "Cancelled": "skipped"}


def execute():
	if not frappe.db.exists("DocType", "Task"):
		return

	onboardings = set()
	for row in frappe.get_all(
		"Employee Boarding Activity",
		filters={"parenttype": "Employee Onboarding", "task": ("is", "set")},
		fields=["name", "parent", "task", "user", "todo"],
	):
		values = {}
		if flag := TASK_STATE.get(frappe.db.get_value("Task", row.task, "status")):
			values[flag] = 1
		if row.user and not row.todo:
			if todo := frappe.db.get_value(
				"ToDo",
				{
					"reference_type": "Task",
					"reference_name": row.task,
					"allocated_to": row.user,
					"status": "Open",
				},
			):
				values["todo"] = todo
				frappe.db.set_value(
					"ToDo",
					todo,
					{"reference_type": "Employee Onboarding", "reference_name": row.parent},
					update_modified=False,
				)
		if values:
			frappe.db.set_value("Employee Boarding Activity", row.name, values, update_modified=False)
		onboardings.add(row.parent)

	for name in frappe.get_all(
		"Employee Onboarding", filters={"name": ("in", list(onboardings)), "docstatus": 1}, pluck="name"
	):
		onboarding = frappe.get_doc("Employee Onboarding", name)
		onboarding.set_boarding_status()
		onboarding.db_set("boarding_status", onboarding.boarding_status, update_modified=False)
