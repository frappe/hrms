# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
<<<<<<< HEAD
from frappe import _, msgprint
from frappe.model.document import Document
from frappe.utils import cint, comma_and, cstr, flt


class LeaveControlPanel(Document):
	def get_employees(self):
		conditions, values = [], []
		for field in [
			"company",
			"employment_type",
			"branch",
			"designation",
			"department",
			"employee",
			"employee_grade",
		]:
			if self.get(field):
				if field == "employee":
					conditions.append("name=%s")
				elif field == "employee_grade":
					conditions.append("grade=%s")
				else:
					conditions.append(f"{field}=%s")

				values.append(self.get(field))

		condition_str = " and " + " and ".join(conditions) if len(conditions) else ""

		# nosemgrep: frappe-semgrep-rules.rules.frappe-using-db-sql
		e = frappe.db.sql(
			f"select name from tabEmployee where status='Active' {condition_str}",
			tuple(values),
		)

		return e

	def validate_values(self):
		for f in ["from_date", "to_date", "leave_type", "no_of_days"]:
			if not self.get(f):
				frappe.throw(_("{0} is required").format(self.meta.get_label(f)))
		self.validate_from_to_dates("from_date", "to_date")

	@frappe.whitelist()
	def allocate_leave(self):
		self.validate_values()
		leave_allocated_for = []
		employees = self.get_employees()
		if not employees:
			frappe.throw(_("No employee found"))

		for d in self.get_employees():
			try:
				la = frappe.new_doc("Leave Allocation")
				la.set("__islocal", 1)
				la.employee = cstr(d[0])
				la.employee_name = frappe.db.get_value("Employee", cstr(d[0]), "employee_name")
				la.leave_type = self.leave_type
				la.from_date = self.from_date
				la.to_date = self.to_date
				la.carry_forward = cint(self.carry_forward)
				la.new_leaves_allocated = flt(self.no_of_days)
				la.docstatus = 1
				la.save()
				leave_allocated_for.append(d[0])
			except Exception:
				pass
		if leave_allocated_for:
			msgprint(_("Leaves Allocated Successfully for {0}").format(comma_and(leave_allocated_for)))
=======
from frappe.model.document import Document
from frappe.utils import cint, flt, get_link_to_form

from erpnext import get_default_company

from hrms.hr.utils import validate_bulk_tool_fields


