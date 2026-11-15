import frappe
from frappe.core.doctype.user_permission.test_user_permission import create_user
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, get_datetime, now_datetime, nowdate

from hrms.hr.doctype.interview.interview import has_cleared_interview, submit_interview_results
from hrms.hr.doctype.job_applicant.job_applicant import (
	get_applicant_stage,
	get_email_setup,
	get_offer_readiness,
	get_reject_details,
	get_stage,
	reject_applicant,
	set_applicant_status,
	undo_reject_applicant,
	update_stage,
)
from hrms.hr.doctype.job_applicant.stage_info import APPLICANT_FIELDS, ApplicantRecords, get_offer_fact
from hrms.hr.doctype.job_offer.job_offer import set_offer_answer
from hrms.hr.doctype.job_opening.job_opening import get_opening_header

HR_USER = "hiring.hr@example.com"
NO_ROLE_USER = "hiring.norole@example.com"
INTERVIEWER = "hiring.interviewer@example.com"


class TestHiringFlow(IntegrationTestCase):
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
		return get_applicant_stage(applicant)

	def test_applied_includes_replied_and_hold(self):
		open_ = self.make_applicant("open")
		replied = self.make_applicant("replied", status="Replied")
		hold = self.make_applicant("hold", status="Hold")

		self.assertEqual(self.get_stage(open_)["stage"], "Applied")
		self.assertEqual(self.get_stage(replied)["stage"], "Applied")
		self.assertEqual(self.get_stage(hold)["stage"], "Applied")

		stages = self.get_stages(open_, hold)
		self.assertFalse(stages[open_]["on_hold"])
		self.assertTrue(stages[hold]["on_hold"])

	def get_stages(self, *names):
		applicants = frappe.get_list(
			"Job Applicant", filters={"name": ["in", names]}, fields=APPLICANT_FIELDS
		)
		records = ApplicantRecords(applicants)
		return {applicant.name: records.get_stage_info(applicant) for applicant in applicants}

	def test_hold_keeps_the_shortlisted_stage(self):
		shortlisted = self.make_applicant("short", status="Shortlisted")
		self.assertEqual(self.get_stage(shortlisted)["stage"], "Shortlisted")

		self.write("Job Applicant", shortlisted, {"status": "Hold"})
		self.assertEqual(self.get_stage(shortlisted)["stage"], "Shortlisted")
		self.assertTrue(self.get_stages(shortlisted)[shortlisted]["on_hold"])

	def test_legacy_accepted_without_offer_is_shortlisted(self):
		applicant = self.make_applicant("legacy", status="Accepted")
		result = self.get_stage(applicant)
		self.assertEqual(result["stage"], "Shortlisted")
		self.assertEqual(result["fact"], "Ready for offer")

	def test_rejected_wins_over_everything(self):
		applicant = self.make_applicant("rejected", status="Rejected")
		self.make_interview(applicant)
		self.make_offer(applicant, docstatus=1)
		self.assertEqual(self.get_stage(applicant)["stage"], "Rejected")

	def test_interviewing_with_feedback_progress(self):
		applicant = self.make_applicant("interview", status="Shortlisted")
		panel = [INTERVIEWER, HR_USER]
		self.make_interview(
			applicant, status="Under Review", days_ago=1, panel=panel, feedback_from=[INTERVIEWER]
		)

		result = self.get_stage(applicant)
		self.assertEqual(result["stage"], "Interviewing")
		self.assertTrue(result["fact"].endswith("Feedback 1 of 2"))

	def test_interview_in_future_has_no_feedback_count(self):
		applicant = self.make_applicant("future")
		self.make_interview(applicant, days_ago=-3, panel=[INTERVIEWER])
		self.assertNotIn("Feedback", self.get_stage(applicant)["fact"])

	def test_cleared_interview_can_make_offer_until_offer_exists(self):
		applicant = self.make_applicant("cleared", status="Shortlisted")
		self.make_interview(applicant, status="Cleared", days_ago=1, docstatus=1, panel=[INTERVIEWER])

		result = self.get_stage(applicant)
		self.assertEqual(result["stage"], "Interviewing")
		self.assertTrue(result["fact"].endswith("Cleared"))
		self.assertTrue(self.get_stages(applicant)[applicant]["can_make_offer"])

		self.make_offer(applicant)
		self.assertEqual(self.get_stage(applicant)["stage"], "Offered")
		self.assertFalse(self.get_stages(applicant)[applicant]["can_make_offer"])

	def test_cancelled_interview_drops_applicant_back(self):
		applicant = self.make_applicant("dropback", status="Shortlisted")
		interview = self.make_interview(applicant)
		self.assertEqual(self.get_stage(applicant)["stage"], "Interviewing")

		self.write("Interview", interview, {"status": "Cancelled", "docstatus": 2})
		self.assertEqual(self.get_stage(applicant)["stage"], "Shortlisted")

		other = self.make_applicant("dropback-two")
		interview = self.make_interview(other)
		self.write("Interview", interview, {"status": "Cancelled"})
		self.assertEqual(self.get_stage(other)["stage"], "Applied")

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
		self.assertEqual(result["stage"], "Offered")
		self.assertEqual(result["fact"], "Offer in draft")

		self.write("Job Offer", offer, {"docstatus": 1, "status": "Ready to Send"})
		self.assertEqual(self.get_stage(applicant)["fact"], "Offer ready to send")

		self.write("Job Offer", offer, {"status": "Awaiting Response"})
		self.assertTrue(self.get_stage(applicant)["fact"].startswith("Offer sent"))

		self.write("Job Offer", offer, {"docstatus": 2})
		self.assertEqual(self.get_stage(applicant)["stage"], "Applied")

	def test_draft_status_offer_is_offered_like_the_applicants_own_stage(self):
		applicant = self.make_applicant("draft-status", status="Shortlisted")
		self.make_interview(applicant, status="Pending", days_ago=1)
		self.make_offer(applicant, status="Draft")
		self.assertEqual(self.get_stage(applicant)["stage"], "Offered")
		self.assertEqual(get_stage(frappe.get_doc("Job Applicant", applicant)), "Offered")

	def test_hired_by_accepted_submitted_offer(self):
		applicant = self.make_applicant("hired", status="Accepted")
		offer = self.make_offer(applicant, status="Accepted")
		self.assertEqual(self.get_stage(applicant)["stage"], "Shortlisted")

		self.write("Job Offer", offer, {"docstatus": 1})
		self.assertEqual(self.get_stage(applicant)["stage"], "Hired")

	def test_hired_by_employee(self):
		applicant = self.make_applicant("employee", status="Shortlisted")
		self.make_employee("Hired", applicant)
		self.assertEqual(self.get_stage(applicant)["stage"], "Hired")

	def test_referred_by_fact(self):
		referrer = self.make_employee("Referrer", None)
		applicant = self.make_applicant("referred", source_name=referrer)
		referrer_name = frappe.db.get_value("Employee", referrer, "employee_name")
		self.assertEqual(self.get_stage(applicant)["fact"], f"Referred by {referrer_name}")

		if not frappe.db.exists("Job Applicant Source", "LinkedIn"):
			frappe.get_doc({"doctype": "Job Applicant Source", "source_name": "LinkedIn"}).insert()
		plain = self.make_applicant("plain", source="LinkedIn")
		self.assertEqual(self.get_stage(plain)["fact"], "LinkedIn")

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
			self.assertEqual(info["stage"], get_stage(frappe.get_doc("Job Applicant", name)), name)
		self.assertEqual([info["stage"] for info in self.get_stages(*applicants).values()].count("Hired"), 2)

	def test_user_without_hr_role_is_refused(self):
		applicant = self.make_applicant("secret")
		for user in (NO_ROLE_USER, INTERVIEWER):
			frappe.set_user(user)
			self.assertRaises(frappe.PermissionError, get_applicant_stage, applicant)

	def test_draft_cleared_interview_can_make_offer(self):
		applicant = self.make_applicant("cleared-draft", status="Shortlisted")
		self.make_interview(applicant, status="Cleared", days_ago=1, docstatus=0, panel=[INTERVIEWER])
		self.assertTrue(self.get_stages(applicant)[applicant]["can_make_offer"])

	def test_submit_interview_results_submits_only_decided_drafts(self):
		applicant = self.make_applicant("submit-results", status="Shortlisted")
		cleared = self.make_saveable_interview(applicant, "Round One", status="Cleared", days_ago=3)
		rejected = self.make_saveable_interview(applicant, "Round Two", status="Rejected", days_ago=2)
		pending = self.make_saveable_interview(applicant, "Round Three", status="Pending", days_ago=1)
		reviewing = self.make_saveable_interview(applicant, "Round Four", status="Under Review", days_ago=1)

		frappe.local.message_log.clear()
		result = submit_interview_results(applicant)

		self.assertEqual(sorted(result["submitted"]), sorted([cleared, rejected]))
		self.assertTrue(result["rejected"])
		docstatus = lambda name: frappe.db.get_value("Interview", name, "docstatus")  # noqa: E731
		self.assertEqual([docstatus(name) for name in (cleared, rejected, pending, reviewing)], [1, 1, 0, 0])
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Shortlisted")
		self.assertEqual(submit_interview_results(applicant)["submitted"], [])

	def test_submit_interview_results_needs_submit_permission(self):
		applicant = self.make_applicant("submit-results-perm", status="Shortlisted")
		interview = self.make_saveable_interview(applicant, status="Cleared", days_ago=1)
		frappe.set_user(NO_ROLE_USER)
		with self.assertRaises(frappe.PermissionError):
			submit_interview_results(applicant)
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("Interview", interview, "docstatus"), 0)

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

		result = set_offer_answer(offer, "Accepted")
		self.assertEqual(result["previous_status"], "Awaiting Response")
		self.assertEqual(frappe.db.get_value("Job Offer", offer, ["status", "docstatus"]), ("Accepted", 1))
		self.assertEqual(self.get_stage(applicant)["stage"], "Hired")
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "stage"), "Hired")

		self.assert_interview_statuses(dict(zip(interviews, ("Cleared", "Cancelled"), strict=True)))

		set_offer_answer(
			offer,
			result["previous_status"],
			result["previous_applicant_status"],
			frappe.as_json(result["closed_interviews"]),
		)
		self.assertEqual(frappe.db.get_value("Job Offer", offer, "status"), "Awaiting Response")
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Shortlisted")
		self.assertEqual(self.get_stage(applicant)["stage"], "Offered")
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "stage"), "Offered")
		self.assert_interview_statuses(interviews)

	def test_set_offer_answer_decline_rejects_the_applicant_and_undo_restores(self):
		applicant = self.make_applicant("declines", status="Shortlisted")
		interviews = self.make_open_interviews(applicant)
		offer = self.make_offer(applicant, docstatus=1, applicant_email=applicant)

		result = set_offer_answer(offer, "Rejected")
		self.assertEqual(frappe.db.get_value("Job Offer", offer, "status"), "Rejected")
		# the offer's own hook marks the applicant rejected
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Rejected")
		self.assertEqual(self.get_stage(applicant)["stage"], "Rejected")
		self.assert_interview_statuses(dict(zip(interviews, ("Rejected", "Cancelled"), strict=True)))

		set_offer_answer(
			offer, result["previous_status"], result["previous_applicant_status"], result["closed_interviews"]
		)
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Shortlisted")
		self.assertEqual(self.get_stage(applicant)["stage"], "Offered")
		self.assert_interview_statuses(interviews)

	def test_offer_fact_follows_the_offer_status(self):
		offer = frappe._dict(docstatus=1, status="Ready to Send", offer_date=nowdate(), creation=nowdate())
		facts = {
			("Draft", 0): "Offer in draft",
			("Ready to Send", 1): "Offer ready to send",
		}
		for (status, docstatus), fact in facts.items():
			offer.update(status=status, docstatus=docstatus)
			self.assertEqual(get_offer_fact(offer), fact)
		offer.update(status="Awaiting Response", docstatus=1)
		self.assertTrue(get_offer_fact(offer).startswith("Offer sent"))

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
			result = set_offer_answer(offer, status)
			self.assertEqual(result["previous_status"], "Ready to Send")
			self.assertEqual(frappe.db.get_value("Job Offer", offer, "status"), status)
			self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), applicant_status)

	def test_set_offer_answer_from_awaiting_response_and_invalid_moves(self):
		applicant = self.make_applicant("awaiting-answer", status="Shortlisted")
		offer = self.make_offer(applicant, docstatus=1, applicant_email="awaiting@example.com")
		for status in ("Draft", "Cancelled", "Maybe"):
			with self.assertRaises(frappe.ValidationError):
				set_offer_answer(offer, status)
		set_offer_answer(offer, "Rejected")
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Rejected")
		# an answered offer can't be answered the other way, only undone
		with self.assertRaises(frappe.ValidationError):
			set_offer_answer(offer, "Accepted")

	def test_set_offer_answer_refuses_drafts_and_unsent_offers(self):
		applicant = self.make_applicant("draft-answer", status="Shortlisted")
		draft = self.make_offer(applicant, status="Draft", docstatus=0)
		with self.assertRaises(frappe.ValidationError):
			set_offer_answer(draft, "Accepted")

		other = self.make_applicant("unsent-answer", status="Shortlisted")
		unsent = self.make_offer(other, status="Ready to Send", docstatus=1, applicant_email="x@example.com")
		with self.assertRaises(frappe.ValidationError):
			set_offer_answer(unsent, "Maybe")
		self.assertEqual(frappe.db.get_value("Job Offer", unsent, "status"), "Ready to Send")

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
		result = reject_applicant(applicant, 1, "Your application", "Hi,\n\nSorry <b>no</b>.")
		return applicant, result

	def test_unanimous_rejecting_feedback_makes_the_interview_not_cleared(self):
		applicant = self.make_applicant("not-cleared", status="Shortlisted")
		interview = self.make_interview(
			applicant,
			status="Under Review",
			panel=["Administrator", INTERVIEWER],
			feedback_from=["Administrator"],
		)
		frappe.db.set_value("Interview Feedback", {"interview": interview}, "result", "Rejected")
		self.assertTrue(self.get_stage(applicant)["fact"].endswith("Not cleared"))

		# one clearing feedback among rejections keeps the usual flow
		self.make_feedback(interview, applicant, INTERVIEWER)
		frappe.db.set_value(
			"Interview Feedback",
			{"interview": interview, "interviewer": INTERVIEWER},
			"result",
			"Cleared",
		)
		self.assertNotIn("Not cleared", self.get_stage(applicant)["fact"])

	def test_reject_applicant_closes_open_interviews(self):
		applicant = self.make_applicant("closes-interviews", status="Shortlisted")
		with_feedback = self.make_saveable_interview(
			applicant, status="Under Review", panel=["Administrator"], feedback_from=["Administrator"]
		)
		without_feedback = self.make_saveable_interview(applicant, status="Pending", panel=())
		cleared = self.make_saveable_interview(applicant, status="Cleared")

		reject_applicant(applicant)

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

		result = reject_applicant(applicant)
		self.assertCountEqual(
			result["closed_interviews"],
			[
				{"name": with_feedback, "status": "Under Review"},
				{"name": without_feedback, "status": "Pending"},
			],
		)

		undo_reject_applicant(
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

		result = set_offer_answer(offer, "Rejected")
		set_offer_answer(
			offer, result["previous_status"], result["previous_applicant_status"], result["closed_interviews"]
		)

		self.assert_interview_statuses(interviews)
		self.assertEqual({name: self.get_interview_fields(name) for name in interviews}, before)

	def test_reject_and_undo_change_only_the_interview_status(self):
		applicant = self.make_applicant("reject-keeps-fields", status="Shortlisted")
		interviews = self.make_interviews_with_own_designation(applicant)
		before = {name: self.get_interview_fields(name) for name in interviews}

		result = reject_applicant(applicant)
		self.assertEqual({name: self.get_interview_fields(name) for name in interviews}, before)
		undo_reject_applicant(
			applicant, result["previous_status"], None, frappe.as_json(result["closed_interviews"])
		)

		self.assert_interview_statuses(interviews)
		self.assertEqual({name: self.get_interview_fields(name) for name in interviews}, before)

	def test_has_cleared_interview_counts_drafts_and_submitted_but_not_cancelled(self):
		none = self.make_applicant("cleared-none", status="Shortlisted")
		self.assertFalse(has_cleared_interview(none))
		self.assertEqual(get_offer_readiness(none)["needs_confirmation"], False)

		draft = self.make_applicant("cleared-draft", status="Shortlisted")
		self.make_saveable_interview(draft, status="Cleared")
		submitted = self.make_applicant("cleared-submitted", status="Shortlisted")
		self.make_saveable_interview(submitted, status="Cleared", docstatus=1)
		for applicant in (draft, submitted):
			self.assertTrue(has_cleared_interview(applicant))
			self.assertFalse(get_offer_readiness(applicant)["needs_confirmation"])

		pending = self.make_applicant("cleared-pending", status="Shortlisted")
		self.make_saveable_interview(pending, status="Pending")
		self.assertFalse(has_cleared_interview(pending))
		self.assertTrue(get_offer_readiness(pending)["needs_confirmation"])

		cancelled = self.make_applicant("cleared-cancelled", status="Shortlisted")
		self.make_saveable_interview(cancelled, status="Cancelled")
		self.assertFalse(get_offer_readiness(cancelled)["needs_confirmation"])

	def test_accepted_offer_closes_open_draft_interviews(self):
		applicant = self.make_applicant("accepts-closes", status="Shortlisted")
		with_feedback = self.make_saveable_interview(
			applicant, status="Under Review", panel=["Administrator"], feedback_from=["Administrator"]
		)
		without_feedback = self.make_saveable_interview(applicant, status="Pending", panel=())
		rejected = self.make_saveable_interview(applicant, status="Rejected")
		offer = self.make_offer(applicant, status="Awaiting Response", docstatus=1, applicant_email=applicant)

		set_offer_answer(offer, "Accepted")

		def status(name):
			return frappe.db.get_value("Interview", name, ["status", "docstatus"])

		self.assertEqual(status(with_feedback), ("Cleared", 0))
		self.assertEqual(status(without_feedback), ("Cancelled", 0))
		self.assertEqual(status(rejected), ("Rejected", 0))

	def test_unreject_returns_the_applicant_to_their_stage(self):
		applicant = self.make_applicant("moves-back", status="Shortlisted")
		reject_applicant(applicant)
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "stage"), "Rejected")

		set_applicant_status(applicant, "Open")
		self.assertEqual(
			frappe.db.get_value("Job Applicant", applicant, ["status", "stage"]), ("Open", "Applied")
		)

		interviewing = self.make_applicant("moves-back-interviewing", status="Shortlisted")
		self.make_saveable_interview(interviewing, status="Cleared")
		reject_applicant(interviewing)
		set_applicant_status(interviewing, "Open")
		self.assertEqual(frappe.db.get_value("Job Applicant", interviewing, "stage"), "Interviewing")

	def test_unreject_by_a_plain_save_reopens_the_interviews_the_reject_closed(self):
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

		reject_applicant(applicant)

		def status(name):
			return frappe.db.get_value("Interview", name, "status")

		self.assertEqual(status(with_feedback), "Rejected")
		self.assertEqual(status(without_feedback), "Cancelled")

		# a plain save, as the form or a Kanban drag does
		doc = frappe.get_doc("Job Applicant", applicant)
		doc.status = "Shortlisted"
		doc.save()

		self.assertEqual(status(with_feedback), "Under Review")
		self.assertEqual(status(without_feedback), "Pending")
		self.assertEqual(status(future), "Pending")
		self.assertEqual(status(cleared), "Cleared")
		self.assertEqual(status(submitted), "Cancelled")
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

		set_offer_answer(offer, "Rejected")

		def status(name):
			return frappe.db.get_value("Interview", name, ["status", "docstatus"])

		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Rejected")
		self.assertEqual(status(with_feedback), ("Rejected", 0))
		self.assertEqual(status(without_feedback), ("Cancelled", 0))

	def test_hired_drop_message_depends_on_a_live_offer(self):
		applicant = self.make_applicant("no-offer", status="Shortlisted")
		readiness = get_offer_readiness(applicant)
		self.assertFalse(readiness["has_live_offer"])
		self.assertFalse(readiness["has_accepted_offer"])

	def test_reject_applicant_sets_rejected_and_returns_previous_status(self):
		applicant = self.make_applicant("rejected", status="Shortlisted")
		result = reject_applicant(applicant)
		self.assertEqual(
			result, {"previous_status": "Shortlisted", "communication": None, "closed_interviews": []}
		)
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Rejected")
		self.assertFalse(frappe.db.exists("Communication", {"reference_name": applicant}))

	def test_reject_applicant_stores_the_reason_and_note(self):
		applicant = self.make_applicant("reasoned", status="Shortlisted")
		reject_applicant(applicant, reason="Withdrew", note="  Took another offer  ")
		values = frappe.db.get_value("Job Applicant", applicant, ["rejection_reason", "rejection_note"])
		self.assertEqual(values, ("Withdrew", "Took another offer"))
		# the stage card shows the reason
		self.assertEqual(self.get_stage(applicant)["fact"], "Withdrew")

	def test_undo_reject_and_unreject_clear_the_reason(self):
		def reason(name):
			return frappe.db.get_value("Job Applicant", name, ["rejection_reason", "rejection_note"])

		undone = self.make_applicant("undo-reason", status="Shortlisted")
		result = reject_applicant(undone, reason="No response", note="Silent")
		undo_reject_applicant(undone, result["previous_status"])
		self.assertEqual(reason(undone), (None, None))

		moved = self.make_applicant("back-reason", status="Shortlisted")
		reject_applicant(moved, reason="Not qualified", note="Too junior")
		set_applicant_status(moved, "Open")
		self.assertEqual(reason(moved), (None, None))

	def test_declined_offer_sets_the_reason_unless_one_is_given(self):
		applicant = self.make_applicant("declines-reason", status="Shortlisted")
		offer = self.make_offer(applicant, docstatus=1, applicant_email=applicant)
		result = set_offer_answer(offer, "Rejected")
		self.assertEqual(
			frappe.db.get_value("Job Applicant", applicant, "rejection_reason"), "Declined offer"
		)

		set_offer_answer(offer, result["previous_status"], result["previous_applicant_status"])
		self.assertIsNone(frappe.db.get_value("Job Applicant", applicant, "rejection_reason"))

		# a reason someone already gave stays
		frappe.db.set_value("Job Applicant", applicant, "rejection_reason", "Salary mismatch")
		set_offer_answer(offer, "Rejected")
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
		undone = undo_reject_applicant(applicant, result["previous_status"], result["communication"])
		self.assertEqual(undone, {"email_cancelled": True})
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Shortlisted")
		self.assertFalse(frappe.db.exists("Communication", result["communication"]))
		self.assertFalse(frappe.db.exists("Email Queue", {"communication": result["communication"]}))

	def test_undo_reject_leaves_a_sent_email_alone(self):
		applicant, result = self.reject_with_email()
		frappe.db.set_value("Email Queue", {"communication": result["communication"]}, "status", "Sent")
		undone = undo_reject_applicant(applicant, result["previous_status"], result["communication"])
		self.assertEqual(undone, {"email_cancelled": False})
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Shortlisted")
		self.assertTrue(frappe.db.exists("Communication", result["communication"]))

	def test_undo_reject_leaves_another_applicants_email_alone(self):
		_rejected, rejection = self.reject_with_email()
		applicant = self.make_applicant("undo-foreign", status="Rejected")
		undone = undo_reject_applicant(applicant, "Shortlisted", rejection["communication"])
		self.assertEqual(undone, {"email_cancelled": False})
		self.assertTrue(frappe.db.exists("Communication", rejection["communication"]))
		self.assertTrue(frappe.db.exists("Email Queue", {"communication": rejection["communication"]}))

	def test_undo_reject_without_email(self):
		applicant = self.make_applicant("undoplain", status="Open")
		reject_applicant(applicant)
		self.assertEqual(undo_reject_applicant(applicant, "Open"), {"email_cancelled": False})
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Open")

	def test_reject_and_undo_require_write_access(self):
		applicant = self.make_applicant("guarded-reject", status="Open")
		frappe.set_user(NO_ROLE_USER)
		self.assertRaises(frappe.PermissionError, reject_applicant, applicant)
		self.assertRaises(frappe.PermissionError, undo_reject_applicant, applicant, "Open")
		frappe.set_user("Administrator")
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Open")

	def test_email_sender_prefers_hr_settings_hiring_sender_email(self):
		applicant = self.make_applicant("sender")
		self.make_outgoing_account()
		self.assertEqual(get_reject_details(applicant)["email_sender"], "hiring.outgoing@example.com")
		frappe.db.set_single_value("HR Settings", "hiring_sender_email", "careers@example.com")
		self.assertEqual(get_email_setup()["email_sender"], "careers@example.com")

	def test_reject_details_have_opening_title_and_company(self):
		result = get_reject_details(self.make_applicant("titled"))
		self.assertEqual((result["job_title"], result["company"]), ("Hiring Test Opening", self.company))

	def test_opening_header_adds_location_only_when_an_open_role_shares_the_name(self):
		for location in ("Pune", "Bengaluru", "Mumbai"):
			if not frappe.db.exists("Branch", location):
				frappe.get_doc({"doctype": "Branch", "branch": location}).insert(ignore_permissions=True)
		alone = self.make_opening("Only Role", location="Pune")
		self.assertEqual(get_opening_header(alone.name)["display_title"], "Only Role")
		first = self.make_opening("Twin Role", location="Bengaluru")
		second = self.make_opening("Twin Role", location="Mumbai", route="jobs/twin-role-mumbai")
		self.assertEqual(get_opening_header(first.name)["display_title"], "Twin Role · Bengaluru")
		self.assertEqual(get_opening_header(second.name)["display_title"], "Twin Role · Mumbai")
		second.db_set("status", "Closed")
		self.assertEqual(get_opening_header(first.name)["display_title"], "Twin Role")
		self.assertEqual(get_opening_header(second.name)["status"], "Closed")
