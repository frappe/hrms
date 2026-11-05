# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, today

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.tests.utils import HRMSTestSuite, make_user


class TestEmployeeGrievance(HRMSTestSuite):
	def test_create_employee_grievance(self):
		grievance_type = create_grievance_type()
		emp_1 = make_employee("test_emp_grievance_@example.com", company="_Test Company")
		emp_2 = make_employee("testculprit@example.com", company="_Test Company")
		grievance = create_employee_grievance(
			raised_by=emp_1, raised_against=emp_2, grievance_type=grievance_type
		)
		self.assertEqual(grievance.raised_by, emp_1)
		self.assertEqual(grievance.grievance_against, emp_2)
		self.assertEqual(grievance.status, "Open")
		grievance.status = "Resolved"
		grievance.submit()

	def test_status_on_discard(self):
		grievance_type = create_grievance_type()
		emp_1 = make_employee("test_emp_grievance_@example.com", company="_Test Company")
		emp_2 = make_employee("testculprit@example.com", company="_Test Company")
		grievance = create_employee_grievance(
			raised_by=emp_1, raised_against=emp_2, grievance_type=grievance_type
		)
		self.assertEqual(grievance.status, "Open")
		grievance.discard()
		grievance.reload()
		self.assertEqual(grievance.status, "Cancelled")

	def test_status_on_cancel(self):
		grievance_type = create_grievance_type()
		emp_1 = make_employee("test_emp_grievance_@example.com", company="_Test Company")
		emp_2 = make_employee("testculprit@example.com", company="_Test Company")
		grievance = create_employee_grievance(
			raised_by=emp_1, raised_against=emp_2, grievance_type=grievance_type
		)
		grievance.status = "Resolved"
		grievance.submit()
		grievance.cancel()
		self.assertEqual(frappe.db.get_value("Employee Grievance", grievance.name, "status"), "Cancelled")

	def test_validations(self):
		grievance_type = create_grievance_type()
		emp_1 = make_employee("test_emp_grievance_@example.com", company="_Test Company")
		emp_2 = make_employee("testculprit@example.com", company="_Test Company")

		self.assertRaises(
			frappe.ValidationError,
			create_employee_grievance,
			raised_by=emp_1,
			raised_against=emp_1,
			grievance_type=grievance_type,
		)

		grievance = create_employee_grievance(
			raised_by=emp_1, raised_against=emp_2, grievance_type=grievance_type
		)
		grievance.resolution_date = add_days(grievance.date, -1)
		self.assertRaises(frappe.ValidationError, grievance.save)

	def test_raiser_cannot_resolve_own_grievance(self):
		grievance_type = create_grievance_type()
		user = make_user("test_grievance_raiser@example.com", "Employee")
		emp_1 = make_employee(user, company="_Test Company")
		emp_2 = make_employee("testculprit@example.com", company="_Test Company")

		frappe.set_user(user)
		try:
			grievance = frappe.get_doc(
				{
					"doctype": "Employee Grievance",
					"subject": "Test Employee Grievance",
					"raised_by": emp_1,
					"date": today(),
					"grievance_type": grievance_type,
					"grievance_against_party": "Employee",
					"grievance_against": emp_2,
					"description": "test descrip",
				}
			).insert()
			self.assertEqual(grievance.status, "Open")

			grievance.description = "updated description"
			grievance.save()

			grievance.status = "Resolved"
			grievance.resolved_by = user
			grievance.resolution_date = today()
			grievance.resolution_detail = "self resolved"
			self.assertRaises(frappe.PermissionError, grievance.save)
		finally:
			frappe.set_user("Administrator")


def create_employee_grievance(raised_by, raised_against, grievance_type):
	grievance = frappe.new_doc("Employee Grievance")
	grievance.subject = "Test Employee Grievance"
	grievance.raised_by = raised_by
	grievance.date = today()
	grievance.grievance_type = grievance_type
	grievance.grievance_against_party = "Employee"
	grievance.grievance_against = raised_against
	grievance.description = "test descrip"

	# set cause
	grievance.cause_of_grievance = "test cause"

	# resolution details
	grievance.resolution_date = today()
	grievance.resolution_detail = "test resolution detail"
	grievance.resolved_by = "test_emp_grievance_@example.com"
	grievance.employee_responsible = raised_against
	grievance.save()
	return grievance


def create_grievance_type():
	if frappe.db.exists("Grievance Type", "Employee Abuse"):
		return frappe.get_doc("Grievance Type", "Employee Abuse").name
	grievance_type = frappe.new_doc("Grievance Type")
	grievance_type.name = "Employee Abuse"
	grievance_type.description = "Test"
	grievance_type.save()

	return grievance_type.name
