# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.bulk_salary_structure_assignment.bulk_salary_structure_assignment import (
	BulkSalaryStructureAssignment,
)
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from hrms.tests.test_utils import create_company, create_department, create_employee_grade
from hrms.tests.utils import HRMSTestSuite


class TestBulkSalaryStructureAssignment(HRMSTestSuite):
	def setUp(self):
		create_company()
		self.department = create_department("Accounts")
		self.grade = create_employee_grade("Test Grade")

		# employee grade with default base pay 50000
		self.emp1 = make_employee(
			"employee1@bssa.com", company="_Test Company", department=self.department, grade=self.grade.name
		)
		self.emp2 = make_employee("employee2@bssa.com", company="_Test Company", department=self.department)
		self.emp3 = make_employee("employee3@bssa.com", company="_Test Company", department=self.department)
		# no department
		self.emp4 = make_employee("employee4@bssa.com", company="_Test Company")
		# different domain in employee_name
		self.emp5 = make_employee("employee5@test.com", company="_Test Company", department=self.department)

	def test_get_employees(self):
		today = getdate()

		# create structure and assign to emp2
		make_salary_structure("Salary Structure 1", "Monthly", self.emp2, today, company="_Test Company")

		args = {
			"doctype": "Bulk Salary Structure Assignment",
			"from_date": today,
			"company": "_Test Company",
			"department": self.department,
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
		self.assertEqual(employees[0].base, self.grade.default_base_pay)
		# no employee grade
		self.assertEqual(employees[1].base, 0)
		self.assertEqual(len(employees), 2)

	def test_grade_base_not_prefilled_in_another_currency(self):
		structure = make_salary_structure(
			"Salary Structure INR", "Monthly", company="_Test Company", currency="INR"
		)
		frappe.db.set_value("Employee Grade", self.grade.name, "currency", "USD")

		bulk_assignment = BulkSalaryStructureAssignment(
			{
				"doctype": "Bulk Salary Structure Assignment",
				"from_date": getdate(),
				"company": "_Test Company",
				"department": self.department,
				"salary_structure": structure.name,
			}
		)
		employees = bulk_assignment.get_employees([["Employee", "name", "=", self.emp1]])
		self.assertEqual(employees[0].base, 0)

		frappe.db.set_value("Employee Grade", self.grade.name, "currency", "INR")
		employees = bulk_assignment.get_employees([["Employee", "name", "=", self.emp1]])
		self.assertEqual(employees[0].base, self.grade.default_base_pay)

	def test_bulk_assign_structure(self):
		today = getdate()
		salary_structure = make_salary_structure("Salary Structure 1", "Monthly", company="_Test Company")

		args = {
			"doctype": "Bulk Salary Structure Assignment",
			"salary_structure": salary_structure.name,
			"from_date": today,
			"company": "_Test Company",
		}
		bulk_assignment = BulkSalaryStructureAssignment(args)

		employees = [
			{"employee": self.emp1, "base": 50000, "variable": 2000},
			{"employee": self.emp2, "base": 40000, "variable": 0},
		]
		bulk_assignment.bulk_assign_structure(employees)

		ssa1 = frappe.get_value(
			"Salary Structure Assignment",
			{"employee": self.emp1},
			["salary_structure", "from_date", "company", "base", "variable"],
			as_dict=1,
		)
		self.assertEqual(ssa1.salary_structure, salary_structure.name)
		self.assertEqual(ssa1.from_date, today)
		self.assertEqual(ssa1.company, "_Test Company")
		self.assertEqual(ssa1.base, 50000)
		self.assertEqual(ssa1.variable, 2000)

		ssa2 = frappe.get_value(
			"Salary Structure Assignment",
			{"employee": self.emp2},
			["base", "variable"],
			as_dict=1,
		)
		self.assertEqual(ssa2.base, 40000)
		self.assertEqual(ssa2.variable, 0)

	def test_user_permissions_applied(self):
		today = getdate()
		other_employee = make_employee("employee6@bssa.com", company="_Test Company 1")
		salary_structure = make_salary_structure("Salary Structure 1", "Monthly", company="_Test Company")

		user = "bssa_restricted@example.com"
		if not frappe.db.exists("User", user):
			frappe.get_doc({"doctype": "User", "email": user, "first_name": "BSSA"}).insert()
		frappe.get_doc("User", user).add_roles("HR User", "HR Manager")
		frappe.get_doc(
			{"doctype": "User Permission", "user": user, "allow": "Company", "for_value": "_Test Company"}
		).insert()

		bulk_assignment = BulkSalaryStructureAssignment(
			{
				"doctype": "Bulk Salary Structure Assignment",
				"salary_structure": salary_structure.name,
				"from_date": today,
				"company": "_Test Company 1",
			}
		)
		frappe.set_user(user)
		try:
			self.assertEqual(bulk_assignment.get_employees([]), [])

			bulk_assignment.company = "_Test Company"
			employees = bulk_assignment.get_employees([["Employee", "company", "=", "_Test Company 1"]])
			self.assertEqual(employees, [])

			self.assertRaises(
				frappe.PermissionError,
				bulk_assignment.bulk_assign_structure,
				[{"employee": other_employee, "base": 99999, "variable": 0}],
			)
		finally:
			frappe.set_user("Administrator")

		self.assertFalse(frappe.db.exists("Salary Structure Assignment", {"employee": other_employee}))
