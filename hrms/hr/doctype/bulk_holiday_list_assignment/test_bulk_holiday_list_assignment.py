# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee
from erpnext.setup.doctype.holiday_list.test_holiday_list import make_holiday_list

from hrms.hr.doctype.bulk_holiday_list_assignment.bulk_holiday_list_assignment import (
	BulkHolidayListAssignment,
)
from hrms.tests.test_utils import create_company, create_department
from hrms.tests.utils import HRMSTestSuite


class TestBulkHolidayListAssignment(HRMSTestSuite):
	def setUp(self):
		create_company()
		self.department = create_department("Accounts")

		self.today = getdate()
		self.holiday_list = make_holiday_list(
			"Bulk Assignment Test Holiday List",
			from_date=add_days(self.today, -10),
			to_date=add_days(self.today, 10),
		).name

		self.emp1 = make_employee(
			"employee1@bhla.com", company="_Test Company", department=self.department
		)
		self.emp2 = make_employee(
			"employee2@bhla.com", company="_Test Company", department=self.department
		)
		# no department
		self.emp3 = make_employee("employee3@bhla.com", company="_Test Company")

	def make_assignment(self, employee, holiday_list, from_date):
		frappe.get_doc(
			{
				"doctype": "Holiday List Assignment",
				"applicable_for": "Employee",
				"assigned_to": employee,
				"holiday_list": holiday_list,
				"from_date": from_date,
			}
		).submit()

	def test_get_employees(self):
		# assignment falls within the chosen holiday list's period
		self.make_assignment(self.emp2, self.holiday_list, add_days(self.today, -5))

		args = {
			"doctype": "Bulk Holiday List Assignment",
			"holiday_list": self.holiday_list,
			"from_date": self.today,
			"department": self.department,
		}
		bulk_assignment = BulkHolidayListAssignment(args)
		employee_names = [d.employee for d in bulk_assignment.get_employees([])]

		# employee already has an assignment within this holiday list's period
		self.assertNotIn(self.emp2, employee_names)
		# department quick filter applied
		self.assertNotIn(self.emp3, employee_names)
		self.assertIn(self.emp1, employee_names)
		self.assertEqual(len(employee_names), 1)

	def test_get_employees_ignores_assignment_outside_chosen_holiday_list_period(self):
		# an assignment that starts before the chosen holiday list's period
		# even begins should not count as "already assigned" for this period
		earlier_holiday_list = make_holiday_list(
			"Bulk Assignment Earlier Holiday List",
			from_date=add_days(self.today, -30),
			to_date=add_days(self.today, -20),
		).name
		self.make_assignment(self.emp1, earlier_holiday_list, add_days(self.today, -25))

		args = {
			"doctype": "Bulk Holiday List Assignment",
			"holiday_list": self.holiday_list,
			"from_date": self.today,
			"department": self.department,
		}
		bulk_assignment = BulkHolidayListAssignment(args)
		employee_names = [d.employee for d in bulk_assignment.get_employees([])]

		self.assertIn(self.emp1, employee_names)

	def test_bulk_assign_holiday_list(self):
		args = {
			"doctype": "Bulk Holiday List Assignment",
			"holiday_list": self.holiday_list,
			"from_date": self.today,
		}
		bulk_assignment = BulkHolidayListAssignment(args)
		bulk_assignment.bulk_assign_holiday_list([self.emp1, self.emp2])

		for employee in [self.emp1, self.emp2]:
			assignment = frappe.get_value(
				"Holiday List Assignment",
				{"assigned_to": employee, "docstatus": 1},
				["holiday_list", "from_date", "applicable_for"],
				as_dict=1,
			)
			self.assertEqual(assignment.holiday_list, self.holiday_list)
			self.assertEqual(assignment.from_date, self.today)
			self.assertEqual(assignment.applicable_for, "Employee")
