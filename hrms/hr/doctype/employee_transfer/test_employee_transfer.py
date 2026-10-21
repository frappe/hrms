# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.employee import InactiveEmployeeStatusError
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.tests.utils import HRMSTestSuite


class TestEmployeeTransfer(HRMSTestSuite):
	def setUp(self):
		create_company()

	def test_submit_before_transfer_date(self):
		make_employee("employee2@transfers.com", company="Test Company")

		transfer_obj = frappe.get_doc(
			{
				"doctype": "Employee Transfer",
				"employee": frappe.get_value("Employee", {"user_id": "employee2@transfers.com"}, "name"),
				"transfer_details": [
					{
						"property": "Designation",
						"current": "Software Developer",
						"new": "Project Manager",
						"fieldname": "designation",
					}
				],
			}
		)
		transfer_obj.transfer_date = add_days(getdate(), 1)
		transfer_obj.save()
		self.assertRaises(frappe.DocstatusTransitionError, transfer_obj.submit)
		transfer = frappe.get_doc("Employee Transfer", transfer_obj.name)
		transfer.transfer_date = getdate()
		transfer.submit()
		self.assertEqual(transfer.docstatus, 1)

	def test_new_employee_creation(self):
		make_employee("employee3@transfers.com", company="Test Company")

		transfer = frappe.get_doc(
			{
				"doctype": "Employee Transfer",
				"employee": frappe.get_value("Employee", {"user_id": "employee3@transfers.com"}, "name"),
				"create_new_employee_id": 1,
				"transfer_date": getdate(),
				"transfer_details": [
					{
						"property": "Designation",
						"current": "Software Developer",
						"new": "Project Manager",
						"fieldname": "designation",
					}
				],
			}
		).insert()
		transfer.submit()
		self.assertTrue(transfer.new_employee_id)
		self.assertEqual(frappe.get_value("Employee", transfer.new_employee_id, "status"), "Active")
		self.assertEqual(frappe.get_value("Employee", transfer.employee, "status"), "Left")

	def test_employee_history(self):
		employee = make_employee(
			"employee4@transfers.com",
			company="Test Company",
			date_of_birth=getdate("30-09-1980"),
			date_of_joining=getdate("01-10-2021"),
			department="Accounts - TC",
			designation="Accountant",
		)
		transfer = create_employee_transfer(employee)

		count = 0
		department = ["Accounts - TC", "Management - TC"]
		designation = ["Accountant", "Manager"]
		dt = [getdate("01-10-2021"), getdate()]
		to_date = [add_days(dt[1], -1), None]

		employee = frappe.get_doc("Employee", employee)
		for data in employee.internal_work_history:
			self.assertEqual(data.department, department[count])
			self.assertEqual(data.designation, designation[count])
			self.assertEqual(data.from_date, dt[count])
			self.assertEqual(data.to_date, to_date[count])
			count = count + 1

		transfer.cancel()
		employee.reload()

		for data in employee.internal_work_history:
			self.assertEqual(data.designation, designation[0])
			self.assertEqual(data.department, department[0])
			self.assertEqual(data.from_date, dt[0])
			self.assertEqual(data.to_date, None)

	def test_cancel_cross_company_transfer_restores_date_of_joining(self):
		employee = make_employee(
			"employee5@transfers.com",
			company="Test Company",
			date_of_joining=getdate("01-10-2021"),
			designation="Accountant",
		)
		transfer = frappe.get_doc(
			{
				"doctype": "Employee Transfer",
				"employee": employee,
				"transfer_date": getdate(),
				"new_company": "_Test Company",
				"transfer_details": [
					{
						"property": "Designation",
						"current": "Accountant",
						"new": "Manager",
						"fieldname": "designation",
					}
				],
			}
		).insert()
		transfer.submit()
		self.assertEqual(
			frappe.db.get_value("Employee", employee, ["company", "date_of_joining"]),
			("_Test Company", getdate()),
		)

		transfer.cancel()
		self.assertEqual(
			frappe.db.get_value("Employee", employee, ["company", "date_of_joining", "designation"]),
			("Test Company", getdate("01-10-2021"), "Accountant"),
		)

	def test_cancel_new_employee_transfer_restores_user(self):
		user = "employee6@transfers.com"
		employee = make_employee(user, company="Test Company")
		transfer = frappe.get_doc(
			{
				"doctype": "Employee Transfer",
				"employee": employee,
				"create_new_employee_id": 1,
				"transfer_date": getdate(),
				"transfer_details": [
					{
						"property": "Designation",
						"current": "Software Developer",
						"new": "Project Manager",
						"fieldname": "designation",
					}
				],
			}
		).insert()
		transfer.submit()
		self.assertEqual(frappe.db.get_value("Employee", transfer.new_employee_id, "user_id"), user)
		self.assertFalse(frappe.db.get_value("Employee", employee, "user_id"))

		frappe.db.delete("User Permission", {"allow": "Employee", "for_value": transfer.new_employee_id})
		frappe.delete_doc("Employee", transfer.new_employee_id)
		transfer.reload()
		transfer.cancel()
		self.assertEqual(frappe.db.get_value("Employee", employee, ["status", "user_id"]), ("Active", user))

	def test_transfer_for_left_employee(self):
		employee = make_employee("employee7@transfers.com", company="Test Company")
		frappe.db.set_value(
			"Employee", employee, {"status": "Left", "relieving_date": add_days(getdate(), -30)}
		)

		transfer = frappe.get_doc(
			{
				"doctype": "Employee Transfer",
				"employee": employee,
				"transfer_date": getdate(),
				"transfer_details": [
					{
						"property": "Designation",
						"current": "Software Developer",
						"new": "Project Manager",
						"fieldname": "designation",
					}
				],
			}
		)
		self.assertRaises(InactiveEmployeeStatusError, transfer.insert)

	@HRMSTestSuite.change_settings("System Settings", {"number_format": "#.###,##"})
	def test_data_formatting_in_history(self):
		from hrms.hr.utils import get_formatted_value

		value = get_formatted_value("12.500,00", "Float")
		self.assertEqual(value, 12500.0)

		value = get_formatted_value("12.500,00", "Currency")
		self.assertEqual(value, 12500.0)


def create_company():
	if not frappe.db.exists("Company", "Test Company"):
		frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": "Test Company",
				"default_currency": "INR",
				"country": "India",
			}
		).insert()


def create_employee_transfer(employee):
	doc = frappe.get_doc(
		{
			"doctype": "Employee Transfer",
			"employee": employee,
			"transfer_date": getdate(),
			"transfer_details": [
				{
					"property": "Designation",
					"current": "Accountant",
					"new": "Manager",
					"fieldname": "designation",
				},
				{
					"property": "Department",
					"current": "Accounts - TC",
					"new": "Management - TC",
					"fieldname": "department",
				},
			],
		}
	)

	doc.save()
	doc.submit()

	return doc