class LeaveControlPanel(Document):
	def validate_fields(self, employees: list):
		mandatory_fields = []
		if self.dates_based_on == "Leave Period":
			mandatory_fields.append("leave_period")
		elif self.dates_based_on == "Joining Date":
			mandatory_fields.append("to_date")
		else:
			mandatory_fields.extend(["from_date", "to_date"])

		if self.allocate_based_on_leave_policy:
			mandatory_fields.append("leave_policy")
		else:
			mandatory_fields.extend(["leave_type", "no_of_days"])
		validate_bulk_tool_fields(self, mandatory_fields, employees, "from_date", "to_date")

	@frappe.whitelist()
	def allocate_leave(self, employees: list):
		self.validate_fields(employees)
		if self.allocate_based_on_leave_policy:
			return self.create_leave_policy_assignments(employees)
		return self.create_leave_allocations(employees)

	def create_leave_allocations(self, employees: list) -> dict:
		from_date, to_date = self.get_from_to_date()
		failure = []
		success = []
		savepoint = "before_allocation_submission"

		for employee in employees:
			try:
				frappe.db.savepoint(savepoint)
				allocation = frappe.new_doc("Leave Allocation")
				allocation.employee = employee
				allocation.leave_type = self.leave_type
				allocation.from_date = from_date or frappe.db.get_value(
					"Employee", employee, "date_of_joining"
				)
				allocation.to_date = to_date
				allocation.carry_forward = cint(self.carry_forward)
				allocation.new_leaves_allocated = flt(self.no_of_days)
				allocation.insert()
				allocation.submit()
				success.append(
					{"doc": get_link_to_form("Leave Allocation", allocation.name), "employee": employee}
				)
			except Exception:
				frappe.db.rollback(save_point=savepoint)
				allocation.log_error(f"Leave Allocation failed for employee {employee}")
				failure.append(employee)

		frappe.clear_messages()
		frappe.publish_realtime(
			"completed_bulk_leave_allocation",
			message={"success": success, "failure": failure},
			doctype="Bulk Salary Structure Assignment",
			after_commit=True,
		)

	def create_leave_policy_assignments(self, employees: list) -> dict:
		from_date, to_date = self.get_from_to_date()
		assignment_based_on = None if self.dates_based_on == "Custom Range" else self.dates_based_on
		failure = []
		success = []
		savepoint = "before_assignment_submission"

		for employee in employees:
			try:
				frappe.db.savepoint(savepoint)
				assignment = frappe.new_doc("Leave Policy Assignment")
				assignment.employee = employee
				assignment.assignment_based_on = assignment_based_on
				assignment.leave_policy = self.leave_policy
				assignment.effective_from = from_date or frappe.db.get_value(
					"Employee", employee, "date_of_joining"
				)
				assignment.effective_to = to_date
				assignment.leave_period = self.get("leave_period")
				assignment.carry_forward = self.carry_forward
				assignment.save()
				assignment.submit()
				success.append(
					{
						"doc": get_link_to_form("Leave Policy Assignment", assignment.name),
						"employee": employee,
					}
				)
			except Exception:
				frappe.db.rollback(save_point=savepoint)
				assignment.log_error(f"Leave Policy Assignment failed for employee {employee}")
				failure.append(employee)

		frappe.clear_messages()
		frappe.publish_realtime(
			"completed_bulk_leave_policy_assignment",
			message={"success": success, "failure": failure},
			doctype="Bulk Salary Structure Assignment",
			after_commit=True,
		)

	def get_from_to_date(self):
		if self.dates_based_on == "Joining Date":
			return None, self.to_date
		elif self.dates_based_on == "Leave Period" and self.leave_period:
			return frappe.db.get_value("Leave Period", self.leave_period, ["from_date", "to_date"])
		else:
			return self.from_date, self.to_date

	@frappe.whitelist()
	def get_employees(self, advanced_filters: list) -> list:
		from_date, to_date = self.get_from_to_date()

		if to_date and (from_date or self.dates_based_on == "Joining Date"):
			if all_employees := frappe.get_list(
				"Employee",
				filters=self.get_filters() + advanced_filters,
				fields=["name", "employee", "employee_name", "company", "department", "date_of_joining"],
			):
				return self.get_employees_without_allocations(all_employees, from_date, to_date)

		return []

	def get_employees_without_allocations(self, all_employees: list, from_date: str, to_date: str) -> list:
		Allocation = frappe.qb.DocType("Leave Allocation")
		Employee = frappe.qb.DocType("Employee")

		query = (
			frappe.qb.from_(Allocation)
			.join(Employee)
			.on(Allocation.employee == Employee.name)
			.select(Employee.name)
			.distinct()
			.where((Allocation.docstatus == 1) & (Allocation.employee.isin([d.name for d in all_employees])))
		)

		if self.dates_based_on == "Joining Date":
			from_date = Employee.date_of_joining

		query = query.where(
			(Allocation.from_date[from_date:to_date] | Allocation.to_date[from_date:to_date])
			| (
				(Allocation.from_date <= from_date)
				& (Allocation.from_date <= to_date)
				& (Allocation.to_date >= from_date)
				& (Allocation.to_date >= to_date)
			)
		)

		if self.allocate_based_on_leave_policy and self.leave_policy:
			leave_types = frappe.get_all(
				"Leave Policy Detail", {"parent": self.leave_policy}, pluck="leave_type"
			)
			query = query.where(Allocation.leave_type.isin(leave_types))

		elif not self.allocate_based_on_leave_policy and self.leave_type:
			query = query.where(Allocation.leave_type == self.leave_type)

		employees_with_allocations = query.run(pluck=True)
		return [d for d in all_employees if d.name not in employees_with_allocations]

	@frappe.whitelist()
	def get_latest_leave_period(self):
		return frappe.db.get_value(
			"Leave Period",
			{
				"is_active": 1,
				"company": self.company or get_default_company(),
			},
			"name",
			order_by="from_date desc",
		)

	def get_filters(self):
		filter_fields = [
			"company",
			"employment_type",
			"branch",
			"department",
			"designation",
			"employee_grade",
		]
		filters = [["status", "=", "Active"]]

		for d in filter_fields:
			if self.get(d):
				if d == "employee_grade":
					filters.append(["grade", "=", self.get(d)])
				else:
					filters.append([d, "=", self.get(d)])
		return filters
>>>>>>> da17577dc (chore: remove unused import)
