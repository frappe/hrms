import frappe
from frappe.core.doctype.user_permission.test_user_permission import create_user
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, get_datetime, now_datetime, nowdate

from hrms.hr.doctype.job_applicant.job_applicant import get_stage, update_stage
from hrms.hr.page.hiring import applicant as applicant_api
from hrms.hr.page.hiring import hiring

HR_USER = "hiring.hr@example.com"
NO_ROLE_USER = "hiring.norole@example.com"
INTERVIEWER = "hiring.interviewer@example.com"


class TestHiring(IntegrationTestCase):
	def setUp(self):
		self.addCleanup(frappe.db.rollback)
		create_user(HR_USER, "HR User")
		create_user(INTERVIEWER, "Interviewer")
		if not frappe.db.exists("User", NO_ROLE_USER):
			frappe.get_doc({"doctype": "User", "email": NO_ROLE_USER, "first_name": "Norole"}).insert()
		self.company = frappe.get_all("Company", pluck="name", limit=1)[0]
		if not frappe.db.exists("Designation", "Researcher"):
			frappe.get_doc({"doctype": "Designation", "designation_name": "Researcher"}).insert()
		self.opening = self.make_opening("Hiring Test Opening")
		frappe.set_user(HR_USER)
		self.addCleanup(frappe.set_user, "Administrator")

	def make_opening(self, title, status="Open", **kwargs):
		opening = frappe.get_doc(
			{
				"doctype": "Job Opening",
				"job_title": title,
				"designation": "Researcher",
				"company": self.company,
				"status": status,
				"vacancies": 2,
				**kwargs,
			}
		)
		opening.insert(ignore_permissions=True)
		return opening

	def make_applicant(self, label, status="Open", opening=None, **kwargs):
		applicant = frappe.get_doc(
			{
				"doctype": "Job Applicant",
				"applicant_name": label.title(),
				"email_id": f"hiring-{label}@example.com",
				"status": status,
				"job_title": (opening or self.opening).name,
				"designation": "Researcher",
				**kwargs,
			}
		)
		applicant.insert(ignore_permissions=True)
		return applicant.name

	def make_employee(self, label, applicant):
		employee = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": label,
				"company": self.company,
				"gender": frappe.get_all("Gender", pluck="name", limit=1)[0],
				"date_of_birth": "1990-05-08",
				"date_of_joining": "2013-01-01",
				"status": "Active",
				"job_applicant": applicant,
			}
		)
		employee.insert(ignore_permissions=True)
		return employee.name

	def make_offer(self, applicant, status="Awaiting Response", docstatus=0, **kwargs):
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

	def make_onboarding(self, applicant, docstatus=0):
		onboarding = frappe.get_doc(
			{
				"doctype": "Employee Onboarding",
				"job_applicant": applicant,
				"company": self.company,
				"date_of_joining": nowdate(),
				"boarding_status": "Pending",
			}
		)
		onboarding.set_new_name()
		onboarding.set_user_and_timestamp()
		onboarding.docstatus = docstatus
		onboarding.db_insert()
		return onboarding.name

	def make_interview(
		self, applicant, status="Pending", days_ago=0, docstatus=0, panel=(), feedback_from=()
	):
		interview = frappe.get_doc(
			{
				"doctype": "Interview",
				"job_applicant": applicant,
				"scheduled_on": add_days(nowdate(), -days_ago),
				"from_time": "10:00:00",
				"to_time": "11:00:00",
				"status": status,
				"interview_details": [{"interviewer": user} for user in panel],
			}
		)
		interview.flags.ignore_validate = True
		interview.insert(ignore_permissions=True, ignore_mandatory=True)
		self.write("Interview", interview.name, {"docstatus": docstatus, "status": status})
		for user in feedback_from:
			self.make_feedback(interview.name, applicant, user)
		return interview.name

	def make_saveable_interview(self, applicant, interview_type="Hiring Test Round", **kwargs):
		"""An interview that passes mandatory checks, for tests that save or submit it."""
		if not frappe.db.exists("Interview Type", interview_type):
			frappe.get_doc({"doctype": "Interview Type", "interview_type_name": interview_type}).insert(
				ignore_permissions=True, ignore_mandatory=True
			)
		kwargs.setdefault("panel", ("Administrator",))
		interview = self.make_interview(applicant, **kwargs)
		frappe.db.set_value("Interview", interview, "interview_type", interview_type)
		return interview

	def make_feedback(self, interview, applicant, user):
		feedback = frappe.get_doc(
			{
				"doctype": "Interview Feedback",
				"interview": interview,
				"job_applicant": applicant,
				"interviewer": user,
			}
		)
		feedback.flags.ignore_validate = True
		feedback.insert(ignore_permissions=True, ignore_mandatory=True)
		frappe.db.set_value("Interview Feedback", feedback.name, "docstatus", 1)

	def write(self, doctype, name, values):
		"""A raw write like the fixtures make, then the stored stage the hooks would have refreshed."""
		frappe.db.set_value(doctype, name, values)
		update_stage(
			name if doctype == "Job Applicant" else frappe.db.get_value(doctype, name, "job_applicant")
		)

	def get_stage(self, applicant):
		return hiring.get_applicant_stage(applicant)

	def test_applied_includes_replied_and_hold(self):
		open_ = self.make_applicant("open")
		replied = self.make_applicant("replied", status="Replied")
		hold = self.make_applicant("hold", status="Hold")

		self.assertEqual(self.get_stage(open_)["stage"], "applied")
		self.assertEqual(self.get_stage(replied)["stage"], "applied")
		self.assertEqual(self.get_stage(hold)["stage"], "applied")

		stages = self.get_stages(open_, hold)
		self.assertFalse(stages[open_]["on_hold"])
		self.assertTrue(stages[hold]["on_hold"])

	def get_stages(self, *names):
		applicants = frappe.get_list(
			"Job Applicant", filters={"name": ["in", names]}, fields=hiring.APPLICANT_FIELDS
		)
		return hiring.get_applicant_stages(applicants)

	def test_hold_keeps_the_shortlisted_stage(self):
		shortlisted = self.make_applicant("short", status="Shortlisted")
		self.assertEqual(self.get_stage(shortlisted)["stage"], "shortlisted")

		self.write("Job Applicant", shortlisted, {"status": "Hold"})
		self.assertEqual(self.get_stage(shortlisted)["stage"], "shortlisted")
		self.assertTrue(self.get_stages(shortlisted)[shortlisted]["on_hold"])

	def test_legacy_accepted_without_offer_is_shortlisted(self):
		applicant = self.make_applicant("legacy", status="Accepted")
		result = self.get_stage(applicant)
		self.assertEqual(result["stage"], "shortlisted")
		self.assertEqual(result["fact"], "Ready for offer")

	def test_rejected_wins_over_everything(self):
		applicant = self.make_applicant("rejected", status="Rejected")
		self.make_interview(applicant)
		self.make_offer(applicant, docstatus=1)
		self.assertEqual(self.get_stage(applicant)["stage"], "rejected")

	def test_interviewing_with_feedback_progress(self):
		applicant = self.make_applicant("interview", status="Shortlisted")
		panel = [INTERVIEWER, HR_USER]
		self.make_interview(
			applicant, status="Under Review", days_ago=1, panel=panel, feedback_from=[INTERVIEWER]
		)

		result = self.get_stage(applicant)
		self.assertEqual(result["stage"], "interviewing")
		self.assertTrue(result["fact"].endswith("Feedback 1 of 2"))

	def test_interview_in_future_has_no_feedback_count(self):
		applicant = self.make_applicant("future")
		self.make_interview(applicant, days_ago=-3, panel=[INTERVIEWER])
		self.assertNotIn("Feedback", self.get_stage(applicant)["fact"])

	def test_cleared_interview_can_make_offer_until_offer_exists(self):
		applicant = self.make_applicant("cleared", status="Shortlisted")
		self.make_interview(applicant, status="Cleared", days_ago=1, docstatus=1, panel=[INTERVIEWER])

		result = self.get_stage(applicant)
		self.assertEqual(result["stage"], "interviewing")
		self.assertTrue(result["fact"].endswith("Cleared"))
		self.assertTrue(self.get_stages(applicant)[applicant]["can_make_offer"])

		self.make_offer(applicant)
		self.assertEqual(self.get_stage(applicant)["stage"], "offered")
		self.assertFalse(self.get_stages(applicant)[applicant]["can_make_offer"])

	def test_cancelled_interview_drops_applicant_back(self):
		applicant = self.make_applicant("dropback", status="Shortlisted")
		interview = self.make_interview(applicant)
		self.assertEqual(self.get_stage(applicant)["stage"], "interviewing")

		self.write("Interview", interview, {"status": "Cancelled", "docstatus": 2})
		self.assertEqual(self.get_stage(applicant)["stage"], "shortlisted")

		other = self.make_applicant("dropback-two")
		interview = self.make_interview(other)
		self.write("Interview", interview, {"status": "Cancelled"})
		self.assertEqual(self.get_stage(other)["stage"], "applied")

	def test_latest_interview_decides_the_fact(self):
		applicant = self.make_applicant("rounds", status="Shortlisted")
		self.make_interview(applicant, status="Cleared", days_ago=5, docstatus=1)
		self.make_interview(applicant, status="Pending", days_ago=-2)
		self.assertNotIn("Cleared", self.get_stage(applicant)["fact"])
		self.assertFalse(self.get_stages(applicant)[applicant]["can_make_offer"])

	def test_offered_draft_and_sent(self):
		applicant = self.make_applicant("offered")
		offer = self.make_offer(applicant)
		result = self.get_stage(applicant)
		self.assertEqual(result["stage"], "offered")
		self.assertEqual(result["fact"], "Offer in draft")

		self.write("Job Offer", offer, {"docstatus": 1, "status": "Ready to Send"})
		self.assertEqual(self.get_stage(applicant)["fact"], "Offer ready to send")

		self.write("Job Offer", offer, {"status": "Awaiting Response"})
		self.assertTrue(self.get_stage(applicant)["fact"].startswith("Offer sent"))

		self.write("Job Offer", offer, {"docstatus": 2})
		self.assertEqual(self.get_stage(applicant)["stage"], "applied")

	def test_draft_status_offer_is_offered_like_the_applicants_own_stage(self):
		applicant = self.make_applicant("draft-status", status="Shortlisted")
		self.make_interview(applicant, status="Pending", days_ago=1)
		self.make_offer(applicant, status="Draft")
		self.assertEqual(self.get_stage(applicant)["stage"], "offered")
		self.assertEqual(get_stage(applicant), "Offered")

	def test_hired_by_accepted_submitted_offer(self):
		applicant = self.make_applicant("hired", status="Accepted")
		offer = self.make_offer(applicant, status="Accepted")
		self.assertEqual(self.get_stage(applicant)["stage"], "shortlisted")

		self.write("Job Offer", offer, {"docstatus": 1})
		self.assertEqual(self.get_stage(applicant)["stage"], "hired")

	def test_hired_by_employee(self):
		applicant = self.make_applicant("employee", status="Shortlisted")
		self.make_employee("Hired", applicant)
		self.assertEqual(self.get_stage(applicant)["stage"], "hired")

	def test_referred_by_fact(self):
		referrer = self.make_employee("Referrer", None)
		applicant = self.make_applicant("referred", source_name=referrer)
		referrer_name = frappe.db.get_value("Employee", referrer, "employee_name")
		self.assertEqual(self.get_stage(applicant)["fact"], f"Referred by {referrer_name}")

		if not frappe.db.exists("Job Applicant Source", "LinkedIn"):
			frappe.get_doc({"doctype": "Job Applicant Source", "source_name": "LinkedIn"}).insert()
		plain = self.make_applicant("plain", source="LinkedIn")
		self.assertEqual(self.get_stage(plain)["fact"], "LinkedIn")

	def test_pipeline_counts_rows_and_search(self):
		self.make_applicant("alpha")
		self.make_applicant("beta")
		self.make_applicant("gamma", status="Rejected")
		self.make_applicant("delta", status="Shortlisted")
		self.make_offer(self.make_applicant("epsilon"))

		result = hiring.get_pipeline(self.opening.name)
		self.assertEqual(
			result["counts"],
			{"applied": 2, "shortlisted": 1, "interviewing": 0, "offered": 1, "hired": 0, "rejected": 1},
		)
		self.assertEqual(result["total"], 2)
		self.assertEqual({row["applicant_name"] for row in result["rows"]}, {"Alpha", "Beta"})
		self.assertEqual(result["opening"]["name"], self.opening.name)
		self.assertEqual(result["opening"]["designation"], "Researcher")

		searched = hiring.get_pipeline(self.opening.name, search="ALP")
		self.assertEqual([row["applicant_name"] for row in searched["rows"]], ["Alpha"])
		self.assertEqual(searched["total"], 1)
		self.assertEqual(searched["counts"]["applied"], 2)

		by_email = hiring.get_pipeline(self.opening.name, search="hiring-beta@")
		self.assertEqual([row["applicant_name"] for row in by_email["rows"]], ["Beta"])

		rejected = hiring.get_pipeline(self.opening.name, stage="rejected")
		self.assertEqual([row["applicant_name"] for row in rejected["rows"]], ["Gamma"])

	def test_stored_stage_matches_the_stage_rules(self):
		applicants = [
			self.make_applicant("parity-open"),
			self.make_applicant("parity-hold", status="Hold"),
			self.make_applicant("parity-accepted", status="Accepted"),
			self.make_applicant("parity-rejected", status="Rejected"),
		]
		interviewing = self.make_applicant("parity-interview", status="Shortlisted")
		self.make_interview(interviewing, status="Cleared", docstatus=1)
		offered = self.make_applicant("parity-offer")
		self.make_offer(offered, status="Draft")
		accepted = self.make_applicant("parity-hired")
		self.make_offer(accepted, status="Accepted", docstatus=1)
		employed = self.make_applicant("parity-employee", status="Shortlisted")
		self.make_employee("Parity", employed)
		applicants += [interviewing, offered, accepted, employed]

		for name, info in self.get_stages(*applicants).items():
			self.assertEqual(info["stage"], get_stage(name).lower(), name)
		self.assertEqual([info["stage"] for info in self.get_stages(*applicants).values()].count("hired"), 2)

	def test_pipeline_search_is_literal_text(self):
		self.make_applicant("percent")
		self.assertEqual(hiring.get_pipeline(self.opening.name, "applied", search="%")["total"], 0)
		self.assertEqual(hiring.get_pipeline(self.opening.name, "applied", search="PERC")["total"], 1)

	def test_pipeline_paging(self):
		for index in range(5):
			self.make_applicant(f"page{index}")

		first = hiring.get_pipeline(self.opening.name, page_length=3)
		second = hiring.get_pipeline(self.opening.name, start=3, page_length=3)
		self.assertEqual((first["total"], len(first["rows"]), len(second["rows"])), (5, 3, 2))
		names = [row["name"] for row in first["rows"] + second["rows"]]
		self.assertEqual(len(set(names)), 5)

	def test_pipeline_sorts_by_creation_and_rating(self):
		old = self.make_applicant("old", applicant_rating=0.2)
		mid = self.make_applicant("mid", applicant_rating=0.8)
		new = self.make_applicant("new", applicant_rating=0.4)
		for name, days in ((old, 3), (mid, 2), (new, 1)):
			frappe.db.set_value("Job Applicant", name, "creation", add_days(nowdate(), -days))

		def names(sort):
			return [row["name"] for row in hiring.get_pipeline(self.opening.name, sort=sort)["rows"]]

		self.assertEqual(names("newest"), [new, mid, old])
		self.assertEqual(names("oldest"), [old, mid, new])
		self.assertEqual(names("rating"), [mid, new, old])
		self.assertRaises(frappe.ValidationError, hiring.get_pipeline, self.opening.name, sort="name; drop")

	def test_pipeline_filters_by_source_and_lists_sources(self):
		for source in ("LinkedIn", "Careers page"):
			if not frappe.db.exists("Job Applicant Source", source):
				frappe.get_doc({"doctype": "Job Applicant Source", "source_name": source}).insert()
		linkedin = self.make_applicant("li-one", source="LinkedIn")
		self.make_applicant("li-two", source="LinkedIn")
		self.make_applicant("careers", source="Careers page")
		self.make_applicant("no-source")
		self.make_applicant("rejected-li", status="Rejected", source="LinkedIn")

		result = hiring.get_pipeline(self.opening.name)
		self.assertEqual(
			result["sources"],
			[{"source": "Careers page", "count": 1}, {"source": "LinkedIn", "count": 2}],
		)
		self.assertEqual(result["total"], 4)

		filtered = hiring.get_pipeline(self.opening.name, source="LinkedIn")
		self.assertEqual(filtered["total"], 2)
		self.assertIn(linkedin, [row["name"] for row in filtered["rows"]])
		self.assertEqual(filtered["counts"]["applied"], 4)
		self.assertEqual(len(filtered["sources"]), 2)

	def test_interviewing_pipeline_groups_by_what_happens_next(self):
		scheduled = self.make_applicant("scheduled")
		self.make_interview(scheduled, days_ago=-3, panel=[INTERVIEWER])
		cleared = self.make_applicant("cleared-one")
		self.make_interview(cleared, status="Cleared", days_ago=1, docstatus=1, panel=[INTERVIEWER])
		no_panel = self.make_applicant("no-panel")
		self.make_interview(no_panel, days_ago=-1)
		due = self.make_applicant("due")
		self.make_interview(due, days_ago=1, panel=[INTERVIEWER, HR_USER], feedback_from=[INTERVIEWER])
		feedback_in = self.make_applicant("feedback-in")
		self.make_interview(feedback_in, days_ago=1, panel=[INTERVIEWER], feedback_from=[INTERVIEWER])
		not_cleared = self.make_applicant("not-cleared")
		self.make_interview(not_cleared, status="Rejected", days_ago=1, docstatus=1, panel=[INTERVIEWER])
		self.make_applicant("still-applied")
		for name, days in ((scheduled, 6), (cleared, 5), (no_panel, 4), (due, 3), (feedback_in, 2)):
			frappe.db.set_value("Job Applicant", name, "creation", add_days(nowdate(), -days))

		result = hiring.get_pipeline(self.opening.name, stage="interviewing", sort="oldest")
		self.assertEqual(
			[(row["name"], row["group"]) for row in result["rows"]],
			[
				(cleared, "cleared"),
				(feedback_in, "feedback_in"),
				(not_cleared, "not_cleared"),
				(due, "feedback_due"),
				(no_panel, "no_panel"),
				(scheduled, "scheduled"),
			],
		)
		self.assertEqual(
			result["groups"],
			[
				{"group": "cleared", "label": "Cleared", "count": 1},
				{"group": "feedback_in", "label": "Feedback in", "count": 1},
				{"group": "not_cleared", "label": "Not cleared", "count": 1},
				{"group": "feedback_due", "label": "Feedback due", "count": 1},
				{"group": "no_panel", "label": "No interviewers", "count": 1},
				{"group": "scheduled", "label": "Scheduled", "count": 1},
			],
		)

		# The header carries the state; rows only add progress the header can't show.
		facts = {row["name"]: row["group_fact"] for row in result["rows"]}
		self.assertNotIn("Cleared", facts[cleared])
		self.assertTrue(facts[due].endswith("1 of 2 in"))
		self.assertNotIn("of", facts[feedback_in].split(" · ")[-1])

	def test_interviewing_pipeline_keeps_sort_within_group_and_counts_all_pages(self):
		first = self.make_applicant("first")
		second = self.make_applicant("second")
		for name, days in ((first, 2), (second, 1)):
			self.make_interview(name, status="Cleared", days_ago=1, docstatus=1, panel=[INTERVIEWER])
			frappe.db.set_value("Job Applicant", name, "creation", add_days(nowdate(), -days))
		waiting = self.make_applicant("waiting")
		self.make_interview(waiting, days_ago=-1, panel=[INTERVIEWER])

		result = hiring.get_pipeline(self.opening.name, stage="interviewing", page_length=2)
		self.assertEqual([row["name"] for row in result["rows"]], [second, first])
		self.assertEqual(
			[(group["group"], group["count"]) for group in result["groups"]],
			[("cleared", 2), ("scheduled", 1)],
		)

	def test_interviewing_without_a_readable_interview_is_listed_and_opens(self):
		# the stage is stored, the interview may be one the user can't read
		hidden = self.make_applicant("hidden-interview")
		frappe.db.set_value("Job Applicant", hidden, "stage", "Interviewing")

		result = hiring.get_pipeline(self.opening.name, stage="interviewing")
		self.assertEqual(result["total"], 1)
		row = result["rows"][0]
		self.assertEqual((row["name"], row["group"], row["group_fact"]), (hidden, "scheduled", row["fact"]))
		self.assertEqual(result["groups"], [{"group": "scheduled", "label": "Scheduled", "count": 1}])

		detail = applicant_api.get_applicant(hidden)
		self.assertEqual(detail["stage"], "interviewing")
		self.assertIsNone(detail["current_interview"])
		self.assertTrue(detail["stage_since"])

	def test_other_stages_have_no_groups(self):
		self.make_applicant("plain")
		result = hiring.get_pipeline(self.opening.name)
		self.assertEqual(result["groups"], [])
		self.assertIsNone(result["rows"][0]["group"])

	def test_pipeline_rejects_unknown_stage(self):
		self.assertRaises(frappe.ValidationError, hiring.get_pipeline, self.opening.name, "nonsense")

	def test_applicant_panel_gets_the_interview_group_and_feedback_givers(self):
		booked = self.make_applicant("booked")
		self.make_interview(booked, days_ago=-1, panel=[INTERVIEWER, HR_USER])
		due = self.make_applicant("overdue")
		interview = self.make_interview(
			due, days_ago=1, panel=[INTERVIEWER, HR_USER], feedback_from=[INTERVIEWER]
		)

		self.assertEqual(applicant_api.get_applicant(booked)["interview_group"], "scheduled")
		result = applicant_api.get_applicant(due)
		self.assertEqual(result["interview_group"], "feedback_due")
		self.assertEqual(result["current_interview"], interview)
		self.assertEqual(result["interviews"][0]["feedback_from"], [INTERVIEWER])
		self.assertIsNone(applicant_api.get_applicant(self.make_applicant("plain-one"))["interview_group"])

	def test_user_without_hr_role_is_refused(self):
		applicant = self.make_applicant("secret")
		for user in (NO_ROLE_USER, INTERVIEWER):
			frappe.set_user(user)
			self.assertRaises(frappe.PermissionError, hiring.get_pipeline, self.opening.name)
			self.assertRaises(frappe.PermissionError, hiring.get_applicant_stage, applicant)

	def test_applicant_detail_fields_stage_and_empty_children(self):
		if not frappe.db.exists("Job Applicant Source", "LinkedIn"):
			frappe.get_doc({"doctype": "Job Applicant Source", "source_name": "LinkedIn"}).insert()
		applicant = self.make_applicant(
			"detail", status="Hold", source="LinkedIn", phone_number="9876543210", cover_letter="Hello"
		)

		result = applicant_api.get_applicant(applicant)
		self.assertEqual(result["name"], applicant)
		self.assertEqual(result["applicant_name"], "Detail")
		self.assertEqual((result["stage"], result["stage_label"]), ("applied", "Applied"))
		self.assertEqual(result["fact"], "LinkedIn")
		self.assertTrue(result["on_hold"])
		self.assertEqual(result["job_opening"], self.opening.name)
		self.assertEqual((result["designation"], result["phone_number"]), ("Researcher", "9876543210"))
		self.assertEqual(result["cover_letter"], "Hello")
		self.assertIsNone(result["referred_by"])
		self.assertEqual((result["interviews"], result["offer"], result["onboarding"]), ([], None, None))

	def test_applicant_detail_resume_requires_an_existing_file(self):
		applicant = self.make_applicant("resume-detail", resume_attachment="/files/resume-detail-missing.pdf")
		result = applicant_api.get_applicant(applicant)
		self.assertIsNone(result["resume_attachment"])
		self.assertTrue(result["resume_missing"])

		frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "resume-detail.txt",
				"content": b"resume",
				"is_private": 0,
			}
		).insert()
		file_url = frappe.db.get_value("File", {"file_name": "resume-detail.txt"}, "file_url")
		frappe.db.set_value("Job Applicant", applicant, "resume_attachment", file_url)
		result = applicant_api.get_applicant(applicant)
		self.assertEqual(result["resume_attachment"], file_url)
		self.assertEqual(result["resume_file_name"], "resume-detail.txt")
		self.assertTrue(result["resume_uploaded_on"])
		self.assertFalse(result["resume_missing"])

		frappe.db.set_value("Job Applicant", applicant, "resume_attachment", None)
		self.assertFalse(applicant_api.get_applicant(applicant)["resume_missing"])

	def test_applicant_detail_referrer(self):
		referrer = self.make_employee("Referrer", None)
		applicant = self.make_applicant("referred-detail", source_name=referrer)
		name = frappe.db.get_value("Employee", referrer, "employee_name")
		self.assertEqual(applicant_api.get_applicant(applicant)["referred_by"], name)

	def test_applicant_detail_interviews_newest_first_with_feedback_counts(self):
		applicant = self.make_applicant("rounds-detail", status="Shortlisted")
		first = self.make_interview(applicant, status="Cleared", days_ago=5, docstatus=1, panel=[INTERVIEWER])
		second = self.make_interview(
			applicant,
			status="Under Review",
			days_ago=1,
			panel=[INTERVIEWER, HR_USER],
			feedback_from=[HR_USER],
		)
		cancelled = self.make_interview(applicant, days_ago=3)
		self.write("Interview", cancelled, {"status": "Cancelled", "docstatus": 2})

		result = applicant_api.get_applicant(applicant)
		self.assertEqual(result["stage"], "interviewing")
		self.assertEqual([row["name"] for row in result["interviews"]], [second, first])
		self.assertEqual(result["interviews"][0]["status"], "Under Review")
		self.assertEqual(result["interviews"][0]["from_time"], "10:00:00")
		self.assertEqual(
			[(row["feedback_count"], row["interviewer_count"]) for row in result["interviews"]],
			[(1, 2), (0, 1)],
		)

	def test_applicant_detail_offer_and_onboarding(self):
		applicant = self.make_applicant("offer-detail", status="Accepted")
		offer = self.make_offer(applicant, status="Accepted", docstatus=1)

		result = applicant_api.get_applicant(applicant)
		self.assertEqual(result["stage"], "hired")
		self.assertEqual(result["offer"]["name"], offer)
		self.assertEqual(result["offer"]["status"], "Accepted")
		self.assertIsNone(result["onboarding"])

		onboarding = self.make_onboarding(applicant)
		self.assertEqual(applicant_api.get_applicant(applicant)["onboarding"], onboarding)

	def test_stage_data_exposes_the_onboarding(self):
		applicant = self.make_applicant("stage-onboarding", status="Accepted")
		self.make_offer(applicant, status="Accepted", docstatus=1)
		self.assertIsNone(self.get_stage(applicant)["onboarding"])

		onboarding = self.make_onboarding(applicant)
		self.assertEqual(self.get_stage(applicant)["onboarding"], onboarding)

	def test_applicant_detail_can_make_offer(self):
		applicant = self.make_applicant("cleared-detail", status="Shortlisted")
		self.make_interview(applicant, status="Cleared", days_ago=1, docstatus=1, panel=[INTERVIEWER])
		self.assertTrue(applicant_api.get_applicant(applicant)["can_make_offer"])

	def test_draft_cleared_interview_can_make_offer(self):
		applicant = self.make_applicant("cleared-draft", status="Shortlisted")
		self.make_interview(applicant, status="Cleared", days_ago=1, docstatus=0, panel=[INTERVIEWER])
		self.assertTrue(self.get_stages(applicant)[applicant]["can_make_offer"])
		self.assertTrue(applicant_api.get_applicant(applicant)["can_make_offer"])

	def test_applicant_detail_interview_average_rating_and_panel(self):
		applicant = self.make_applicant("rating-detail", status="Shortlisted")
		interview = self.make_interview(
			applicant,
			status="Under Review",
			days_ago=1,
			panel=[INTERVIEWER, HR_USER],
			feedback_from=[INTERVIEWER, HR_USER],
		)
		quiet = self.make_applicant("rating-quiet", status="Shortlisted")
		self.make_interview(quiet, days_ago=1, panel=[INTERVIEWER])
		for user, rating in ((INTERVIEWER, 0.8), (HR_USER, 0.6)):
			frappe.db.set_value(
				"Interview Feedback",
				{"interview": interview, "interviewer": user},
				{"average_rating": rating, "result": "Cleared"},
			)

		row = applicant_api.get_applicant(applicant)["interviews"][0]
		self.assertEqual(row["average_rating"], 3.5)
		self.assertEqual(row["docstatus"], 0)
		self.assertEqual(
			sorted((member["user"], member["result"], member["rating"]) for member in row["panel"]),
			sorted([(INTERVIEWER, "Cleared", 4.0), (HR_USER, "Cleared", 3.0)]),
		)

		silent = applicant_api.get_applicant(quiet)["interviews"][0]
		self.assertIsNone(silent["average_rating"])
		self.assertEqual(
			[(member["user"], member["result"], member["rating"]) for member in silent["panel"]],
			[(INTERVIEWER, None, None)],
		)

	def test_set_interview_result_saves_the_draft_and_undoes(self):
		applicant = self.make_applicant("decide", status="Shortlisted")
		interview = self.make_saveable_interview(
			applicant, status="Under Review", days_ago=1, panel=[INTERVIEWER]
		)

		result = applicant_api.set_interview_result(interview, "Cleared")
		self.assertEqual(result["previous_status"], "Under Review")
		self.assertEqual(frappe.db.get_value("Interview", interview, ["status", "docstatus"]), ("Cleared", 0))
		self.assertTrue(self.get_stages(applicant)[applicant]["can_make_offer"])

		applicant_api.set_interview_result(interview, result["previous_status"])
		self.assertFalse(self.get_stages(applicant)[applicant]["can_make_offer"])
		self.assertEqual(
			frappe.db.get_value("Interview", interview, ["status", "docstatus"]), ("Under Review", 0)
		)

	def test_set_interview_result_switches_a_submitted_result_but_never_back_to_undecided(self):
		applicant = self.make_applicant("decided", status="Shortlisted")
		submitted = self.make_saveable_interview(applicant, status="Cleared", days_ago=1, docstatus=1)

		result = applicant_api.set_interview_result(submitted, "Rejected")
		self.assertEqual(result["previous_status"], "Cleared")
		self.assertEqual(
			frappe.db.get_value("Interview", submitted, ["status", "docstatus"]), ("Rejected", 1)
		)
		for status in ("Pending", "Under Review", "Cancelled"):
			with self.assertRaises(frappe.ValidationError):
				applicant_api.set_interview_result(submitted, status)
		self.assertEqual(frappe.db.get_value("Interview", submitted, "status"), "Rejected")

		doc = frappe.get_doc("Interview", submitted)
		doc.status = "Pending"
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_set_interview_result_refuses_unknown(self):
		other = self.make_applicant("decided-two", status="Shortlisted")
		draft = self.make_saveable_interview(other, days_ago=1)
		with self.assertRaises(frappe.ValidationError):
			applicant_api.set_interview_result(draft, "Postponed")

	def test_set_interview_result_takes_every_status_and_undoes(self):
		applicant = self.make_applicant("every-status", status="Shortlisted")
		interview = self.make_saveable_interview(applicant, days_ago=1)
		for status in ("Pending", "Under Review", "Cleared", "Rejected", "Cancelled"):
			previous = frappe.db.get_value("Interview", interview, "status")
			result = applicant_api.set_interview_result(interview, status)
			self.assertEqual(result["previous_status"], previous)
			self.assertEqual(
				frappe.db.get_value("Interview", interview, ["status", "docstatus"]), (status, 0)
			)
			applicant_api.set_interview_result(interview, previous)
			self.assertEqual(
				frappe.db.get_value("Interview", interview, ["status", "docstatus"]), (previous, 0)
			)

	def test_cancelled_draft_is_listed_in_the_panel_but_outside_the_stage(self):
		applicant = self.make_applicant("cancelled-draft", status="Shortlisted")
		interview = self.make_saveable_interview(applicant, days_ago=1)
		self.assertEqual(self.get_stage(applicant)["stage"], "interviewing")

		applicant_api.set_interview_result(interview, "Cancelled")
		self.assertEqual(self.get_stage(applicant)["stage"], "shortlisted")
		self.assertFalse(self.get_stages(applicant)[applicant]["can_make_offer"])
		listed = applicant_api.get_applicant(applicant)["interviews"]
		self.assertEqual([(row["name"], row["status"]) for row in listed], [(interview, "Cancelled")])

		applicant_api.set_interview_result(interview, "Pending")
		self.assertEqual(self.get_stage(applicant)["stage"], "interviewing")

	def test_set_interview_result_needs_write_permission(self):
		applicant = self.make_applicant("decide-perm", status="Shortlisted")
		interview = self.make_saveable_interview(applicant, days_ago=1)
		frappe.set_user(NO_ROLE_USER)
		with self.assertRaises(frappe.PermissionError):
			applicant_api.set_interview_result(interview, "Cleared")

	def test_submit_interview_refuses_undecided(self):
		applicant = self.make_applicant("undecided", status="Shortlisted")
		interview = self.make_saveable_interview(applicant, status="Under Review", days_ago=1)
		with self.assertRaises(frappe.ValidationError):
			applicant_api.submit_interview(interview, "Under Review")
		self.assertEqual(
			frappe.db.get_value("Interview", interview, ["status", "docstatus"]), ("Under Review", 0)
		)

	def test_submit_interview_results_submits_only_decided_drafts(self):
		applicant = self.make_applicant("submit-results", status="Shortlisted")
		cleared = self.make_saveable_interview(applicant, "Round One", status="Cleared", days_ago=3)
		rejected = self.make_saveable_interview(applicant, "Round Two", status="Rejected", days_ago=2)
		pending = self.make_saveable_interview(applicant, "Round Three", status="Pending", days_ago=1)
		reviewing = self.make_saveable_interview(applicant, "Round Four", status="Under Review", days_ago=1)

		frappe.local.message_log.clear()
		result = applicant_api.submit_interview_results(applicant)

		self.assertEqual(sorted(result["submitted"]), sorted([cleared, rejected]))
		self.assertTrue(result["rejected"])
		docstatus = lambda name: frappe.db.get_value("Interview", name, "docstatus")  # noqa: E731
		self.assertEqual([docstatus(name) for name in (cleared, rejected, pending, reviewing)], [1, 1, 0, 0])
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Shortlisted")
		self.assertEqual(applicant_api.submit_interview_results(applicant)["submitted"], [])

	def test_submit_interview_results_needs_submit_permission(self):
		applicant = self.make_applicant("submit-results-perm", status="Shortlisted")
		interview = self.make_saveable_interview(applicant, status="Cleared", days_ago=1)
		frappe.set_user(NO_ROLE_USER)
		with self.assertRaises(frappe.PermissionError):
			applicant_api.submit_interview_results(applicant)
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("Interview", interview, "docstatus"), 0)

	def test_submit_interview_sets_the_result_submits_and_offers_to_reject_only_when_rejected(self):
		cleared = self.make_applicant("submit-cleared", status="Shortlisted")
		interview = self.make_saveable_interview(cleared, status="Under Review", days_ago=1)
		result = applicant_api.submit_interview(interview, "Cleared")
		self.assertEqual(frappe.db.get_value("Interview", interview, ["status", "docstatus"]), ("Cleared", 1))
		self.assertFalse(result["reject_applicant"])
		self.assertTrue(self.get_stages(cleared)[cleared]["can_make_offer"])
		with self.assertRaises(frappe.ValidationError):
			applicant_api.submit_interview(interview, "Rejected")

		rejected = self.make_applicant("submit-rejected", status="Shortlisted")
		interview = self.make_saveable_interview(rejected, days_ago=1)
		frappe.local.message_log.clear()
		result = applicant_api.submit_interview(interview, "Rejected")
		self.assertEqual(frappe.db.get_value("Interview", interview, "docstatus"), 1)
		self.assertTrue(result["reject_applicant"])
		self.assertEqual(result["applicant"], rejected)
		self.assertEqual(frappe.db.get_value("Job Applicant", rejected, "status"), "Shortlisted")
		self.assertFalse(frappe.local.message_log)

	def make_open_interviews(self, applicant):
		"""A draft with feedback in and one still pending, which answering an offer closes."""
		reviewed = self.make_saveable_interview(
			applicant, status="Under Review", panel=["Administrator"], feedback_from=["Administrator"]
		)
		return {reviewed: "Under Review", self.make_saveable_interview(applicant, panel=()): "Pending"}

	def assert_interview_statuses(self, statuses):
		for name, status in statuses.items():
			self.assertEqual(frappe.db.get_value("Interview", name, "status"), status)

	def test_set_offer_answer_accept_hires_and_undo_restores(self):
		applicant = self.make_applicant("accepts", status="Shortlisted")
		interviews = self.make_open_interviews(applicant)
		offer = self.make_offer(applicant, docstatus=1, applicant_email=applicant)

		result = applicant_api.set_offer_answer(offer, "Accepted")
		self.assertEqual(result["previous_status"], "Awaiting Response")
		self.assertEqual(frappe.db.get_value("Job Offer", offer, ["status", "docstatus"]), ("Accepted", 1))
		self.assertEqual(self.get_stage(applicant)["stage"], "hired")
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "stage"), "Hired")

		self.assert_interview_statuses(dict(zip(interviews, ("Cleared", "Cancelled"), strict=True)))

		applicant_api.set_offer_answer(
			offer,
			result["previous_status"],
			result["previous_applicant_status"],
			frappe.as_json(result["closed_interviews"]),
		)
		self.assertEqual(frappe.db.get_value("Job Offer", offer, "status"), "Awaiting Response")
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Shortlisted")
		self.assertEqual(self.get_stage(applicant)["stage"], "offered")
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "stage"), "Offered")
		self.assert_interview_statuses(interviews)

	def test_set_offer_answer_decline_rejects_the_applicant_and_undo_restores(self):
		applicant = self.make_applicant("declines", status="Shortlisted")
		interviews = self.make_open_interviews(applicant)
		offer = self.make_offer(applicant, docstatus=1, applicant_email=applicant)

		result = applicant_api.set_offer_answer(offer, "Rejected")
		self.assertEqual(frappe.db.get_value("Job Offer", offer, "status"), "Rejected")
		# the offer's own hook marks the applicant rejected
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Rejected")
		self.assertEqual(self.get_stage(applicant)["stage"], "rejected")
		self.assert_interview_statuses(dict(zip(interviews, ("Rejected", "Cancelled"), strict=True)))

		applicant_api.set_offer_answer(
			offer, result["previous_status"], result["previous_applicant_status"], result["closed_interviews"]
		)
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Shortlisted")
		self.assertEqual(self.get_stage(applicant)["stage"], "offered")
		self.assert_interview_statuses(interviews)

	def test_offer_fact_follows_the_offer_status(self):
		offer = frappe._dict(docstatus=1, status="Ready to Send", offer_date=nowdate(), creation=nowdate())
		facts = {
			("Draft", 0): "Offer in draft",
			("Ready to Send", 1): "Offer ready to send",
		}
		for (status, docstatus), fact in facts.items():
			offer.update(status=status, docstatus=docstatus)
			self.assertEqual(hiring.get_offer_fact(offer), fact)
		offer.update(status="Awaiting Response", docstatus=1)
		self.assertTrue(hiring.get_offer_fact(offer).startswith("Offer sent"))

	def test_set_offer_answer_from_ready_to_send(self):
		for status, applicant_status in (
			("Awaiting Response", "Shortlisted"),
			("Accepted", "Accepted"),
			("Rejected", "Rejected"),
		):
			applicant = self.make_applicant(f"ready-{status.replace(' ', '-')}", status="Shortlisted")
			offer = self.make_offer(
				applicant,
				status="Ready to Send",
				docstatus=1,
				applicant_email=f"{status.replace(' ', '')}@example.com",
			)
			result = applicant_api.set_offer_answer(offer, status)
			self.assertEqual(result["previous_status"], "Ready to Send")
			self.assertEqual(frappe.db.get_value("Job Offer", offer, "status"), status)
			self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), applicant_status)

	def test_set_offer_answer_from_awaiting_response_and_invalid_moves(self):
		applicant = self.make_applicant("awaiting-answer", status="Shortlisted")
		offer = self.make_offer(applicant, docstatus=1, applicant_email="awaiting@example.com")
		for status in ("Draft", "Cancelled", "Maybe"):
			with self.assertRaises(frappe.ValidationError):
				applicant_api.set_offer_answer(offer, status)
		applicant_api.set_offer_answer(offer, "Rejected")
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Rejected")
		# an answered offer can't be answered the other way, only undone
		with self.assertRaises(frappe.ValidationError):
			applicant_api.set_offer_answer(offer, "Accepted")

	def test_set_offer_answer_refuses_drafts_and_unsent_offers(self):
		applicant = self.make_applicant("draft-answer", status="Shortlisted")
		draft = self.make_offer(applicant, status="Draft", docstatus=0)
		with self.assertRaises(frappe.ValidationError):
			applicant_api.set_offer_answer(draft, "Accepted")

		other = self.make_applicant("unsent-answer", status="Shortlisted")
		unsent = self.make_offer(other, status="Ready to Send", docstatus=1, applicant_email="x@example.com")
		with self.assertRaises(frappe.ValidationError):
			applicant_api.set_offer_answer(unsent, "Maybe")
		self.assertEqual(frappe.db.get_value("Job Offer", unsent, "status"), "Ready to Send")

	def test_applicant_detail_stage_since(self):
		applied = self.make_applicant("since-applied")
		creation = frappe.db.get_value("Job Applicant", applied, "creation")
		self.assertEqual(applicant_api.get_applicant(applied)["stage_since"], creation)

		interviewing = self.make_applicant("since-interviewing", status="Shortlisted")
		interview = self.make_interview(interviewing, days_ago=1)
		self.assertEqual(
			applicant_api.get_applicant(interviewing)["stage_since"],
			frappe.db.get_value("Interview", interview, "creation"),
		)

		offered = self.make_applicant("since-offered", status="Accepted")
		offer = self.make_offer(offered)
		self.assertEqual(
			applicant_api.get_applicant(offered)["stage_since"],
			frappe.db.get_value("Job Offer", offer, "creation"),
		)

	def test_applicant_detail_stage_since_follows_status_change(self):
		applicant = self.make_applicant("since-status")
		self.write("Job Applicant", applicant, {"status": "Shortlisted"})
		modified = frappe.db.get_value("Job Applicant", applicant, "modified")
		self.assertEqual(applicant_api.get_applicant(applicant)["stage_since"], modified)

		changed_on = add_days(frappe.db.get_value("Job Applicant", applicant, "creation"), 1)
		version = frappe.get_doc(
			{
				"doctype": "Version",
				"ref_doctype": "Job Applicant",
				"docname": applicant,
				"data": frappe.as_json({"changed": [["status", "Open", "Shortlisted"]]}),
			}
		).insert(ignore_permissions=True)
		frappe.db.set_value("Version", version.name, "creation", changed_on)
		result = applicant_api.get_applicant(applicant)
		self.assertEqual((result["stage"], result["stage_since"]), ("shortlisted", get_datetime(changed_on)))

	def test_applicant_detail_refuses_users_without_applicant_access(self):
		applicant = self.make_applicant("detail-secret")
		for user in (NO_ROLE_USER, INTERVIEWER):
			frappe.set_user(user)
			self.assertRaises(frappe.PermissionError, applicant_api.get_applicant, applicant)

	def make_email(self, applicant, subject, date, sent_or_received="Received", seen=0, **kwargs):
		communication = frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"subject": subject,
				"content": f"<p>{subject}</p>",
				"sender": "recruiter@example.com" if sent_or_received == "Sent" else "candidate@example.com",
				"recipients": "candidate@example.com"
				if sent_or_received == "Sent"
				else "recruiter@example.com",
				"sent_or_received": sent_or_received,
				"seen": seen,
				"communication_date": date,
				"reference_doctype": "Job Applicant",
				"reference_name": applicant,
				**kwargs,
			}
		)
		communication.insert(ignore_permissions=True)
		return communication.name

	def test_applicant_detail_emails_in_date_order_for_this_applicant_only(self):
		applicant = self.make_applicant("mailed")
		other = self.make_applicant("unmailed")
		later = self.make_email(applicant, "Later", "2026-03-02 10:00:00")
		earlier = self.make_email(applicant, "Earlier", "2026-03-01 10:00:00", "Sent")
		self.make_email(other, "Not yours", "2026-03-01 12:00:00")
		result = applicant_api.get_applicant(applicant)
		self.assertEqual([email.name for email in result["emails"]], [earlier, later])
		self.assertEqual(applicant_api.get_applicant(other)["emails"][0].subject, "Not yours")

	def test_applicant_detail_comments_only_of_type_comment(self):
		applicant = self.make_applicant("commented")
		doc = frappe.get_doc("Job Applicant", applicant)
		doc.add_comment("Comment", "Strong portfolio")
		doc.add_comment("Info", "Something happened")
		result = applicant_api.get_applicant(applicant)
		self.assertEqual([comment.content for comment in result["comments"]], ["Strong portfolio"])

	def test_applicant_detail_cannot_send_email_without_outgoing_account(self):
		applicant = self.make_applicant("noaccount")
		frappe.set_user("Administrator")
		outgoing = frappe.get_all("Email Account", filters={"enable_outgoing": 1}, pluck="name")
		for name in outgoing:
			frappe.db.set_value("Email Account", name, "enable_outgoing", 0)
		result = applicant_api.get_applicant(applicant)
		self.assertFalse(result["can_send_email"])
		self.assertIsNone(result["email_sender"])

	def test_mark_emails_seen_marks_only_received_unseen_emails_of_the_applicant(self):
		applicant = self.make_applicant("unread")
		other = self.make_applicant("untouched")
		received = self.make_email(applicant, "Hello", "2026-03-01 10:00:00")
		sent = self.make_email(applicant, "Hi", "2026-03-01 11:00:00", "Sent", seen=0)
		elsewhere = self.make_email(other, "Hello", "2026-03-01 12:00:00")
		applicant_api.mark_emails_seen(applicant)
		self.assertEqual(frappe.db.get_value("Communication", received, "seen"), 1)
		self.assertEqual(frappe.db.get_value("Communication", sent, "seen"), 0)
		self.assertEqual(frappe.db.get_value("Communication", elsewhere, "seen"), 0)

	def test_mark_emails_seen_refuses_users_without_applicant_access(self):
		applicant = self.make_applicant("guarded")
		received = self.make_email(applicant, "Hello", "2026-03-01 10:00:00")
		frappe.set_user(NO_ROLE_USER)
		self.assertRaises(frappe.PermissionError, applicant_api.mark_emails_seen, applicant)
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("Communication", received, "seen"), 0)

	def make_outgoing_account(self, email_id="hiring.outgoing@example.com"):
		frappe.set_user("Administrator")
		for name in frappe.get_all("Email Account", filters={"enable_outgoing": 1}, pluck="name"):
			frappe.db.set_value("Email Account", name, "enable_outgoing", 0)
		frappe.get_doc(
			{
				"doctype": "Email Account",
				"email_account_name": "Hiring Test Outgoing",
				"email_id": email_id,
				"enable_outgoing": 1,
				"default_outgoing": 1,
				"smtp_server": "smtp.example.com",
				"smtp_port": 587,
				"use_tls": 1,
				"password": "not-a-real-password",
			}
		).insert(ignore_permissions=True, ignore_mandatory=True)
		frappe.set_user(HR_USER)

	def reject_with_email(self, label="rejectme"):
		self.make_outgoing_account()
		applicant = self.make_applicant(label, status="Shortlisted")
		result = applicant_api.reject_applicant(applicant, 1, "Your application", "Hi,\n\nSorry <b>no</b>.")
		return applicant, result

	def test_unanimous_rejecting_feedback_makes_the_interview_not_cleared(self):
		applicant = self.make_applicant("not-cleared", status="Shortlisted")
		interview = self.make_interview(
			applicant,
			status="Under Review",
			panel=["Administrator", "test@example.com"],
			feedback_from=["Administrator"],
		)
		frappe.db.set_value("Interview Feedback", {"interview": interview}, "result", "Rejected")
		self.assertEqual(applicant_api.get_applicant(applicant)["interview_group"], "not_cleared")
		self.assertEqual(applicant_api.get_applicant(applicant)["interviews"][0]["is_not_cleared"], True)

		# one clearing feedback among rejections keeps the usual flow
		self.make_feedback(interview, applicant, "test@example.com")
		frappe.db.set_value(
			"Interview Feedback",
			{"interview": interview, "interviewer": "test@example.com"},
			"result",
			"Cleared",
		)
		self.assertNotEqual(applicant_api.get_applicant(applicant)["interview_group"], "not_cleared")

	def test_reject_applicant_closes_open_interviews(self):
		applicant = self.make_applicant("closes-interviews", status="Shortlisted")
		with_feedback = self.make_saveable_interview(
			applicant, status="Under Review", panel=["Administrator"], feedback_from=["Administrator"]
		)
		without_feedback = self.make_saveable_interview(applicant, status="Pending", panel=())
		cleared = self.make_saveable_interview(applicant, status="Cleared")

		applicant_api.reject_applicant(applicant)

		def status(name):
			return frappe.db.get_value("Interview", name, ["status", "docstatus"])

		self.assertEqual(status(with_feedback), ("Rejected", 0))
		self.assertEqual(status(without_feedback), ("Cancelled", 0))
		self.assertEqual(status(cleared), ("Cleared", 0))

	def test_undo_reject_restores_the_interviews_the_reject_closed(self):
		applicant = self.make_applicant("undo-interviews", status="Shortlisted")
		with_feedback = self.make_saveable_interview(
			applicant, status="Under Review", panel=["Administrator"], feedback_from=["Administrator"]
		)
		without_feedback = self.make_saveable_interview(applicant, status="Pending", panel=())
		cleared = self.make_saveable_interview(applicant, status="Cleared")

		result = applicant_api.reject_applicant(applicant)
		self.assertCountEqual(
			result["closed_interviews"],
			[
				{"name": with_feedback, "status": "Under Review"},
				{"name": without_feedback, "status": "Pending"},
			],
		)

		applicant_api.undo_reject_applicant(
			applicant, result["previous_status"], None, frappe.as_json(result["closed_interviews"])
		)

		def status(name):
			return frappe.db.get_value("Interview", name, "status")

		self.assertEqual(status(with_feedback), "Under Review")
		self.assertEqual(status(without_feedback), "Pending")
		self.assertEqual(status(cleared), "Cleared")
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Shortlisted")

	def make_interviews_with_own_designation(self, applicant):
		"""Open drafts whose designation their Interview Type doesn't carry, which a re-fetch would blank."""
		interviews = self.make_open_interviews(applicant)
		for name in interviews:
			frappe.db.set_value("Interview", name, "designation", "Researcher", update_modified=False)
		return interviews

	def get_interview_fields(self, name):
		"""Every stored field of the interview and its rows, except the status and timestamps a save moves."""

		def strip(row):
			return {key: value for key, value in row.items() if key not in ("modified", "status")}

		values = strip(frappe.get_doc("Interview", name).as_dict())
		values["interview_details"] = [strip(row) for row in values["interview_details"]]
		return values

	def test_offer_answer_and_undo_change_only_the_interview_status(self):
		applicant = self.make_applicant("offer-keeps-fields", status="Shortlisted")
		interviews = self.make_interviews_with_own_designation(applicant)
		before = {name: self.get_interview_fields(name) for name in interviews}
		offer = self.make_offer(applicant, docstatus=1, applicant_email=applicant)

		result = applicant_api.set_offer_answer(offer, "Rejected")
		applicant_api.set_offer_answer(
			offer, result["previous_status"], result["previous_applicant_status"], result["closed_interviews"]
		)

		self.assert_interview_statuses(interviews)
		self.assertEqual({name: self.get_interview_fields(name) for name in interviews}, before)

	def test_reject_and_undo_change_only_the_interview_status(self):
		applicant = self.make_applicant("reject-keeps-fields", status="Shortlisted")
		interviews = self.make_interviews_with_own_designation(applicant)
		before = {name: self.get_interview_fields(name) for name in interviews}

		result = applicant_api.reject_applicant(applicant)
		self.assertEqual({name: self.get_interview_fields(name) for name in interviews}, before)
		applicant_api.undo_reject_applicant(
			applicant, result["previous_status"], None, frappe.as_json(result["closed_interviews"])
		)

		self.assert_interview_statuses(interviews)
		self.assertEqual({name: self.get_interview_fields(name) for name in interviews}, before)

	def test_has_cleared_interview_counts_drafts_and_submitted_but_not_cancelled(self):
		none = self.make_applicant("cleared-none", status="Shortlisted")
		self.assertFalse(applicant_api.has_cleared_interview(none))
		self.assertEqual(applicant_api.get_offer_readiness(none)["needs_confirmation"], False)

		draft = self.make_applicant("cleared-draft", status="Shortlisted")
		self.make_saveable_interview(draft, status="Cleared")
		submitted = self.make_applicant("cleared-submitted", status="Shortlisted")
		self.make_saveable_interview(submitted, status="Cleared", docstatus=1)
		for applicant in (draft, submitted):
			self.assertTrue(applicant_api.has_cleared_interview(applicant))
			self.assertFalse(applicant_api.get_offer_readiness(applicant)["needs_confirmation"])

		pending = self.make_applicant("cleared-pending", status="Shortlisted")
		self.make_saveable_interview(pending, status="Pending")
		self.assertFalse(applicant_api.has_cleared_interview(pending))
		self.assertTrue(applicant_api.get_offer_readiness(pending)["needs_confirmation"])

		cancelled = self.make_applicant("cleared-cancelled", status="Shortlisted")
		self.make_saveable_interview(cancelled, status="Cancelled")
		self.assertFalse(applicant_api.get_offer_readiness(cancelled)["needs_confirmation"])

	def test_accepted_offer_closes_open_draft_interviews(self):
		applicant = self.make_applicant("accepts-closes", status="Shortlisted")
		with_feedback = self.make_saveable_interview(
			applicant, status="Under Review", panel=["Administrator"], feedback_from=["Administrator"]
		)
		without_feedback = self.make_saveable_interview(applicant, status="Pending", panel=())
		rejected = self.make_saveable_interview(applicant, status="Rejected")
		offer = self.make_offer(applicant, status="Awaiting Response", docstatus=1, applicant_email=applicant)

		applicant_api.set_offer_answer(offer, "Accepted")

		def status(name):
			return frappe.db.get_value("Interview", name, ["status", "docstatus"])

		self.assertEqual(status(with_feedback), ("Cleared", 0))
		self.assertEqual(status(without_feedback), ("Cancelled", 0))
		self.assertEqual(status(rejected), ("Rejected", 0))

	def test_move_back_returns_a_rejected_applicant_to_their_stage(self):
		applicant = self.make_applicant("moves-back", status="Shortlisted")
		applicant_api.reject_applicant(applicant)
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "stage"), "Rejected")

		result = applicant_api.move_back_applicant(applicant)
		self.assertEqual(result, {"stage": "applied", "stage_label": "Applied"})
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Open")

		with self.assertRaises(frappe.ValidationError):
			applicant_api.move_back_applicant(applicant)

		interviewing = self.make_applicant("moves-back-interviewing", status="Shortlisted")
		self.make_saveable_interview(interviewing, status="Cleared")
		applicant_api.reject_applicant(interviewing)
		self.assertEqual(applicant_api.move_back_applicant(interviewing)["stage"], "interviewing")

	def test_move_back_reopens_the_interviews_the_reject_closed(self):
		applicant = self.make_applicant("moves-back-reopens", status="Shortlisted")
		with_feedback = self.make_saveable_interview(
			applicant,
			status="Under Review",
			days_ago=1,
			panel=["Administrator"],
			feedback_from=["Administrator"],
		)
		without_feedback = self.make_saveable_interview(applicant, status="Pending", panel=())
		future = self.make_saveable_interview(
			applicant,
			interview_type="Hiring Test Round 2",
			status="Under Review",
			days_ago=-3,
			panel=["Administrator"],
			feedback_from=["Administrator"],
		)
		cleared = self.make_saveable_interview(
			applicant, interview_type="Hiring Test Round 3", status="Cleared"
		)
		submitted = self.make_saveable_interview(
			applicant, interview_type="Hiring Test Round 4", status="Cancelled", docstatus=1
		)

		applicant_api.reject_applicant(applicant)

		def status(name):
			return frappe.db.get_value("Interview", name, "status")

		self.assertEqual(status(with_feedback), "Rejected")
		self.assertEqual(status(without_feedback), "Cancelled")

		result = applicant_api.move_back_applicant(applicant)

		self.assertEqual(status(with_feedback), "Under Review")
		self.assertEqual(status(without_feedback), "Pending")
		self.assertEqual(status(future), "Pending")
		self.assertEqual(status(cleared), "Cleared")
		self.assertEqual(status(submitted), "Cancelled")
		self.assertEqual(result["stage"], "interviewing")
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "stage"), "Interviewing")

	def test_declined_offer_closes_open_interviews(self):
		applicant = self.make_applicant("declines-closes", status="Shortlisted")
		with_feedback = self.make_saveable_interview(
			applicant, status="Under Review", panel=["Administrator"], feedback_from=["Administrator"]
		)
		without_feedback = self.make_saveable_interview(
			applicant, interview_type="Hiring Test Round 2", status="Pending", panel=()
		)
		offer = self.make_offer(applicant, status="Awaiting Response", docstatus=1, applicant_email=applicant)

		applicant_api.set_offer_answer(offer, "Rejected")

		def status(name):
			return frappe.db.get_value("Interview", name, ["status", "docstatus"])

		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Rejected")
		self.assertEqual(status(with_feedback), ("Rejected", 0))
		self.assertEqual(status(without_feedback), ("Cancelled", 0))

	def test_hired_drop_message_depends_on_a_live_offer(self):
		applicant = self.make_applicant("no-offer", status="Shortlisted")
		readiness = applicant_api.get_offer_readiness(applicant)
		self.assertFalse(readiness["has_live_offer"])
		self.assertFalse(readiness["has_accepted_offer"])

	def test_reject_applicant_sets_rejected_and_returns_previous_status(self):
		applicant = self.make_applicant("rejected", status="Shortlisted")
		result = applicant_api.reject_applicant(applicant)
		self.assertEqual(
			result, {"previous_status": "Shortlisted", "communication": None, "closed_interviews": []}
		)
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Rejected")
		self.assertFalse(frappe.db.exists("Communication", {"reference_name": applicant}))

	def test_reject_applicant_stores_the_reason_and_note(self):
		applicant = self.make_applicant("reasoned", status="Shortlisted")
		applicant_api.reject_applicant(applicant, reason="Withdrew", note="  Took another offer  ")
		values = frappe.db.get_value("Job Applicant", applicant, ["rejection_reason", "rejection_note"])
		self.assertEqual(values, ("Withdrew", "Took another offer"))
		# the stage card shows the reason
		self.assertEqual(self.get_stage(applicant)["fact"], "Withdrew")
		self.assertEqual(applicant_api.get_applicant(applicant)["rejection_note"], "Took another offer")

	def test_undo_reject_and_move_back_clear_the_reason(self):
		def reason(name):
			return frappe.db.get_value("Job Applicant", name, ["rejection_reason", "rejection_note"])

		undone = self.make_applicant("undo-reason", status="Shortlisted")
		result = applicant_api.reject_applicant(undone, reason="No response", note="Silent")
		applicant_api.undo_reject_applicant(undone, result["previous_status"])
		self.assertEqual(reason(undone), (None, None))

		moved = self.make_applicant("back-reason", status="Shortlisted")
		applicant_api.reject_applicant(moved, reason="Not qualified", note="Too junior")
		applicant_api.move_back_applicant(moved)
		self.assertEqual(reason(moved), (None, None))

	def test_declined_offer_sets_the_reason_unless_one_is_given(self):
		applicant = self.make_applicant("declines-reason", status="Shortlisted")
		offer = self.make_offer(applicant, docstatus=1, applicant_email=applicant)
		result = applicant_api.set_offer_answer(offer, "Rejected")
		self.assertEqual(
			frappe.db.get_value("Job Applicant", applicant, "rejection_reason"), "Declined offer"
		)

		applicant_api.set_offer_answer(offer, result["previous_status"], result["previous_applicant_status"])
		self.assertIsNone(frappe.db.get_value("Job Applicant", applicant, "rejection_reason"))

		# a reason someone already gave stays
		frappe.db.set_value("Job Applicant", applicant, "rejection_reason", "Salary mismatch")
		applicant_api.set_offer_answer(offer, "Rejected")
		self.assertEqual(
			frappe.db.get_value("Job Applicant", applicant, "rejection_reason"), "Salary mismatch"
		)

	def test_reject_applicant_with_email_queues_a_delayed_communication(self):
		applicant, result = self.reject_with_email()
		communication = frappe.get_doc("Communication", result["communication"])
		self.assertEqual(
			(communication.reference_doctype, communication.reference_name), ("Job Applicant", applicant)
		)
		self.assertEqual(communication.subject, "Your application")
		self.assertEqual(communication.content, "Hi,<br><br>Sorry &lt;b&gt;no&lt;/b&gt;.")
		self.assertEqual(communication.sender, "hiring.outgoing@example.com")
		queue = frappe.get_all(
			"Email Queue", filters={"communication": communication.name}, fields=["status", "send_after"]
		)
		self.assertEqual(len(queue), 1)
		self.assertEqual(queue[0].status, "Not Sent")
		self.assertGreater(get_datetime(queue[0].send_after), now_datetime())
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Rejected")

	def test_undo_reject_restores_status_and_cancels_unsent_email(self):
		applicant, result = self.reject_with_email()
		undone = applicant_api.undo_reject_applicant(
			applicant, result["previous_status"], result["communication"]
		)
		self.assertEqual(undone, {"email_cancelled": True})
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Shortlisted")
		self.assertFalse(frappe.db.exists("Communication", result["communication"]))
		self.assertFalse(frappe.db.exists("Email Queue", {"communication": result["communication"]}))

	def test_undo_reject_leaves_a_sent_email_alone(self):
		applicant, result = self.reject_with_email()
		frappe.db.set_value("Email Queue", {"communication": result["communication"]}, "status", "Sent")
		undone = applicant_api.undo_reject_applicant(
			applicant, result["previous_status"], result["communication"]
		)
		self.assertEqual(undone, {"email_cancelled": False})
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Shortlisted")
		self.assertTrue(frappe.db.exists("Communication", result["communication"]))

	def test_undo_reject_leaves_another_applicants_email_alone(self):
		_rejected, rejection = self.reject_with_email()
		applicant = self.make_applicant("undo-foreign", status="Rejected")
		undone = applicant_api.undo_reject_applicant(applicant, "Shortlisted", rejection["communication"])
		self.assertEqual(undone, {"email_cancelled": False})
		self.assertTrue(frappe.db.exists("Communication", rejection["communication"]))
		self.assertTrue(frappe.db.exists("Email Queue", {"communication": rejection["communication"]}))

	def test_undo_reject_without_email(self):
		applicant = self.make_applicant("undoplain", status="Open")
		applicant_api.reject_applicant(applicant)
		self.assertEqual(applicant_api.undo_reject_applicant(applicant, "Open"), {"email_cancelled": False})
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Open")

	def test_reject_and_undo_require_write_access(self):
		applicant = self.make_applicant("guarded-reject", status="Open")
		frappe.set_user(NO_ROLE_USER)
		self.assertRaises(frappe.PermissionError, applicant_api.reject_applicant, applicant)
		self.assertRaises(frappe.PermissionError, applicant_api.undo_reject_applicant, applicant, "Open")
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Open")

	def test_email_sender_prefers_hr_settings_hiring_sender_email(self):
		applicant = self.make_applicant("sender")
		self.make_outgoing_account()
		self.assertEqual(
			applicant_api.get_applicant(applicant)["email_sender"], "hiring.outgoing@example.com"
		)
		frappe.db.set_single_value("HR Settings", "hiring_sender_email", "careers@example.com")
		self.assertEqual(applicant_api.get_applicant(applicant)["email_sender"], "careers@example.com")

	def test_applicant_detail_has_opening_title_and_company(self):
		result = applicant_api.get_applicant(self.make_applicant("titled"))
		self.assertEqual((result["job_title"], result["company"]), ("Hiring Test Opening", self.company))

	def test_opening_header_adds_location_only_when_an_open_role_shares_the_name(self):
		for location in ("Pune", "Bengaluru", "Mumbai"):
			if not frappe.db.exists("Branch", location):
				frappe.get_doc({"doctype": "Branch", "branch": location}).insert(ignore_permissions=True)
		alone = self.make_opening("Only Role", location="Pune")
		self.assertEqual(hiring.get_opening_header(alone.name)["display_title"], "Only Role")
		first = self.make_opening("Twin Role", location="Bengaluru")
		second = self.make_opening("Twin Role", location="Mumbai", route="jobs/twin-role-mumbai")
		self.assertEqual(hiring.get_opening_header(first.name)["display_title"], "Twin Role · Bengaluru")
		self.assertEqual(hiring.get_opening_header(second.name)["display_title"], "Twin Role · Mumbai")
		second.db_set("status", "Closed")
		self.assertEqual(hiring.get_opening_header(first.name)["display_title"], "Twin Role")
		self.assertEqual(hiring.get_opening_header(second.name)["status"], "Closed")
