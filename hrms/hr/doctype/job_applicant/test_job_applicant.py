# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate, nowdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.interview.test_interview import create_interview_type
from hrms.hr.doctype.job_applicant.job_applicant import create_interview
from hrms.hr.doctype.job_applicant.job_applicant import make_employee as map_applicant_to_employee
from hrms.hr.doctype.job_offer.test_job_offer import create_job_offer
from hrms.hr.doctype.job_opening.job_opening import get_published_job_title
from hrms.hr.doctype.job_opening.test_job_opening import get_job_opening
from hrms.tests.test_utils import create_job_applicant
from hrms.tests.utils import HRMSTestSuite, make_user


class TestJobApplicant(HRMSTestSuite):
	def test_onload_filters_out_cancelled_job_offer(self):
		applicant = create_job_applicant()
		job_offer = create_job_offer(job_applicant=applicant.name)
		job_offer.submit()
		job_offer.cancel()

		applicant.onload()
		onload = applicant.get("__onload") or {}
		self.assertNotIn("job_offer", onload)

		# positive case: active job offer should be loaded
		active_job_offer = create_job_offer(job_applicant=applicant.name)
		active_job_offer.submit()

		applicant.onload()
		onload = applicant.get("__onload") or {}
		self.assertEqual(onload.get("job_offer"), active_job_offer.name)

	def test_web_form_application_needs_published_open_opening(self):
		opening = get_job_opening(job_title="Web Form Opening", company="_Test Company").insert()

		def apply(email):
			return frappe.get_doc(
				{
					"doctype": "Job Applicant",
					"applicant_name": "_Test Web Applicant",
					"email_id": email,
					"job_title": opening.name,
				}
			).insert()

		frappe.flags.in_web_form = True
		try:
			self.assertRaises(frappe.ValidationError, apply, "web_form_unpublished@example.com")
			self.assertIsNone(get_published_job_title(opening.name))

			opening.reload()
			opening.publish = 1
			opening.posted_on = add_days(getdate(), -5)
			opening.closes_on = add_days(getdate(), -1)
			opening.save()
			self.assertRaises(frappe.ValidationError, apply, "web_form_expired@example.com")

			opening.db_set("closes_on", None)
			self.assertEqual(apply("web_form_published@example.com").job_title, opening.name)
			self.assertEqual(get_published_job_title(opening.name), "Web Form Opening")
		finally:
			frappe.flags.in_web_form = False

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
		job_offer = create_job_offer(
			job_applicant=applicant.name, status="Awaiting Response", company="_Test Company"
		)
		job_offer.save()

		# before creating employee
		self.assertEqual(applicant.status, "Open")
		self.assertEqual(job_offer.status, "Draft")

		# create employee
		make_employee(user=applicant.name, job_applicant=applicant.name, company="_Test Company")

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

	def test_create_interview_permission(self):
		applicant = create_job_applicant()
		interviewer = make_user("test_interviewer1@example.com", "Interviewer")
		hr_user = make_user("test_hr_user_interview@example.com", "HR User")
		interview_type = create_interview_type("Technical Round", ["Python"], [interviewer])

		with self.set_user(interviewer):
			self.assertRaises(frappe.PermissionError, create_interview, applicant.name, interview_type.name)

		with self.set_user(hr_user):
			interview = create_interview(applicant.name, interview_type.name)
			self.assertEqual(interview.job_applicant, applicant.name)
