# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _, msgprint
from frappe.model.document import Document
from frappe.utils import cint, comma_and, flt

from erpnext import get_default_company


class LeaveControlPanel(Document):
	def validate_fields(self, employees):
		fields = []
		if self.dates_based_on == "Leave Period":
			fields.append("leave_period")
		elif self.dates_based_on == "Joining Date":
			fields.append("to_date")
		else:
			self.validate_from_to_dates("from_date", "to_date")
			fields.extend(["from_date", "to_date"])

		if self.allocate_based_on_leave_policy:
			fields.append("leave_policy")
		else:
			fields.extend(["leave_type", "no_of_days"])

		for f in fields:
			if not self.get(f):
				frappe.throw(_("{0} is required").format(self.meta.get_label(f)))
		if not employees:
			frappe.throw(_("No employee(s) selected"))

	@frappe.whitelist()
	def allocate_leave(self, employees):
		self.validate_fields(employees)
		if self.allocate_based_on_leave_policy:
			self.create_leave_policy_assignments(employees)
		else:
			self.create_leave_allocations(employees)

	def create_leave_allocations(self, employees):
		leave_allocated_for = []
		from_date, to_date = self.get_from_to_date()

		for employee in employees:
			try:
				allocation = frappe.new_doc("Leave Allocation")
				allocation.employee = employee
				allocation.leave_type = self.leave_type
				allocation.from_date = from_date or frappe.db.get_value(
					"Employee", employee, "date_of_joining"
				)
				allocation.to_date = to_date
				allocation.carry_forward = cint(self.carry_forward)
				allocation.new_leaves_allocated = flt(self.no_of_days)
				allocation.submit()
				leave_allocated_for.append(employee)
			except Exception:
				pass

		if leave_allocated_for:
			msgprint(_("Leaves Allocated Successfully for {0}").format(comma_and(leave_allocated_for)))

	def create_leave_policy_assignments(self, employees):
		from hrms.hr.doctype.leave_policy_assignment.leave_policy_assignment import (
			show_assignment_submission_status,
		)

		failed = []
		from_date, to_date = self.get_from_to_date()
		assignment_based_on = None if self.dates_based_on == "Custom Range" else self.dates_based_on

		for d in employees:
			assignment = frappe.new_doc("Leave Policy Assignment")
			assignment.employee = d
			assignment.assignment_based_on = assignment_based_on
			assignment.leave_policy = self.leave_policy
			assignment.effective_from = (
				from_date if from_date else frappe.db.get_value("Employee", d, "date_of_joining")
			)
			assignment.effective_to = to_date
			assignment.leave_period = self.leave_period or None
			assignment.carry_forward = self.carry_forward
			assignment.save()

			savepoint = "before_assignment_submission"
			try:
				frappe.db.savepoint(savepoint)
				assignment.submit()
			except Exception:
				frappe.db.rollback(save_point=savepoint)
				assignment.log_error("Leave Policy Assignment submission failed")
				failed.append(assignment.name)
		if failed:
			show_assignment_submission_status(failed)

	def get_from_to_date(self):
		if self.dates_based_on == "Joining Date":
			return None, self.to_date
		else:
			return self.from_date, self.to_date

	@frappe.whitelist()
	def get_employees(self):
		from_date, to_date = self.get_from_to_date()
		if to_date and (from_date or self.dates_based_on == "Joining Date"):
			la = frappe.qb.DocType("Leave Allocation")
			all_employees = frappe.get_list(
				"Employee",
				filters=self.get_filters(),
				fields=["employee", "employee_name", "company", "department", "date_of_joining"],
			)
			filtered_employees = []

			if self.allocate_based_on_leave_policy and self.leave_policy:
				leave_types = frappe.get_list(
					"Leave Policy Detail", {"parent": self.leave_policy}, pluck="leave_type"
				)
				for d in all_employees:
					query = self.get_query(from_date, to_date, d)
					query = query.where(la.leave_type.isin(leave_types))
					if not query.run():
						filtered_employees.append(d)
				return filtered_employees

			elif not self.allocate_based_on_leave_policy and self.leave_type:
				for d in all_employees:
					query = self.get_query(from_date, to_date, d)
					query = query.where(la.leave_type == self.leave_type)
					if not query.run():
						filtered_employees.append(d)
				return filtered_employees

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
		filters = {"status": "Active"}

		for d in filter_fields:
			if self.get(d):
				if d == "employee_grade":
					filters["grade"] = self.get(d)
				else:
					filters[d] = self.get(d)
		return filters

	def get_query(self, from_date, to_date, employee):
		if self.dates_based_on == "Joining Date":
			from_date = employee.date_of_joining

		Allocation = frappe.qb.DocType("Leave Allocation")
		return (
			frappe.qb.from_(Allocation)
			.select(True)
			.where(
				(Allocation.docstatus == 1)
				& (Allocation.employee == employee.employee)
				& (
					(Allocation.from_date[from_date:to_date] | Allocation.to_date[from_date:to_date])
					| (
						(Allocation.from_date <= from_date)
						& (Allocation.from_date <= to_date)
						& (Allocation.to_date >= from_date)
						& (Allocation.to_date >= to_date)
					)
				)
			)
		)
