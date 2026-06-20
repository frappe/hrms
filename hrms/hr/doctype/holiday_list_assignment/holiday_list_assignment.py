# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder.terms import SubQuery
from frappe.utils import format_date, get_link_to_form, getdate

from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import DuplicateAssignment


def parse_filters(filters: dict | str) -> frappe._dict:
	if isinstance(filters, str):
		filters = json.loads(filters)
	return frappe._dict(filters)


class HolidayListAssignment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		applicable_for: DF.Literal["Employee", "Company"]
		assigned_to: DF.DynamicLink
		employee_company: DF.Link | None
		employee_name: DF.Data | None
		from_date: DF.Date
		holiday_list: DF.Link
		naming_series: DF.Literal["HR-HLA-.YYYY.-"]
	# end: auto-generated types

	@property
	def holiday_list_start(self):
		return frappe.get_value("Holiday List", self.holiday_list, "from_date") if self.holiday_list else None

	@property
	def holiday_list_end(self):
		return frappe.get_value("Holiday List", self.holiday_list, "to_date") if self.holiday_list else None

	def validate(self):
		self.validate_assignment_start_date()
		self.validate_existing_assignment()

	def validate_existing_assignment(self):
		holiday_list = frappe.db.exists(
			"Holiday List Assignment",
			{"assigned_to": self.assigned_to, "from_date": self.from_date, "docstatus": 1},
		)

		if holiday_list:
			frappe.throw(
				_("Holiday List Assignment for {0} already exists for date {1}: {2}").format(
					self.assigned_to,
					format_date(self.from_date),
					get_link_to_form("Holiday List Assignment", holiday_list),
				),
				DuplicateAssignment,
				title=_("Duplicate Assignment"),
			)

	def validate_assignment_start_date(self):
		holiday_list_start, holiday_list_end = frappe.db.get_value(
			"Holiday List", self.holiday_list, ["from_date", "to_date"]
		)
		assignment_start_date = getdate(self.from_date)
		if (assignment_start_date < holiday_list_start) or (assignment_start_date > holiday_list_end):
			frappe.throw(_("Assignment start date cannot be outside holiday list dates"))


@frappe.whitelist()
def get_employees_for_bulk_assignment(filters: dict | str) -> list:
	filters = parse_filters(filters)
	quick_filter_fields = [
		"company",
		"employment_type",
		"branch",
		"department",
		"designation",
		"grade",
	]
	employee_filters = [[d, "=", filters.get(d)] for d in quick_filter_fields if filters.get(d)]

	HolidayListAssignment = frappe.qb.DocType("Holiday List Assignment")
	employees_with_assignments = SubQuery(
		frappe.qb.from_(HolidayListAssignment)
		.select(HolidayListAssignment.assigned_to)
		.distinct()
		.where(
			(HolidayListAssignment.applicable_for == "Employee")
			& (HolidayListAssignment.holiday_list == filters.holiday_list)
			& (HolidayListAssignment.docstatus == 1)
		)
	)

	Employee = frappe.qb.DocType("Employee")
	query = frappe.qb.get_query(
		Employee,
		fields=[Employee.employee, Employee.employee_name, Employee.department, Employee.branch],
		filters=employee_filters,
	).where((Employee.status == "Active") & (Employee.employee.notin(employees_with_assignments)))
	return query.run(as_dict=True)


@frappe.whitelist()
def bulk_assign_holiday_list(filters: dict | str, employees: list | str) -> None:
	filters = parse_filters(filters)
	if isinstance(employees, str):
		employees = json.loads(employees)

	mandatory_fields = {
		"holiday_list": _("Holiday List"),
		"from_date": _("Assignment Starts From"),
		"company": _("Company"),
	}
	for fieldname, label in mandatory_fields.items():
		if not filters.get(fieldname):
			frappe.throw(_("{0} is required").format(label), title=_("Missing Field"))

	if not employees:
		frappe.throw(
			_("Please select at least one employee to perform this action."),
			title=_("No Employees Selected"),
		)

	if len(employees) <= 30:
		return _bulk_assign_holiday_list(filters, employees)

	frappe.enqueue(_bulk_assign_holiday_list, timeout=3000, filters=filters, employees=employees)
	frappe.msgprint(
		_("Creation of Holiday List Assignments has been queued. It may take a few minutes."),
		alert=True,
		indicator="blue",
	)


def _bulk_assign_holiday_list(filters: dict, employees: list) -> None:
	filters = frappe._dict(filters)
	success, failure = [], []
	count = 0
	savepoint = "before_holiday_assignment"

	for d in employees:
		try:
			frappe.db.savepoint(savepoint)
			assignment = frappe.new_doc("Holiday List Assignment")
			assignment.applicable_for = "Employee"
			assignment.assigned_to = d["employee"]
			assignment.holiday_list = filters.holiday_list
			assignment.from_date = filters.from_date
			assignment.save()
			assignment.submit()
		except Exception:
			frappe.db.rollback(save_point=savepoint)
			frappe.log_error(
				f"Bulk Assignment - Holiday List Assignment failed for employee {d['employee']}.",
				reference_doctype="Holiday List Assignment",
			)
			failure.append(d["employee"])
		else:
			success.append(
				{
					"doc": get_link_to_form("Holiday List Assignment", assignment.name),
					"employee": d["employee"],
				}
			)

		count += 1
		frappe.publish_progress(count * 100 / len(employees), title=_("Assigning Holiday List..."))

	frappe.publish_realtime(
		"completed_bulk_holiday_list_assignment",
		message={"success": success, "failure": failure},
		doctype="Holiday List Assignment",
		after_commit=True,
	)
