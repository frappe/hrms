# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
import dateutil.parser
from frappe.model.document import Document
import frappe
import json
import dateutil
import datetime
import calendar

from itertools import chain

class ProvisionalPlan(Document):
	pass


@frappe.whitelist()
def create_shifts(provisional_plan):
	# frappe.cancel_doc("Shift Assignment", {"provisional_plan": provisional_plan})
	frappe.db.sql(f"DELETE FROM `tabShift Assignment` WHERE provisional_plan = '{provisional_plan}'")

	doc = frappe.get_doc("Provisional Plan", provisional_plan)
	employees = doc.employees
	shifts = json.loads(doc.shifts)
	start_date = doc.start_date
	department = frappe.get_doc("Department", doc.department)
	company = department.company

	first_date_of_month = datetime.datetime(start_date.year, start_date.month, 1)
	start_date_index = int((start_date - datetime.timedelta(days=start_date.weekday())).strftime("%d"))
	flat_shifts = list(chain.from_iterable(shifts))
	num_days = calendar.monthrange(start_date.year, start_date.month)[1]

	result_shifts = []
	shift_types = frappe.get_all("Shift Type", filters=[
		["department", "in", [department.name, department.parent_department]],
	], fields=["name", "shift_suffix", "start_time", "end_time"])
	shift_map = {}
	for shift_type in shift_types:
		shift_map[shift_type.shift_suffix] = shift_type

	
	for ei, employee in enumerate(employees):
		emp = frappe.get_doc("Employee", employee.employee)
		emp_shifts = []

		# generate shifts for the month
		for i in range(num_days):
			shift_index = (i + 1 - (start_date_index - (ei * 7))) % len(flat_shifts)
			s = ""
			if shift_index >= 0:
				s = flat_shifts[shift_index]
			else:
				s = flat_shifts[len(flat_shifts) + shift_index]
				
			s_date = (first_date_of_month + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
			
			if s != "R":
				shift_assignment = frappe.new_doc("Shift Assignment")
				shift_assignment.employee = emp.employee
				shift_assignment.start_date = s_date
				shift_assignment.end_date = s_date
				shift_assignment.shift_type = shift_map[s].name
				shift_assignment.department = department.name
				shift_assignment.company = company
				# shift_assignment.docstatus = 1
				shift_assignment.status = "Active"
				shift_assignment.provisional_plan = doc.name
				shift_assignment.submit()



	

	frappe.db.commit()
	# frappe.db.bulk_insert("Shift Assignment",
	# 				    fields=["name","employee","start_date","shift_type","department","company","docstatus","status", "provisional_plan"],
	# 					  values=result_shifts)
	# for s in result_shifts:
	# 	print(s)

	# frappe.db.set_value('Provisional Plan', provisional_plan, 'real_shift_assigned', 1)






	return result_shifts
