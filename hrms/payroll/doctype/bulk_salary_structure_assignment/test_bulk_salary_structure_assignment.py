# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.bulk_salary_structure_assignment.bulk_salary_structure_assignment import (
	BulkSalaryStructureAssignment,
)
from hrms.payroll.doctype.salary_structure.test_salary_structure import (
	create_employee_grade,
	make_salary_structure,
)
from hrms.tests.test_utils import create_company, create_department


class TestBulkSalaryStructureAssignment(FrappeTestCase):
	def setUp(self):
		create_company()
		create_department("Accounts")
		create_employee_grade("Test Grade")

		# employee grade with default base pay 50000
		self.emp1 = make_employee(
			"employee1@bssa.com", company="_Test Company", department="Accounts", grade="Test Grade"
		)
		self.emp2 = make_employee("employee2@bssa.com", company="_Test Company", department="Accounts")
		self.emp3 = make_employee("employee3@bssa.com", company="_Test Company", department="Accounts")
		# no department
		self.emp4 = make_employee("employee4@bssa.com", company="_Test Company")
		# different domain in employee_name
		self.emp5 = make_employee("employee5@test.com", company="_Test Company", department="Accounts")

	def tearDown(self):
		frappe.db.rollback()

	def test_get_employees(self):
		today = getdate()

		# create structure and assign to emp2
		make_salary_structure("Salary Structure 1", "Monthly", self.emp2, today, company="_Test Company")

		args = {
			"doctype": "Bulk Salary Structure Assignment",
			"from_date": today,
			"department": "Accounts",
		}
		bulk_assignment = BulkSalaryStructureAssignment(args)

		advanced_filters = [["Employee", "employee_name", "like", "%bssa%"]]
		employees = bulk_assignment.get_employees(advanced_filters)
		employee_names = [d.name for d in employees]

		# employee already having an assignment
		self.assertNotIn(self.emp2, employee_names)
		# department quick filter applied
		self.assertNotIn(self.emp4, employee_names)
		# employee_name advanced filter applied
		self.assertNotIn(self.emp5, employee_names)
		# employee grade default base pay fetched
		self.assertEqual(employees[0].base, 50000)
		# no employee grade
		self.assertFalse(employees[1].base)
		self.assertEqual(len(employees), 2)
