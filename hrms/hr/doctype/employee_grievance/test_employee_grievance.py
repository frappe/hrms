# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from erpnext.setup.doctype.employee.test_employee import make_employee


class TestEmployeeGrievance(IntegrationTestCase):
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
