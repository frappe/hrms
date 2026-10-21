import frappe
from frappe.core.doctype.user_permission.test_user_permission import create_user
from frappe.permissions import add_user_permission
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.designation.test_designation import create_designation

from hrms.hr.report.recruitment_analytics.recruitment_analytics import (
	get_job_offer,
	get_staffing_plan,
)
from hrms.tests.test_utils import create_job_applicant
from hrms.tests.utils import HRMSTestSuite


class TestRecruitmentAnalytics(HRMSTestSuite):
	def setUp(self):
		self.from_date = add_days(getdate(), 5)
		self.to_date = add_days(getdate(), 15)
		self.submitted = make_plan("_Test RA Submitted", self.from_date, self.to_date, submit=True)
		self.draft = make_plan("_Test RA Draft", self.from_date, self.to_date, submit=False)

	def get_plans(self, on_date):
		filters = frappe._dict(company="_Test Company", on_date=on_date)
		return [d.name for d in get_staffing_plan(filters)]

	def test_staffing_plans_by_date_and_docstatus(self):
		self.assertNotIn(self.submitted.name, self.get_plans(add_days(self.from_date, -1)))
		self.assertIn(self.submitted.name, self.get_plans(self.from_date))
		self.assertIn(self.submitted.name, self.get_plans(self.to_date))
		self.assertNotIn(self.draft.name, self.get_plans(self.from_date))

	def test_company_user_permission_applied(self):
		user = "test_recruitment_analytics@example.com"
		create_user(user, "HR User")
		add_user_permission("Company", "_Test Company 1", user)

		frappe.set_user(user)
		try:
			self.assertNotIn(self.submitted.name, self.get_plans(self.from_date))
		finally:
			frappe.set_user("Administrator")

	def test_latest_live_job_offer_reported(self):
		applicant = create_job_applicant().name
		old = make_offer(applicant, add_days(getdate(), -2), "Rejected", docstatus=1)
		live = make_offer(applicant, add_days(getdate(), -1), "Awaiting Response", docstatus=0)
		cancelled = make_offer(applicant, getdate(), "Accepted", docstatus=2)

		offers = get_job_offer([applicant], frappe._dict(company="_Test Company"))[applicant]
		self.assertEqual(offers[0].name, live)
		self.assertNotIn(cancelled, [d.name for d in offers])
		self.assertIn(old, [d.name for d in offers])


def make_plan(designation, from_date, to_date, submit):
	designation = create_designation(designation_name=designation).name
	plan = frappe.get_doc(
		{
			"doctype": "Staffing Plan",
			"__newname": f"{designation}-{submit}",
			"company": "_Test Company",
			"from_date": from_date,
			"to_date": to_date,
			"staffing_details": [{"designation": designation, "vacancies": 2}],
		}
	).insert()
	if submit:
		plan.submit()
	return plan


def make_offer(job_applicant, offer_date, status, docstatus):
	offer = frappe.get_doc(
		{
			"doctype": "Job Offer",
			"job_applicant": job_applicant,
			"offer_date": offer_date,
			"designation": create_designation().name,
			"status": status,
			"company": "_Test Company",
			"docstatus": docstatus,
		}
	)
	offer.set_new_name()
	offer.db_insert()
	return offer.name
