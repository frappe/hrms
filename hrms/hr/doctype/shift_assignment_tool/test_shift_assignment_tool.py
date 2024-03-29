# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.shift_assignment_tool.shift_assignment_tool import ShiftAssignmentTool
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

	def test_get_employees(self):
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

		# does not exclude emp1 as dates don't overlap
		make_shift_assignment(self.shift3.name, self.emp1, add_days(today, -5), add_days(today, -1))
		# excludes emp2 due to overlapping dates
		make_shift_assignment(self.shift3.name, self.emp2, add_days(today, 6))
		# excludes emp3 due to overlapping dates
		make_shift_assignment(self.shift3.name, self.emp3, today)

		advanced_filters = [["employee_name", "like", "%test.com%"]]  # excludes emp5
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
