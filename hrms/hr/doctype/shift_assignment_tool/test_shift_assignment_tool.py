# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.shift_assignment_tool.shift_assignment_tool import ShiftAssignmentTool
from hrms.hr.doctype.shift_request.test_shift_request import make_shift_request
from hrms.hr.doctype.shift_schedule.shift_schedule import get_or_insert_shift_schedule
from hrms.hr.doctype.shift_type.test_shift_type import make_shift_assignment, setup_shift_type
from hrms.tests.test_utils import create_company
from hrms.tests.utils import HRMSTestSuite


class TestShiftAssignmentTool(HRMSTestSuite):
	def setUp(self):
		create_company()
		create_company("_Test Company2")
		self.shift1 = setup_shift_type(shift_type="Shift 1", start_time="08:00:00", end_time="12:00:00")
		self.shift2 = setup_shift_type(shift_type="Shift 2", start_time="11:00:00", end_time="15:00:00")
		self.shift3 = setup_shift_type(shift_type="Shift 3", start_time="14:00:00", end_time="18:00:00")
		self.schedule1 = get_or_insert_shift_schedule(self.shift1.name, "Every Week", ["Monday"])
		self.schedule2 = get_or_insert_shift_schedule(self.shift2.name, "Every Week", ["Monday"])
		self.schedule3 = get_or_insert_shift_schedule(self.shift3.name, "Every Week", ["Monday"])
		self.schedule4 = get_or_insert_shift_schedule(self.shift1.name, "Every Week", ["Tuesday"])
		self.emp1 = make_employee("employee1@test.com", company="_Test Company")
		self.emp2 = make_employee("employee2@test.com", company="_Test Company")
		self.emp3 = make_employee("employee3@test.com", company="_Test Company")
		self.emp4 = make_employee("employee4@test.com", company="_Test Company2")
		self.emp5 = make_employee("employee5@test.io", company="_Test Company")

	@HRMSTestSuite.change_settings("HR Settings", {"allow_multiple_shift_assignments": 0})
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

	@HRMSTestSuite.change_settings("HR Settings", {"allow_multiple_shift_assignments": 0})
	def test_get_employees_for_assigning_shift_schedule(self):
		today = getdate()

		args = {
			"doctype": "Shift Assignment Tool",
			"action": "Assign Shift Schedule",
			"company": "_Test Company",  # excludes emp4
			"shift_schedule": self.schedule1,
			"start_date": today,
		}
		shift_assignment_tool = ShiftAssignmentTool(args)
		advanced_filters = [["employee_name", "like", "%test.com%"]]  # excludes emp5

		# does not exclude emp1 as days don't overlap
		make_shift_schedule_assignment(self.schedule4, self.emp1).create_shifts(today)
		# excludes emp2 due to overlapping days
		make_shift_schedule_assignment(self.schedule2, self.emp2).create_shifts(today)
		# excludes emp3 due to overlapping days
		make_shift_schedule_assignment(self.schedule3, self.emp3).create_shifts(today)

		employees = shift_assignment_tool.get_employees(advanced_filters)
		self.assertEqual(len(employees), 1)  # emp1

		# includes emp3 as multiple shifts in a day are allowed and timings don't overlap
		frappe.db.set_single_value("HR Settings", "allow_multiple_shift_assignments", 1)
		employees = shift_assignment_tool.get_employees(advanced_filters)
		self.assertEqual(len(employees), 2)  # emp1, emp3

		employee_names = [d.employee for d in employees]
		self.assertIn(self.emp1, employee_names)
		self.assertIn(self.emp3, employee_names)

	@HRMSTestSuite.change_settings("HR Settings", {"allow_multiple_shift_assignments": 0})
	def test_complementary_rotation_schedules(self):
		days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
		schedule_a = get_or_insert_shift_schedule(self.shift1.name, "Every 3 Weeks", days)
		schedule_b = get_or_insert_shift_schedule(self.shift2.name, "Every 3 Weeks", days)
		make_shift_schedule_assignment(schedule_a, self.emp1).create_shifts("2026-09-21")
		make_shift_schedule_assignment(schedule_a, self.emp2).create_shifts("2026-09-28")

		tool = ShiftAssignmentTool(
			{
				"doctype": "Shift Assignment Tool",
				"action": "Assign Shift Schedule",
				"company": "_Test Company",
				"shift_schedule": schedule_b,
				"start_date": "2026-09-28",
				"status": "Active",
			}
		)
		for allow_multiple in (0, 1):
			with self.subTest(allow_multiple=allow_multiple):
				frappe.db.set_single_value("HR Settings", "allow_multiple_shift_assignments", allow_multiple)
				employees = {d.employee for d in tool.get_employees()}
				self.assertIn(self.emp1, employees)
				self.assertNotIn(self.emp2, employees)

		# The complementary schedule must also pass the actual assignment validations.
		assignment = tool.create_shift_schedule_assignment(self.emp1)
		assignment.create_shifts(tool.start_date)
		shifts = frappe.get_all(
			"Shift Assignment",
			filters={"shift_schedule_assignment": assignment.name, "docstatus": 1},
			fields=["start_date", "end_date"],
			order_by="start_date",
		)
		self.assertEqual(
			[(str(d.start_date), str(d.end_date)) for d in shifts],
			[
				("2026-09-28", "2026-10-04"),
				("2026-10-19", "2026-10-25"),
				("2026-11-09", "2026-11-15"),
				("2026-11-30", "2026-12-06"),
				("2026-12-21", "2026-12-27"),
			],
		)

	@HRMSTestSuite.change_settings("HR Settings", {"allow_multiple_shift_assignments": 0})
	def test_schedule_conflicts_with_actual_shifts(self):
		tool = ShiftAssignmentTool(
			{
				"doctype": "Shift Assignment Tool",
				"action": "Assign Shift Schedule",
				"company": "_Test Company",
				"shift_schedule": self.schedule1,  # Mondays
				"start_date": "2026-09-21",
				"end_date": "2026-09-28",
			}
		)
		# An assignment from a finite (disabled) schedule still blocks overlapping dates.
		assignment = make_shift_schedule_assignment(self.schedule2, self.emp1, enabled=0)
		assignment.create_shifts("2026-09-21", "2026-09-21")
		# Standalone, open-ended shifts also need to be considered.
		make_shift_assignment(self.shift2.name, self.emp2, "2026-09-28")
		# A shift in between the requested Mondays is not a conflict.
		make_shift_assignment(self.shift2.name, self.emp3, "2026-09-22", "2026-09-22")

		employees = {d.employee for d in tool.get_employees()}
		self.assertNotIn(self.emp1, employees)
		self.assertNotIn(self.emp2, employees)
		self.assertIn(self.emp3, employees)

		# Restricting the end date excludes the later conflict.
		tool.end_date = "2026-09-21"
		employees = {d.employee for d in tool.get_employees()}
		self.assertNotIn(self.emp1, employees)
		self.assertIn(self.emp2, employees)

		# Cancelled shifts must not block the schedule.
		shift = frappe.get_doc("Shift Assignment", {"shift_schedule_assignment": assignment.name})
		shift.cancel()
		self.assertIn(self.emp1, {d.employee for d in tool.get_employees()})

		# A range containing no scheduled weekdays must not exclude any of these employees.
		tool.start_date = tool.end_date = "2026-09-29"
		employees = {d.employee for d in tool.get_employees()}
		self.assertTrue({self.emp1, self.emp2, self.emp3}.issubset(employees))

	@HRMSTestSuite.change_settings("HR Settings", {"allow_multiple_shift_assignments": 1})
	def test_touching_shift_timings_do_not_conflict(self):
		shift4 = setup_shift_type(shift_type="Shift 4", start_time="12:00:00", end_time="16:00:00")
		schedule = get_or_insert_shift_schedule(shift4.name, "Every Week", ["Monday"])
		# shift1 (08:00-12:00) ends when shift4 starts
		make_shift_assignment(self.shift1.name, self.emp1, "2026-09-21", "2026-09-21")
		# shift2 (11:00-15:00) overlaps shift4
		make_shift_assignment(self.shift2.name, self.emp2, "2026-09-21", "2026-09-21")

		for action, field, value in (
			("Assign Shift", "shift_type", shift4.name),
			("Assign Shift Schedule", "shift_schedule", schedule),
		):
			with self.subTest(action=action):
				tool = ShiftAssignmentTool(
					{
						"doctype": "Shift Assignment Tool",
						"action": action,
						"company": "_Test Company",
						field: value,
						"start_date": "2026-09-21",
						"end_date": "2026-09-21",
						"status": "Active",
					}
				)
				employees = {d.employee for d in tool.get_employees()}
				self.assertIn(self.emp1, employees)
				self.assertNotIn(self.emp2, employees)

	def test_get_shift_requests(self):
		today = getdate()
		setup_shift_type(shift_type="Day Shift")

		for emp in [self.emp1, self.emp2, self.emp3, self.emp4, self.emp5]:
			employee = frappe.get_doc("Employee", emp)
			employee.shift_request_approver = "employee1@test.com"
			employee.save()

		request1 = make_shift_request(
			employee=self.emp1,
			employee_name="employee1@test.com",
			from_date=today,
			to_date=add_days(today, 10),
			status="Draft",
			do_not_submit=1,
		)
		# request2
		make_shift_request(
			employee=self.emp2,
			employee_name="employee2@test.com",
			from_date=add_days(today, 6),
			to_date=add_days(today, 10),
			status="Draft",
			do_not_submit=1,
		)
		# request3
		make_shift_request(
			employee=self.emp2,
			employee_name="employee2@test.com",
			from_date=add_days(today, -5),
			to_date=add_days(today, -1),
			status="Draft",
			do_not_submit=1,
		)
		# request4
		make_shift_request(
			employee=self.emp4,
			employee_name="employee4@test.com",
			status="Approved",
		)
		# request5
		make_shift_request(
			employee=self.emp5,
			employee_name="employee5@test.com",
			status="Approved",
		)
		# request excluded as it is approved
		make_shift_request(
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

	def test_bulk_assign_shift(self):
		today = getdate()

		args = {
			"doctype": "Shift Assignment Tool",
			"action": "Assign Shift",
			"company": "_Test Company",
			"shift_type": self.shift1.name,
			"status": "Active",
			"start_date": today,
			"end_date": add_days(today, 10),
		}
		shift_assignment_tool = ShiftAssignmentTool(args)

		employees = [self.emp1, self.emp2, self.emp3]
		shift_assignment_tool.bulk_assign(employees)
		shift_assignment_employees = frappe.get_list(
			"Shift Assignment",
			filters={
				"shift_type": self.shift1.name,
				"status": "Active",
				"start_date": today,
				"end_date": add_days(today, 10),
				"docstatus": 1,
			},
			pluck="employee",
		)
		self.assertIn(self.emp1, shift_assignment_employees)
		self.assertIn(self.emp2, shift_assignment_employees)
		self.assertIn(self.emp3, shift_assignment_employees)

	def test_bulk_assign_shift_schedule(self):
		today = getdate()

		args = {
			"doctype": "Shift Assignment Tool",
			"action": "Assign Shift Schedule",
			"company": "_Test Company",
			"shift_schedule": self.schedule1,
			"status": "Active",
			"start_date": today,
			"end_date": add_days(today, 10),
		}
		shift_assignment_tool = ShiftAssignmentTool(args)

		employees = [self.emp1, self.emp2, self.emp3]
		shift_assignment_tool._bulk_assign(employees)
		assigned_employees = frappe.get_list(
			"Shift Schedule Assignment",
			filters={
				"shift_schedule": self.schedule1,
				"shift_status": "Active",
				"enabled": 0,
			},
			pluck="employee",
		)
		self.assertIn(self.emp1, assigned_employees)
		self.assertIn(self.emp2, assigned_employees)
		self.assertIn(self.emp3, assigned_employees)

	def test_bulk_process_shift_requests(self):
		for emp in [self.emp1, self.emp2, self.emp3]:
			employee = frappe.get_doc("Employee", emp)
			employee.shift_request_approver = "employee1@test.com"
			employee.save()

		setup_shift_type(shift_type="Day Shift")
		request1 = make_shift_request(
			employee=self.emp1,
			employee_name="employee1@test.com",
			status="Draft",
			do_not_submit=1,
		)
		request2 = make_shift_request(
			employee=self.emp2,
			employee_name="employee2@test.com",
			status="Draft",
			do_not_submit=1,
		)
		request3 = make_shift_request(
			employee=self.emp3,
			employee_name="employee3@test.com",
			status="Draft",
			do_not_submit=1,
		)

		args = {
			"doctype": "Shift Assignment Tool",
			"action": "Process Shift Requests",
			"company": "_Test Company",
		}
		shift_assignment_tool = ShiftAssignmentTool(args)

		requests = [
			{"employee": self.emp1, "shift_request": request1.name},
			{"employee": self.emp2, "shift_request": request2.name},
		]
		shift_assignment_tool.bulk_process_shift_requests(requests, "Rejected")
		processed_shift_requests = frappe.get_list(
			"Shift Request",
			filters={"status": "Rejected", "docstatus": 1},
			pluck="name",
		)
		self.assertIn(request1.name, processed_shift_requests)
		self.assertIn(request2.name, processed_shift_requests)

		requests = [{"employee": self.emp3, "shift_request": request3.name}]
		shift_assignment_tool.bulk_process_shift_requests(requests, "Approved")
		status, docstatus = frappe.db.get_value("Shift Request", request3.name, ["status", "docstatus"])
		self.assertEqual(status, "Approved")
		self.assertEqual(docstatus, 1)

		shift_assignment = frappe.db.exists("Shift Assignment", {"shift_request": request3.name})
		self.assertTrue(shift_assignment)


def make_shift_schedule_assignment(schedule, employee, create_shifts_after=None, enabled=1):
	assignment = frappe.new_doc("Shift Schedule Assignment")
	assignment.shift_schedule = schedule
	assignment.employee = employee
	assignment.company = "_Test Company"
	assignment.enabled = enabled
	assignment.create_shifts_after = create_shifts_after or getdate()
	assignment.save()
	return assignment
