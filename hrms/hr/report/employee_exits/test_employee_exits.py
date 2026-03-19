import frappe
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.exit_interview.test_exit_interview import create_exit_interview
from hrms.hr.doctype.full_and_final_statement.test_full_and_final_statement import (
	create_full_and_final_statement,
)
from hrms.hr.report.employee_exits.employee_exits import execute
from hrms.tests.test_utils import create_company
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeExits(HRMSTestSuite):
	def setUp(self):
		self.company = create_company("Test Company").name
		self.create_records()

	def create_records(self):
		self.emp1 = make_employee(
			"employeeexit1@example.com",
			company=self.company,
			date_of_joining=getdate("01-10-2021"),
			relieving_date=add_days(getdate(), 14),
			designation="Accountant",
		)
		self.emp2 = make_employee(
			"employeeexit2@example.com",
			company=self.company,
			date_of_joining=getdate("01-12-2021"),
			relieving_date=add_days(getdate(), 15),
			designation="Accountant",
		)

		self.emp3 = make_employee(
			"employeeexit3@example.com",
			company=self.company,
			date_of_joining=getdate("02-12-2021"),
			relieving_date=add_days(getdate(), 29),
			designation="Engineer",
		)
		self.emp4 = make_employee(
			"employeeexit4@example.com",
			company=self.company,
			date_of_joining=getdate("01-12-2021"),
			relieving_date=add_days(getdate(), 30),
			designation="Engineer",
		)

		# exit interview for 3 employees only
		self.interview1 = create_exit_interview(self.emp1)
		self.interview2 = create_exit_interview(self.emp2)
		self.interview3 = create_exit_interview(self.emp3)

		# create fnf for some records
		self.fnf1 = create_full_and_final_statement(self.emp1)
		self.fnf2 = create_full_and_final_statement(self.emp2)

		# link questionnaire for a few records
		# setting employee doctype as reference instead of creating a questionnaire
		# since this is just for a test
		frappe.db.set_value(
			"Exit Interview",
			self.interview1.name,
			{"ref_doctype": "Employee", "reference_document_name": self.emp1},
		)

		frappe.db.set_value(
			"Exit Interview",
			self.interview2.name,
			{"ref_doctype": "Employee", "reference_document_name": self.emp2},
		)

		frappe.db.set_value(
			"Exit Interview",
			self.interview3.name,
			{"ref_doctype": "Employee", "reference_document_name": self.emp3},
		)

	def test_employee_exits_summary(self):
		filters = {
			"company": "Test Company",
			"from_date": getdate(),
			"to_date": add_days(getdate(), 15),
			"designation": "Accountant",
		}

		report = execute(filters)

		employee1 = frappe.get_doc("Employee", self.emp1)
		employee2 = frappe.get_doc("Employee", self.emp2)
		expected_data = [
			{
				"employee": employee1.name,
				"employee_name": employee1.employee_name,
				"date_of_joining": employee1.date_of_joining,
				"relieving_date": employee1.relieving_date,
				"department": employee1.department,
				"designation": employee1.designation,
				"reports_to": None,
				"exit_interview": self.interview1.name,
				"interview_status": self.interview1.status,
				"employee_status": "",
				"questionnaire": employee1.name,
				"full_and_final_statement": self.fnf1.name,
			},
			{
				"employee": employee2.name,
				"employee_name": employee2.employee_name,
				"date_of_joining": employee2.date_of_joining,
				"relieving_date": employee2.relieving_date,
				"department": employee2.department,
				"designation": employee2.designation,
				"reports_to": None,
				"exit_interview": self.interview2.name,
				"interview_status": self.interview2.status,
				"employee_status": "",
				"questionnaire": employee2.name,
				"full_and_final_statement": self.fnf2.name,
			},
		]

		self.assertEqual(expected_data, report[1])  # rows

	def test_pending_exit_interviews_summary(self):
		filters = {
			"company": "Test Company",
			"from_date": getdate(),
			"to_date": add_days(getdate(), 30),
			"exit_interview_pending": 1,
		}

		report = execute(filters)

		employee4 = frappe.get_doc("Employee", self.emp4)
		expected_data = [
			{
				"employee": employee4.name,
				"employee_name": employee4.employee_name,
				"date_of_joining": employee4.date_of_joining,
				"relieving_date": employee4.relieving_date,
				"department": employee4.department,
				"designation": employee4.designation,
				"reports_to": None,
				"exit_interview": None,
				"interview_status": None,
				"employee_status": None,
				"questionnaire": None,
				"full_and_final_statement": None,
			}
		]

		self.assertEqual(expected_data, report[1])  # rows

	def test_pending_exit_questionnaire_summary(self):
		filters = {
			"company": "Test Company",
			"from_date": getdate(),
			"to_date": add_days(getdate(), 30),
			"questionnaire_pending": 1,
		}

		report = execute(filters)

		employee4 = frappe.get_doc("Employee", self.emp4)
		expected_data = [
			{
				"employee": employee4.name,
				"employee_name": employee4.employee_name,
				"date_of_joining": employee4.date_of_joining,
				"relieving_date": employee4.relieving_date,
				"department": employee4.department,
				"designation": employee4.designation,
				"reports_to": None,
				"exit_interview": None,
				"interview_status": None,
				"employee_status": None,
				"questionnaire": None,
				"full_and_final_statement": None,
			}
		]

		self.assertEqual(expected_data, report[1])  # rows

	def test_pending_fnf_summary(self):
		filters = {"company": "Test Company", "fnf_pending": 1}

		report = execute(filters)

		employee3 = frappe.get_doc("Employee", self.emp3)
		employee4 = frappe.get_doc("Employee", self.emp4)
		expected_data = [
			{
				"employee": employee3.name,
				"employee_name": employee3.employee_name,
				"date_of_joining": employee3.date_of_joining,
				"relieving_date": employee3.relieving_date,
				"department": employee3.department,
				"designation": employee3.designation,
				"reports_to": None,
				"exit_interview": self.interview3.name,
				"interview_status": self.interview3.status,
				"employee_status": "",
				"questionnaire": employee3.name,
				"full_and_final_statement": None,
			},
			{
				"employee": employee4.name,
				"employee_name": employee4.employee_name,
				"date_of_joining": employee4.date_of_joining,
				"relieving_date": employee4.relieving_date,
				"department": employee4.department,
				"designation": employee4.designation,
				"reports_to": None,
				"exit_interview": None,
				"interview_status": None,
				"employee_status": None,
				"questionnaire": None,
				"full_and_final_statement": None,
			},
		]

		self.assertEqual(expected_data, report[1])  # rows
