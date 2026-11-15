import frappe
from frappe.core.doctype.user_permission.test_user_permission import create_user
from frappe.permissions import add_user_permission
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, nowdate

from hrms.hr.doctype.job_applicant.job_applicant import update_stage
from hrms.hr.page.recruitment_dashboard.recruitment_dashboard import (
	RecruitmentDashboard,
	get_recruitment_dashboard,
)
from hrms.tests.test_utils import create_company

HR_USER = "recruitment.dashboard.hr@example.com"
NO_ROLE_USER = "recruitment.dashboard.norole@example.com"
RECRUITMENT_DOCTYPES = ("Interview", "Job Offer", "Employee Referral", "Job Applicant", "Job Opening")


class TestRecruitmentDashboard(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)
		self.addCleanup(frappe.set_user, "Administrator")
		frappe.flags.mute_emails = True
		for doctype in RECRUITMENT_DOCTYPES:
			frappe.db.delete(doctype)
		self.company = frappe.get_all("Company", pluck="name", order_by="creation asc", limit=1)[0]
		if not frappe.db.exists("Designation", "Researcher"):
			frappe.get_doc({"doctype": "Designation", "designation_name": "Researcher"}).insert()

	def test_empty_site_is_first_use(self):
		data = RecruitmentDashboard("last_90_days").get_data()

		self.assertTrue(data["first_use"])
		self.assertEqual(data["applications"], 0)
		self.assertIsNone(data["time_to_hire"])
		self.assertIsNone(data["applications_delta"])
		self.assertEqual(data["openings"], {"rows": [], "total": 0, "attention": []})
		self.assertEqual([row["count"] for row in data["funnel"]], [0, 0, 0, 0, 0])

	def test_period_counts_applicants_created_in_it(self):
		opening = self.make_opening("Dashboard Opening")
		self.make_applicant("recent", opening)
		self.make_applicant("older", opening, days_ago=45)
		self.make_applicant("previous", opening, days_ago=100)

		last_30 = RecruitmentDashboard("last_30_days").get_data()
		last_90 = RecruitmentDashboard("last_90_days").get_data()

		self.assertFalse(last_30["first_use"])
		self.assertEqual(last_30["applications"], 1)
		self.assertEqual(last_90["applications"], 2)
		# one in the 90 days before is too few to compare against
		self.assertIsNone(last_90["applications_delta"])
		self.assertEqual(last_90["openings"]["rows"][0]["Applied"], 2)

	def test_comparison_needs_ten_previous_records(self):
		opening = self.make_opening("Dashboard Opening")
		self.make_applicant("recent", opening)
		self.make_applicant("also-recent", opening)
		for index in range(10):
			self.make_applicant(f"previous-{index}", opening, days_ago=100)

		# two now against ten in the 90 days before
		self.assertEqual(RecruitmentDashboard("last_90_days").get_data()["applications_delta"], -80)

	def test_funnel_counts_stages_reached_from_records(self):
		opening = self.make_opening("Dashboard Opening")
		self.make_applicant("waiting", opening)
		rejected = self.make_applicant("rejected", opening)
		self.make_interview(rejected)
		frappe.db.set_value("Job Applicant", rejected, {"status": "Rejected", "stage": "Rejected"})
		offered = self.make_applicant("offered", opening)
		self.make_offer(offered, "Awaiting Response")

		funnel = {
			row["stage"]: row["count"] for row in RecruitmentDashboard("last_90_days").get_data()["funnel"]
		}

		self.assertEqual(
			funnel, {"Applied": 3, "Shortlisted": 2, "Interviewing": 2, "Offered": 1, "Hired": 0}
		)

	def test_funnel_never_widens(self):
		opening = self.make_opening("Dashboard Opening")
		hired = self.make_applicant("hired", opening)
		frappe.db.set_value("Job Applicant", hired, {"status": "Accepted", "stage": "Hired"})
		offered = self.make_applicant("offered", opening)
		self.make_offer(offered, "Accepted")

		counts = [row["count"] for row in RecruitmentDashboard("last_90_days").get_data()["funnel"]]

		self.assertEqual(counts, [2, 2, 2, 2, 1])

	def test_draft_offers_stay_out_of_funnel(self):
		opening = self.make_opening("Dashboard Opening")
		drafted = self.make_applicant("drafted", opening)
		self.make_interview(drafted)
		self.make_offer(drafted, "Draft")
		sent = self.make_applicant("sent", opening)
		self.make_offer(sent, "Awaiting Response")

		funnel = {
			row["stage"]: row["count"] for row in RecruitmentDashboard("last_90_days").get_data()["funnel"]
		}

		self.assertEqual(funnel["Interviewing"], 2)
		self.assertEqual(funnel["Offered"], 1)

	def test_cancelled_interviews_are_not_interviewed(self):
		opening = self.make_opening("Dashboard Opening")
		cancelled = self.make_applicant("cancelled", opening)
		interview = self.make_interview(cancelled)
		frappe.db.set_value("Interview", interview, "status", "Cancelled")

		data = RecruitmentDashboard("last_90_days").get_data()

		funnel = {row["stage"]: row["count"] for row in data["funnel"]}
		self.assertEqual(funnel["Interviewing"], 0)
		self.assertEqual(data["sources"][0]["Interviewed"], 0)

	def test_offers_made_count_by_offer_date(self):
		opening = self.make_opening("Dashboard Opening")
		# applied long before the period, offered in it
		early = self.make_applicant("early", opening, days_ago=200)
		self.make_offer(early, "Awaiting Response", docstatus=1)
		declined = self.make_applicant("declined", opening)
		self.make_offer(declined, "Rejected", docstatus=1)
		older = self.make_applicant("older", opening)
		self.make_offer(older, "Accepted", docstatus=1, offer_date=add_days(nowdate(), -40))
		drafted = self.make_applicant("drafted", opening)
		self.make_offer(drafted, "Awaiting Response")

		offers = {
			row["status"]: row["count"] for row in RecruitmentDashboard("last_30_days").get_data()["offers"]
		}

		self.assertEqual(offers, {"Accepted": 0, "Rejected": 1, "Awaiting Response": 1})

	def test_interviews_held_count_by_scheduled_on(self):
		opening = self.make_opening("Dashboard Opening")
		early = self.make_applicant("early", opening, days_ago=200)
		self.make_interview(early)
		self.make_interview(early, scheduled_on=add_days(nowdate(), -40))
		cancelled = self.make_interview(early)
		frappe.db.set_value("Interview", cancelled, {"docstatus": 2, "status": "Cancelled"})

		interviews = RecruitmentDashboard("last_30_days").get_data()["interviews"]

		self.assertEqual({row["status"]: row["count"] for row in interviews if row["count"]}, {"Pending": 1})

	def test_time_to_hire_skips_backdated_offers(self):
		opening = self.make_opening("Dashboard Opening")
		hired = self.make_applicant("hired", opening, days_ago=10)
		self.make_offer(hired, "Accepted", docstatus=1, offer_date=add_days(nowdate(), -4))
		backdated = self.make_applicant("backdated", opening, days_ago=2)
		self.make_offer(backdated, "Accepted", docstatus=1, offer_date=add_days(nowdate(), -30))

		data = RecruitmentDashboard("last_90_days").get_data()

		self.assertEqual(data["hired"], 2)
		self.assertEqual(data["time_to_hire"], {"days": 6, "hires": 1})

	def test_attention_lists_late_and_empty_openings(self):
		self.make_opening(
			"Late Opening", posted_on=add_days(nowdate(), -40), closes_on=add_days(nowdate(), -3)
		)
		self.make_opening("Empty Opening")
		busy = self.make_opening("Busy Opening")
		self.make_applicant("busy", busy)

		attention = RecruitmentDashboard("last_90_days").get_data()["openings"]["attention"]

		self.assertEqual([row["title"] for row in attention], ["Late Opening", "Empty Opening"])
		self.assertEqual(attention[0]["days"], 3)

	def test_needs_read_on_job_applicant(self):
		create_user(HR_USER, "HR User")
		if not frappe.db.exists("User", NO_ROLE_USER):
			frappe.get_doc({"doctype": "User", "email": NO_ROLE_USER, "first_name": "Norole"}).insert()

		frappe.set_user(NO_ROLE_USER)
		self.assertRaises(frappe.PermissionError, get_recruitment_dashboard)

		frappe.set_user(HR_USER)
		self.assertTrue(get_recruitment_dashboard()["first_use"])

	def test_counts_respect_company_user_permission(self):
		other_company = create_company("Test Recruitment Dashboard Other").name
		create_user(HR_USER, "HR User")
		add_user_permission("Company", self.company, HR_USER)
		own = self.make_opening("Own Opening")
		other = self.make_opening("Other Opening", company=other_company)
		self.make_offer(self.make_applicant("own", own), "Accepted", docstatus=1)
		self.make_offer(self.make_applicant("other", other), "Accepted", docstatus=1, company=other_company)

		frappe.set_user(HR_USER)
		data = get_recruitment_dashboard()

		self.assertEqual(data["open_roles"], 1)
		self.assertEqual([row["role"] for row in data["openings"]["rows"]], ["Own Opening"])
		self.assertEqual({row["status"]: row["count"] for row in data["offers"]}["Accepted"], 1)

	def make_opening(self, title, **kwargs):
		return frappe.get_doc(
			{
				"doctype": "Job Opening",
				"job_title": title,
				"designation": "Researcher",
				"company": self.company,
				"status": "Open",
				"vacancies": 1,
				**kwargs,
			}
		).insert(ignore_permissions=True)

	def make_applicant(self, label, opening, days_ago=0):
		applicant = frappe.get_doc(
			{
				"doctype": "Job Applicant",
				"applicant_name": label.title(),
				"email_id": f"recruitment-dashboard-{label}@example.com",
				"job_title": opening.name,
			}
		).insert(ignore_permissions=True)
		if days_ago:
			frappe.db.set_value(
				"Job Applicant",
				applicant.name,
				"creation",
				add_days(nowdate(), -days_ago),
				update_modified=False,
			)
		return applicant.name

	def make_interview(self, applicant, scheduled_on=None):
		interview = frappe.get_doc(
			{
				"doctype": "Interview",
				"job_applicant": applicant,
				"scheduled_on": scheduled_on or nowdate(),
				"from_time": "10:00:00",
				"to_time": "11:00:00",
				"status": "Pending",
			}
		)
		interview.flags.ignore_validate = True
		interview.insert(ignore_permissions=True, ignore_mandatory=True)
		return interview.name

	def make_offer(self, applicant, status, docstatus=0, **kwargs):
		offer = frappe.get_doc(
			{
				"doctype": "Job Offer",
				"job_applicant": applicant,
				"applicant_name": applicant,
				"status": status,
				"offer_date": nowdate(),
				"designation": "Researcher",
				"company": self.company,
				**kwargs,
			}
		)
		offer.set_new_name()
		offer.set_user_and_timestamp()
		offer.docstatus = docstatus
		offer.db_insert()
		update_stage(applicant)
		return offer.name
