from pypika.terms import ValueWrapper

import frappe

from hrms.patches.v16_0.create_holiday_list_assignments import create_holiday_list_assignment


def execute():
	employee = frappe.qb.DocType("Employee")
	holiday_list = frappe.qb.DocType("Holiday List")
	assignment = frappe.qb.DocType("Holiday List Assignment")

	employees_with_assignment = (
		frappe.qb.from_(assignment)
		.select(assignment.assigned_to)
		.where(assignment.applicable_for == "Employee")
	)

	employee_holiday_details = (
		frappe.qb.from_(employee)
		.inner_join(holiday_list)
		.on(employee.holiday_list == holiday_list.name)
		.select(
			(employee.name).as_("assigned_to"),
			employee.holiday_list,
			holiday_list.from_date,
			ValueWrapper("Employee", "applicable_for"),
		)
		.where(employee.status != "Active")
		.where(employee.name.notin(employees_with_assignment))
	).run(as_dict=True)

	for entity in employee_holiday_details:
		try:
			create_holiday_list_assignment(entity)
		except Exception as e:
			frappe.log_error(e)
