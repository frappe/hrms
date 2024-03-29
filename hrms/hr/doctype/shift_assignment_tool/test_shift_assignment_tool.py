# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.shift_assignment_tool.shift_assignment_tool import ShiftAssignmentTool
from hrms.hr.doctype.shift_request.test_shift_request import make_shift_request
from hrms.hr.doctype.shift_type.test_shift_type import make_shift_assignment, setup_shift_type
from hrms.tests.test_utils import create_company


class TestShiftAssignmentTool(FrappeTestCase):
	def setUp(self):
		create_company()
		create_company("_Test Company2")
		self.shift1 = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="12:00:00")
		self.shift2 = setup_shift_type(shift_type="Shift 2", start_time="11:00:00", end_time="15:00:00")
		self.shift3 = setup_shift_type(shift_type="Shift 3", start_time="14:00:00", end_time="18:00:00")
		self.emp1 = make_employee("employee1@test.com", company="_Test Company")
		self.emp2 = make_employee("employee2@test.com", company="_Test Company")
		self.emp3 = make_employee("employee3@test.com", company="_Test Company")
		self.emp4 = make_employee("employee4@test.com", company="_Test Company2")
		self.emp5 = make_employee("employee5@test.io", company="_Test Company")

	def tearDown(self):
		frappe.db.rollback()

	def test_get_employees_for_assigning_shifts(self):
		today = getdate()

		args = {
			"doctype": "Shift Assignment Tool",
			"action": "Assign Shift",
			"company": "_Test Company",  # excludes emp4
			"shift_type": self.shift1.name,
			"status": "Active",
			"start_date": today,
		}
		shift_assignment_tool = ShiftAssignmentTool(args)
		advanced_filters = [["employee_name", "like", "%test.com%"]]  # excludes emp5

		# does not exclude emp1 as dates don't overlap
		make_shift_assignment(self.shift3.name, self.emp1, add_days(today, -5), add_days(today, -1))
		# excludes emp2 due to overlapping dates
		make_shift_assignment(self.shift3.name, self.emp2, add_days(today, 6))
		# excludes emp3 due to overlapping dates
		make_shift_assignment(self.shift3.name, self.emp3, today)

		employees = shift_assignment_tool.get_employees(advanced_filters)
		self.assertEqual(len(employees), 1)  # emp1

		# includes emp2 as dates don't overlap anymore
		shift_assignment_tool.end_date = add_days(today, 5)
		employees = shift_assignment_tool.get_employees(advanced_filters)
		self.assertEqual(len(employees), 2)  # emp1, emp2

		# includes emp3 as multiple shifts in a day are allowed and timings don't overlap
		frappe.db.set_single_value("HR Settings", "allow_multiple_shift_assignments", 1)
		employees = shift_assignment_tool.get_employees(advanced_filters)
		self.assertEqual(len(employees), 3)  # emp1, emp2, emp3

		# excludes emp3 due to overlapping shift timings
		shift_assignment_tool.shift_type = self.shift2.name
		employees = shift_assignment_tool.get_employees(advanced_filters)
		self.assertEqual(len(employees), 2)  # emp1, emp2

		employee_names = [d.employee for d in employees]
		self.assertIn(self.emp1, employee_names)
		self.assertIn(self.emp2, employee_names)

	def test_get_shift_requests(self):
		today = getdate()

		for emp in [self.emp1, self.emp2, self.emp3, self.emp4, self.emp5]:
			employee = frappe.get_doc("Employee", emp)
			employee.shift_request_approver = "employee1@test.com"
			employee.save()

		request1 = make_shift_request(
			approver="employee1@test.com",
			employee=self.emp1,
			employee_name="employee1@test.com",
			from_date=today,
			to_date=add_days(today, 10),
			status="Draft",
			do_not_submit=1,
		)
		request2 = make_shift_request(
			approver="employee1@test.com",
			employee=self.emp2,
			employee_name="employee2@test.com",
			from_date=add_days(today, 6),
			to_date=add_days(today, 10),
			status="Draft",
			do_not_submit=1,
		)
		request3 = make_shift_request(
			approver="employee1@test.com",
			employee=self.emp2,
			employee_name="employee2@test.com",
			from_date=add_days(today, -5),
			to_date=add_days(today, -1),
			status="Draft",
			do_not_submit=1,
		)
		request4 = make_shift_request(
			approver="employee1@test.com",
			employee=self.emp4,
			employee_name="employee4@test.com",
			status="Approved",
		)

		request5 = make_shift_request(
			approver="employee1@test.com",
			employee=self.emp5,
			employee_name="employee5@test.com",
			status="Approved",
		)
		# request excluded as it is approved
		make_shift_request(
			approver="employee1@test.com",
			employee=self.emp3,
			employee_name="employee3@test.com",
			status="Approved",
		)

		args = {
			"doctype": "Shift Assignment Tool",
			"action": "Process Shift Requests",
			"company": "_Test Company",  # excludes request4
		}
		shift_assignment_tool = ShiftAssignmentTool(args)
		advanced_filters = [["employee_name", "like", "%test.com%"]]  # excludes request5

		shift_requests = shift_assignment_tool.get_employees(advanced_filters)
		self.assertEqual(len(shift_requests), 3)  # request1, request2, request3

		# excludes request3 as it ends before from_date
		shift_assignment_tool.from_date = today
		shift_requests = shift_assignment_tool.get_employees(advanced_filters)
		self.assertEqual(len(shift_requests), 2)  # request1, request2

		# excludes request2 as it starts after to_date
		shift_assignment_tool.to_date = add_days(today, 5)
		shift_requests = shift_assignment_tool.get_employees(advanced_filters)
		self.assertEqual(len(shift_requests), 1)  # request1
		self.assertEqual(shift_requests[0].name, request1.name)
