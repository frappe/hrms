# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate

from hrms.payroll.doctype.salary_structure.test_salary_structure import make_employee
from hrms.tests.utils import HRMSTestSuite


class TestEmployeePromotion(HRMSTestSuite):
	def test_cancel_preserves_other_employees_and_earlier_history(self):
		employees = []
		promotions = []
		for index in range(2):
			employee = frappe.get_doc(
				"Employee",
				make_employee(
					f"promotion_history_scope_{index}@example.com",
					company="_Test Company",
					date_of_joining=add_days(getdate(), -30),
					designation="Software Developer",
				),
			)
			employee.append(
				"internal_work_history",
				{"designation": "Project Manager", "from_date": add_days(getdate(), -30)},
			)
			employee.append(
				"internal_work_history",
				{"designation": "Software Developer", "from_date": add_days(getdate(), -20)},
			)
			employee.save()
			promotion = frappe.get_doc(
				{
					"doctype": "Employee Promotion",
					"employee": employee.name,
					"promotion_date": getdate(),
					"promotion_details": [
						{
							"property": "Designation",
							"fieldname": "designation",
							"current": "Software Developer",
							"new": "Project Manager",
						}
					],
				}
			).submit()
			employees.append(employee.reload())
			promotions.append(promotion)

		other_history = [row.as_dict() for row in employees[1].internal_work_history]
		retained_names = [row.name for row in employees[0].internal_work_history[:-1]]
		promotions[0].cancel()

		self.assertEqual(
			[row.as_dict() for row in employees[1].reload().internal_work_history], other_history
		)
		self.assertEqual([row.name for row in employees[0].reload().internal_work_history], retained_names)
		self.assertIsNone(employees[0].internal_work_history[-1].to_date)

	def test_submit_before_promotion_date(self):
		employee = make_employee("employee@promotions.com", company="_Test Company")
		promotion = frappe.get_doc(
			{
				"doctype": "Employee Promotion",
				"employee": employee,
				"promotion_details": [
					{
						"property": "Designation",
						"current": "Software Developer",
						"new": "Project Manager",
						"fieldname": "designation",
					}
				],
			}
		)
		promotion.promotion_date = add_days(getdate(), 1)
		self.assertRaises(frappe.DocstatusTransitionError, promotion.submit)

		promotion.promotion_date = getdate()
		promotion.submit()
		self.assertEqual(promotion.docstatus, 1)

	def test_employee_history(self):
		for grade in ["L1", "L2"]:
			frappe.get_doc({"doctype": "Employee Grade", "__newname": grade}).insert()

		employee = make_employee(
			"test_employee_promotion@example.com",
			company="_Test Company",
			date_of_birth=getdate("30-09-1980"),
			date_of_joining=getdate("01-10-2021"),
			designation="Software Developer",
			grade="L1",
			salary_currency="INR",
			ctc="500000",
		)

		promotion = frappe.get_doc(
			{
				"doctype": "Employee Promotion",
				"employee": employee,
				"promotion_date": getdate(),
				"revised_ctc": "1000000",
				"promotion_details": [
					{
						"property": "Designation",
						"current": "Software Developer",
						"new": "Project Manager",
						"fieldname": "designation",
					},
					{"property": "Grade", "current": "L1", "new": "L2", "fieldname": "grade"},
				],
			}
		).submit()

		# employee fields updated
		employee = frappe.get_doc("Employee", employee)
		self.assertEqual(employee.grade, "L2")
		self.assertEqual(employee.designation, "Project Manager")
		self.assertEqual(employee.ctc, 1000000)

		# internal work history updated
		self.assertEqual(employee.internal_work_history[0].designation, "Software Developer")
		self.assertEqual(employee.internal_work_history[0].from_date, getdate("01-10-2021"))

		self.assertEqual(employee.internal_work_history[1].designation, "Project Manager")
		self.assertEqual(employee.internal_work_history[1].from_date, getdate())

		promotion.cancel()
		employee.reload()

		# fields restored
		self.assertEqual(employee.grade, "L1")
		self.assertEqual(employee.designation, "Software Developer")
		self.assertEqual(employee.ctc, 500000)

		# internal work history updated on cancellation
		self.assertEqual(len(employee.internal_work_history), 1)
		self.assertEqual(employee.internal_work_history[0].designation, "Software Developer")
		self.assertEqual(employee.internal_work_history[0].from_date, getdate("01-10-2021"))
