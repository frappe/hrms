# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import frappe
from frappe.utils import nowdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.job_offer.test_job_offer import create_job_offer
from hrms.tests.test_utils import create_job_applicant
from hrms.tests.utils import HRMSTestSuite


class TestJobApplicant(HRMSTestSuite):
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
		self.assertEqual(job_offer.status, "Awaiting Response")

		# create employee
		make_employee(user=applicant.name, job_applicant=applicant.name, company="_Test Company")

		# after creating employee
		applicant.reload()
		self.assertEqual(applicant.status, "Accepted")
		job_offer.reload()
		self.assertEqual(job_offer.status, "Accepted")

	def test_status_entered_on_set_on_creation(self):
		applicant = create_job_applicant(applicant_name="_Test Applicant Status Tracking", email_id="test.status.tracking@example.com")
		self.assertIsNotNone(applicant.status_entered_on)
		self.assertEqual(len(applicant.status_change_log), 0)
		frappe.db.commit()

	def test_status_change_appends_log_entry(self):
		applicant = create_job_applicant(applicant_name="_Test Applicant Status Tracking 2", email_id="test.status.tracking2@example.com")
		first_status_entered_on = applicant.status_entered_on

		# simulate moving to the next status
		applicant.status = "Replied"
		applicant.save()
		applicant.reload()

		self.assertEqual(len(applicant.status_change_log), 1)

		log_entry = applicant.status_change_log[0]
		self.assertEqual(log_entry.previous_status, "Open")
		self.assertEqual(log_entry.new_status, "Replied")
		self.assertEqual(log_entry.changed_by, frappe.session.user)
		self.assertIsNotNone(log_entry.time_in_previous_status)

		# status_entered_on should have been refreshed to a later timestamp
		self.assertGreater(applicant.status_entered_on, first_status_entered_on)
		frappe.db.commit()

	def test_no_log_entry_when_status_unchanged(self):
		applicant = create_job_applicant(applicant_name="_Test Applicant Status Tracking 3", email_id="test.status.tracking3@example.com")

		# save again without changing status
		applicant.notes = "Just a regular update"
		applicant.save()
		applicant.reload()

		self.assertEqual(len(applicant.status_change_log), 0)
		frappe.db.commit()
