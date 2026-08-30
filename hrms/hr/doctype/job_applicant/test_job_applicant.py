# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.job_applicant.job_applicant import make_employee as map_applicant_to_employee
from hrms.hr.doctype.job_offer.test_job_offer import create_job_offer
from hrms.hr.doctype.job_opening.test_job_opening import get_job_opening
from hrms.tests.test_utils import create_job_applicant


class TestJobApplicant(FrappeTestCase):
	def test_job_applicant_naming(self):
		applicant = frappe.get_doc(
			{
				"doctype": "Job Applicant",
				"status": "Open",
				"applicant_name": "_Test Applicant",
				"email_id": "job_applicant_naming@example.com",
			}
		).insert()
		self.assertEqual(applicant.name, "job_applicant_naming@example.com")

		applicant = frappe.get_doc(
			{
				"doctype": "Job Applicant",
				"status": "Open",
				"applicant_name": "_Test Applicant",
				"email_id": "job_applicant_naming@example.com",
			}
		).insert()
		self.assertEqual(applicant.name, "job_applicant_naming@example.com-1")

	def test_update_applicant_to_employee(self):
		applicant = create_job_applicant()
		job_offer = create_job_offer(job_applicant=applicant.name, status="Awaiting Response")
		job_offer.save()

		# before creating employee
		self.assertEqual(applicant.status, "Open")
		self.assertEqual(job_offer.status, "Awaiting Response")

		# create employee
		make_employee(user=applicant.name, job_applicant=applicant.name)

		# after creating employee
		applicant.reload()
		self.assertEqual(applicant.status, "Accepted")
		job_offer.reload()
		self.assertEqual(job_offer.status, "Accepted")

	def test_make_employee(self):
		opening = get_job_opening(
			job_title="Mapped Applicant Role",
			designation="Software Developer",
			company="_Test Company",
			department="_Test Department - _TC",
		).insert()

		applicant = frappe.get_doc(
			{
				"doctype": "Job Applicant",
				"applicant_name": "Jane Mapped",
				"email_id": "jane.mapped@example.com",
				"phone_number": "1234567890",
				"designation": "Software Developer",
				"job_title": opening.name,
				"currency": "INR",
				"status": "Accepted",
			}
		).insert()

		employee = map_applicant_to_employee(applicant.name)

		self.assertEqual(employee.doctype, "Employee")
		self.assertEqual(employee.job_applicant, applicant.name)
		self.assertEqual(employee.first_name, "Jane Mapped")
		self.assertEqual(employee.employee_name, "Jane Mapped")
		self.assertEqual(employee.personal_email, "jane.mapped@example.com")
		self.assertEqual(employee.cell_number, "1234567890")
		self.assertEqual(employee.designation, "Software Developer")
		self.assertEqual(employee.salary_currency, "INR")
		self.assertEqual(employee.status, "Active")
		self.assertEqual(employee.company, "_Test Company")
		self.assertEqual(employee.department, "_Test Department - _TC")

	def tearDown(self):
		frappe.db.rollback()
