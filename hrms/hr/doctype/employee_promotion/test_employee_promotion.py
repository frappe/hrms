# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.employee import InactiveEmployeeStatusError

from hrms.payroll.doctype.salary_structure.test_salary_structure import make_employee
from hrms.tests.utils import HRMSTestSuite


class TestEmployeePromotion(HRMSTestSuite):
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

	def test_cancel_only_removes_own_work_history(self):
		if not frappe.db.exists("Branch", "_Test Promotion Branch"):
			frappe.get_doc({"doctype": "Branch", "branch": "_Test Promotion Branch"}).insert()

		other = make_employee(
			"promotion_other@example.com",
			company="_Test Company",
			date_of_joining=getdate("01-01-2020"),
			designation="Software Developer",
		)
		other = frappe.get_doc("Employee", other)
		other.append(
			"internal_work_history", {"designation": "Software Developer", "from_date": "2020-01-01"}
		)
		other.append("internal_work_history", {"designation": "Project Manager", "from_date": "2021-01-01"})
		other.save()

		employee = make_employee(
			"promotion_own@example.com",
			company="_Test Company",
			date_of_joining=getdate("01-01-2020"),
			designation="Software Developer",
			branch="_Test Promotion Branch",
		)
		promotion = create_promotion(employee, getdate(), "Software Developer", "Project Manager")

		new_row = frappe.get_doc("Employee", employee).internal_work_history[-1]
		self.assertEqual(new_row.designation, "Project Manager")
		self.assertEqual(new_row.branch, "_Test Promotion Branch")

		promotion.cancel()

		self.assertEqual(len(frappe.get_doc("Employee", employee).internal_work_history), 1)
		other.reload()
		self.assertEqual(
			[row.designation for row in other.internal_work_history],
			["Software Developer", "Project Manager"],
		)

	def test_back_dated_promotion(self):
		employee = make_employee(
			"promotion_back_dated@example.com",
			company="_Test Company",
			date_of_joining=getdate("01-01-2020"),
			designation="Software Developer",
			ctc=100000,
		)
		later_date, earlier_date = add_days(getdate(), -10), add_days(getdate(), -100)
		later = create_promotion(employee, later_date, "Software Developer", "Manager", revised_ctc=200000)
		create_promotion(employee, earlier_date, "Software Developer", "Project Manager", revised_ctc=150000)

		doc = frappe.get_doc("Employee", employee)
		self.assertEqual(doc.designation, "Manager")
		self.assertEqual(doc.ctc, 200000)
		self.assertEqual(
			[(row.designation, row.from_date, row.to_date) for row in doc.internal_work_history],
			[
				("Software Developer", getdate("01-01-2020"), add_days(earlier_date, -1)),
				("Project Manager", earlier_date, add_days(later_date, -1)),
				("Manager", later_date, None),
			],
		)

		later.cancel()
		doc.reload()
		self.assertEqual(doc.designation, "Project Manager")
		self.assertEqual(doc.ctc, 150000)
		self.assertEqual(
			[(row.designation, row.to_date) for row in doc.internal_work_history],
			[("Software Developer", add_days(earlier_date, -1)), ("Project Manager", None)],
		)

	def test_promotion_for_left_employee(self):
		employee = make_employee(
			"promotion_left@example.com", company="_Test Company", date_of_joining=getdate("01-01-2020")
		)
		frappe.db.set_value(
			"Employee", employee, {"status": "Left", "relieving_date": add_days(getdate(), -30)}
		)

		promotion = frappe.get_doc(
			{
				"doctype": "Employee Promotion",
				"employee": employee,
				"promotion_date": getdate(),
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
		self.assertRaises(InactiveEmployeeStatusError, promotion.insert)


def create_promotion(employee, promotion_date, current, new, revised_ctc=0):
	return frappe.get_doc(
		{
			"doctype": "Employee Promotion",
			"employee": employee,
			"promotion_date": promotion_date,
			"revised_ctc": revised_ctc,
			"promotion_details": [
				{"property": "Designation", "current": current, "new": new, "fieldname": "designation"}
			],
		}
	).submit()
