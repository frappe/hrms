# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _, msgprint
from frappe.model.document import Document
from frappe.utils import cint, comma_and, flt


class LeaveControlPanel(Document):
	def validate_fields(self):
		fields = []
		if self.dates_based_on == "Leave Period":
			fields.append("leave_period")
		else:
			fields.extend(["from_date", "to_date"])
			self.validate_from_to_dates("from_date", "to_date")
		if self.allocation_based_on == "Leave Policy Assignment":
			fields.append("leave_policy")
		else:
			fields.extend(["leave_type", "no_of_days"])
		for f in fields:
			if not self.get(f):
				frappe.throw(_("{0} is required").format(self.meta.get_label(f)))

	@frappe.whitelist()
	def allocate_leave(self, employees):
		self.validate_fields()
		if not employees:
			frappe.throw(_("No employee selected"))
		leave_allocated_for = []
		from_date, to_date = self.get_from_to_date()
		for d in employees:
			try:
				la = frappe.new_doc("Leave Allocation")
				la.set("__islocal", 1)
				la.employee = d
				la.employee_name = frappe.get_value("Employee", d, "employee_name")
				la.leave_type = self.leave_type
				la.from_date = from_date
				la.to_date = to_date
				la.carry_forward = cint(self.carry_forward)
				la.new_leaves_allocated = flt(self.no_of_days)
				la.docstatus = 1
				la.save()
				leave_allocated_for.append(d)
			except Exception:
				pass
		if leave_allocated_for:
			msgprint(_("Leaves Allocated Successfully for {0}").format(comma_and(leave_allocated_for)))

	def get_from_to_date(self):
		if self.dates_based_on == "Leave Period":
			return frappe.get_value("Leave Period", self.leave_period, ['from_date', 'to_date'])
		else:
			return self.from_date, self.to_date

@frappe.whitelist()
def get_employees(
	company: str = None,
	employment_type: str = None,
	branch: str = None,
	department: str = None,
	designation: str = None,
	grade: str = None,
) -> list:
	args = locals().copy()
	filters = {"status": "Active"}
	for d in args:
		if args[d]:
			filters[d] = args[d]
	employees = frappe.get_list(
		"Employee",
		filters=filters,
		fields=["employee", "employee_name", "company", "department"],
	)
	return employees
