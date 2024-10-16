# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, nowdate

from erpnext.setup.doctype.designation.test_designation import create_designation

from hrms.hr.doctype.job_applicant.job_applicant import get_applicant_to_hire_percentage
from hrms.hr.doctype.job_offer.job_offer import get_offer_acceptance_rate
from hrms.hr.doctype.staffing_plan.test_staffing_plan import make_company
from hrms.tests.test_utils import create_job_applicant


class TestJobOffer(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Job Applicant")
		frappe.db.delete("Job Offer")

		create_designation(designation_name="Researcher")

	def test_job_offer_creation_against_vacancies(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 1)
		job_applicant = create_job_applicant(email_id="test_job_offer@example.com")
		job_offer = create_job_offer(job_applicant=job_applicant.name, designation="UX Designer")

		create_staffing_plan(
			name="Test No Vacancies",
			staffing_details=[
				{"designation": "UX Designer", "vacancies": 0, "estimated_cost_per_position": 5000}
			],
		)
		self.assertRaises(frappe.ValidationError, job_offer.submit)

		# test creation of job offer when vacancies are not present
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		job_offer.submit()
		self.assertTrue(frappe.db.exists("Job Offer", job_offer.name))

	def test_job_applicant_update(self):
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)
		create_staffing_plan()
		job_applicant = create_job_applicant(email_id="test_job_applicants@example.com")
		job_offer = create_job_offer(job_applicant=job_applicant.name)
		job_offer.submit()
		job_applicant.reload()
		self.assertEqual(job_applicant.status, "Accepted")

		# status update after rejection
		job_offer.status = "Rejected"
		job_offer.submit()
		job_applicant.reload()
		self.assertEqual(job_applicant.status, "Rejected")
		frappe.db.set_single_value("HR Settings", "check_vacancies", 1)

	def test_recruitment_metrics(self):
		job_applicant1 = create_job_applicant(email_id="test_job_applicant1@example.com")
		job_applicant2 = create_job_applicant(email_id="test_job_applicant2@example.com")
		job_offer = create_job_offer(job_applicant=job_applicant1.name)
		job_offer.status = "Accepted"
		job_offer.submit()

		self.assertEqual(get_applicant_to_hire_percentage().get("value"), 50)

		job_offer = create_job_offer(job_applicant=job_applicant2.name)
		job_offer.status = "Rejected"
		job_offer.submit()

		self.assertEqual(get_offer_acceptance_rate().get("value"), 50)


def create_job_offer(**args):
	args = frappe._dict(args)
	if not args.job_applicant:
		job_applicant = create_job_applicant()

	if not frappe.db.exists("Designation", args.designation):
		create_designation(designation_name=args.designation)

	job_offer = frappe.get_doc(
		{
			"doctype": "Job Offer",
			"job_applicant": args.job_applicant or job_applicant.name,
			"offer_date": args.offer_date or nowdate(),
			"designation": args.designation or "Researcher",
			"status": args.status or "Accepted",
		}
	)
	return job_offer


def create_staffing_plan(**args):
	args = frappe._dict(args)
	make_company()
	frappe.db.set_value("Company", "_Test Company", "is_group", 1)
	if frappe.db.exists("Staffing Plan", args.name or "Test"):
		return
	staffing_plan = frappe.get_doc(
		{
			"doctype": "Staffing Plan",
			"name": args.name or "Test",
			"from_date": args.from_date or nowdate(),
			"to_date": args.to_date or add_days(nowdate(), 10),
			"staffing_details": args.staffing_details
			or [{"designation": "Researcher", "vacancies": 1, "estimated_cost_per_position": 50000}],
		}
	)
	staffing_plan.insert()
	staffing_plan.submit()
	return staffing_plan
