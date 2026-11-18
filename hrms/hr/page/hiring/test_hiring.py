import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, get_datetime, nowdate

from hrms.hr.doctype.job_applicant.job_applicant import get_applicant_stage, reject_applicant
from hrms.hr.doctype.job_applicant.stage_info import APPLICANT_FIELDS
from hrms.hr.page.hiring import applicant as applicant_api
from hrms.hr.page.hiring import hiring, overview
from hrms.tests import test_hiring_flow
from hrms.tests.test_hiring_flow import HR_USER, INTERVIEWER, NO_ROLE_USER


class TestHiring(IntegrationTestCase):
	# the flow's fixtures; kept off the module, so the runner doesn't collect the flow's tests here too
	Flow = test_hiring_flow.TestHiringFlow
	setUp = Flow.setUp
	make_opening = Flow.make_opening
	make_applicant = Flow.make_applicant
	make_employee = Flow.make_employee
	make_offer = Flow.make_offer
	make_interview = Flow.make_interview
	make_saveable_interview = Flow.make_saveable_interview
	make_feedback = Flow.make_feedback
	write = Flow.write

	def get_stage(self, applicant):
		return get_applicant_stage(applicant)

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

	def get_stages(self, *names):
		applicants = frappe.get_list(
			"Job Applicant", filters={"name": ["in", names]}, fields=APPLICANT_FIELDS
		)
		return hiring.get_applicant_stages(applicants)

	def test_pipeline_counts_rows_and_search(self):
		self.make_applicant("alpha")
		self.make_applicant("beta")
		self.make_applicant("gamma", status="Rejected")
		self.make_applicant("delta", status="Shortlisted")
		self.make_offer(self.make_applicant("epsilon"))

		result = hiring.get_pipeline(self.opening.name)
		self.assertEqual(
			result["counts"],
			{"Applied": 2, "Shortlisted": 1, "Interviewing": 0, "Offered": 1, "Hired": 0, "Rejected": 1},
		)
		self.assertEqual(result["total"], 2)
		self.assertEqual({row["applicant_name"] for row in result["rows"]}, {"Alpha", "Beta"})
		self.assertEqual(result["opening"]["name"], self.opening.name)
		self.assertEqual(result["opening"]["designation"], "Researcher")

		searched = hiring.get_pipeline(self.opening.name, search="ALP")
		self.assertEqual([row["applicant_name"] for row in searched["rows"]], ["Alpha"])
		self.assertEqual(searched["total"], 1)
		self.assertEqual(searched["counts"]["Applied"], 2)

		by_email = hiring.get_pipeline(self.opening.name, search="hiring-beta@")
		self.assertEqual([row["applicant_name"] for row in by_email["rows"]], ["Beta"])

		rejected = hiring.get_pipeline(self.opening.name, stage="Rejected")
		self.assertEqual([row["applicant_name"] for row in rejected["rows"]], ["Gamma"])

	def test_pipeline_search_is_literal_text(self):
		self.make_applicant("percent")
		self.assertEqual(hiring.get_pipeline(self.opening.name, "Applied", search="%")["total"], 0)
		self.assertEqual(hiring.get_pipeline(self.opening.name, "Applied", search="PERC")["total"], 1)

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
		self.assertEqual(filtered["counts"]["Applied"], 4)
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

		result = hiring.get_pipeline(self.opening.name, stage="Interviewing", sort="oldest")
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

		result = hiring.get_pipeline(self.opening.name, stage="Interviewing", page_length=2)
		self.assertEqual([row["name"] for row in result["rows"]], [second, first])
		self.assertEqual(
			[(group["group"], group["count"]) for group in result["groups"]],
			[("cleared", 2), ("scheduled", 1)],
		)

	def test_interviewing_without_a_readable_interview_is_listed_and_opens(self):
		# the stage is stored, the interview may be one the user can't read
		hidden = self.make_applicant("hidden-interview")
		frappe.db.set_value("Job Applicant", hidden, "stage", "Interviewing")

		result = hiring.get_pipeline(self.opening.name, stage="Interviewing")
		self.assertEqual(result["total"], 1)
		row = result["rows"][0]
		self.assertEqual((row["name"], row["group"], row["group_fact"]), (hidden, "scheduled", row["fact"]))
		self.assertEqual(result["groups"], [{"group": "scheduled", "label": "Scheduled", "count": 1}])

		detail = applicant_api.get_applicant(hidden)
		self.assertEqual(detail["stage"], "Interviewing")
		self.assertIsNone(detail["current_interview"])
		self.assertTrue(detail["stage_since"])

	def test_other_stages_have_no_groups(self):
		self.make_applicant("plain")
		result = hiring.get_pipeline(self.opening.name)
		self.assertEqual(result["groups"], [])
		self.assertIsNone(result["rows"][0]["group"])

	def test_pipeline_rejects_unknown_stage(self):
		self.assertRaises(frappe.ValidationError, hiring.get_pipeline, self.opening.name, "nonsense")

	def get_opening_row(self, opening):
		return next(o for o in overview.get_overview()["openings"] if o["name"] == opening.name)

	def test_needs_you_is_none_when_nothing_is_stuck(self):
		self.make_applicant("review-only")
		self.assertIsNone(self.get_opening_row(self.opening)["needs_you"])
		self.assertIsNone(self.get_opening_row(self.make_opening("Hiring Test Empty"))["needs_you"])

	def test_needs_you_picks_the_most_urgent_stuck_entry(self):
		overdue = self.make_applicant("overdue")
		self.make_interview(
			overdue, status="Under Review", days_ago=3, panel=[INTERVIEWER, HR_USER], feedback_from=[HR_USER]
		)
		self.make_applicant("schedule", status="Shortlisted")
		self.assertEqual(
			self.get_opening_row(self.opening)["needs_you"],
			{"label": "1 feedback due", "kind": "feedback", "stage": "Interviewing", "is_late": True},
		)

	def test_needs_you_ignores_review_schedule_and_onboard(self):
		self.make_applicant("schedule", status="Shortlisted")
		done = self.make_applicant("done", status="Accepted")
		self.make_offer(done, status="Accepted", docstatus=1)
		self.assertIsNone(self.get_opening_row(self.opening)["needs_you"])

	def test_needs_you_is_not_late_for_ready_for_offer(self):
		cleared = self.make_applicant("make-offer", status="Shortlisted")
		self.make_interview(cleared, status="Cleared", days_ago=1, docstatus=1, panel=[INTERVIEWER])
		self.assertEqual(
			self.get_opening_row(self.opening)["needs_you"],
			{"label": "1 ready for offer", "kind": "offer", "stage": "Interviewing", "is_late": False},
		)

	def test_needs_you_unanswered_offer_is_late_and_points_at_offered(self):
		silent = self.make_applicant("silent")
		self.make_offer(silent, docstatus=1, offer_date=add_days(nowdate(), -9))
		needs_you = self.get_opening_row(self.opening)["needs_you"]
		self.assertEqual(
			(needs_you["label"], needs_you["stage"], needs_you["is_late"]),
			("1 offer awaiting reply", "Offered", True),
		)

	def test_needs_you_filled_opening_with_offers_out_comes_first(self):
		opening = self.make_opening("Hiring Test Filled", vacancies=1)
		hired = self.make_applicant("hired", status="Accepted", opening=opening)
		self.make_offer(hired, status="Accepted", docstatus=1)
		self.make_employee("Hired", hired)
		out = self.make_applicant("still-out", opening=opening)
		self.make_offer(out, docstatus=1, offer_date=nowdate())
		self.assertEqual(
			self.get_opening_row(opening)["needs_you"],
			{"label": "1 offer still out", "kind": "offers_out", "stage": "Offered", "is_late": True},
		)

	def test_overview_counts_submitted_unanswered_offers_as_out(self):
		for label, status, docstatus in (
			("out-ready", "Ready to Send", 1),
			("out-sent", "Awaiting Response", 1),
			("out-draft", "Draft", 0),
			("out-accepted", "Accepted", 1),
		):
			applicant = self.make_applicant(label, status="Shortlisted")
			self.make_offer(applicant, status=status, docstatus=docstatus)
		self.assertEqual(self.get_opening_row(self.opening)["offers_out"], 2)

	def test_overview_opening_summary_and_attention_order(self):
		self.make_applicant("new-one")
		self.make_applicant("new-two")
		self.make_applicant("ready", status="Shortlisted")
		self.make_applicant("done", status="Accepted")
		overdue = self.make_applicant("overdue")
		self.make_interview(
			overdue, status="Under Review", days_ago=3, panel=[INTERVIEWER, HR_USER], feedback_from=[HR_USER]
		)
		complete = self.make_applicant("complete")
		self.make_interview(
			complete, status="Under Review", days_ago=1, panel=[INTERVIEWER], feedback_from=[INTERVIEWER]
		)

		opening = self.get_opening_row(self.opening)
		self.assertEqual((opening["applicants"], opening["new"], opening["hired"]), (6, 2, 0))
		self.assertEqual(opening["vacancies"], 2)
		self.assertEqual(
			opening["attention"],
			[
				{"kind": "feedback", "count": 1},
				{"kind": "decide", "count": 1},
				{"kind": "schedule", "count": 2},
				{"kind": "review", "count": 2},
			],
		)
		self.assertEqual(opening["attention_stage"], "Interviewing")
		self.assertTrue(opening["is_overdue"])

	def test_overview_attention_without_overdue_points_at_first_stage(self):
		self.make_applicant("fresh")
		opening = self.get_opening_row(self.opening)
		self.assertEqual(opening["attention"], [{"kind": "review", "count": 1}])
		self.assertEqual(opening["attention_stage"], "Applied")
		self.assertFalse(opening["is_overdue"])

	def test_overview_opening_without_attention_has_none(self):
		opening = self.get_opening_row(self.opening)
		self.assertEqual(
			(opening["attention"], opening["attention_stage"], opening["is_overdue"]), ([], None, False)
		)

	def test_overview_offer_attention_maps_to_its_opening(self):
		other = self.make_opening("Hiring Test Other")
		cleared = self.make_applicant("make-offer", status="Shortlisted")
		self.make_interview(cleared, status="Cleared", days_ago=1, docstatus=1, panel=[INTERVIEWER])
		silent = self.make_applicant("silent", opening=other)
		self.make_offer(silent, docstatus=1, offer_date=add_days(nowdate(), -9))
		accepted = self.make_applicant("accepted", status="Accepted", opening=other)
		self.make_offer(accepted, status="Accepted", docstatus=1)

		mine = self.get_opening_row(self.opening)
		self.assertEqual(mine["attention"], [{"kind": "offer", "count": 1}])
		theirs = self.get_opening_row(other)
		self.assertEqual(
			theirs["attention"], [{"kind": "no_reply", "count": 1}, {"kind": "onboard", "count": 1}]
		)
		self.assertEqual(theirs["attention_stage"], "Offered")
		self.assertTrue(theirs["is_overdue"])

		self.make_employee("Joiner", accepted)
		self.assertEqual(self.get_opening_row(other)["attention"], [{"kind": "no_reply", "count": 1}])

	def test_overview_sorts_open_openings_by_overdue_then_closing_date_then_volume(self):
		soon = self.make_opening("Hiring Test Soon", closes_on=add_days(nowdate(), 3))
		later = self.make_opening("Hiring Test Later", closes_on=add_days(nowdate(), 30))
		busy = self.make_opening("Hiring Test Busy")
		quiet = self.make_opening("Hiring Test Quiet")
		late = self.make_opening("Hiring Test Late Overdue", closes_on=add_days(nowdate(), 90))
		for index in range(2):
			self.make_applicant(f"busy-{index}", opening=busy)
		self.make_applicant("quiet-0", opening=quiet)
		silent = self.make_applicant("silent", opening=late)
		self.make_offer(silent, docstatus=1, offer_date=add_days(nowdate(), -9))

		names = [o["name"] for o in overview.get_overview()["openings"]]
		order = [late.name, soon.name, later.name, busy.name, quiet.name]
		self.assertEqual([n for n in names if n in order], order)

	def test_overview_orders_open_before_closed(self):
		closed = self.make_opening("Hiring Test Closed", status="Closed", closed_on=nowdate())
		names = [o["name"] for o in overview.get_overview()["openings"]]
		self.assertLess(names.index(self.opening.name), names.index(closed.name))

	def test_closed_opening_with_candidates_in_play_is_flagged_active(self):
		live = self.make_opening("Hiring Test Closed Live")
		self.make_interview(self.make_applicant("live-one", opening=live), days_ago=-1, panel=[INTERVIEWER])
		offered = self.make_opening("Hiring Test Closed Offered")
		self.make_offer(self.make_applicant("offered-one", opening=offered))
		quiet = self.make_opening("Hiring Test Closed Quiet")
		self.make_applicant("quiet-applied", opening=quiet)
		self.make_applicant("quiet-rejected", status="Rejected", opening=quiet)
		# applicants can't be added to a closed opening, so close them once they are in
		for opening, days in ((live, 1), (offered, 2), (quiet, 3)):
			frappe.db.set_value(
				"Job Opening", opening.name, {"status": "Closed", "closed_on": add_days(nowdate(), days)}
			)

		rows = {o["name"]: o for o in overview.get_overview()["openings"]}
		self.assertEqual(rows[live.name]["active"], 1)
		self.assertEqual(rows[offered.name]["active"], 1)
		self.assertEqual(rows[quiet.name]["active"], 0)

		names = list(rows)
		self.assertLess(names.index(self.opening.name), names.index(offered.name))
		# live closed ones follow the open ones, most recently closed first; quiet ones come last
		self.assertLess(names.index(offered.name), names.index(live.name))
		self.assertLess(names.index(live.name), names.index(quiet.name))

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
		for user in (NO_ROLE_USER, INTERVIEWER):
			frappe.set_user(user)
			self.assertRaises(frappe.PermissionError, overview.get_overview)
			self.assertRaises(frappe.PermissionError, hiring.get_pipeline, self.opening.name)

	def test_applicant_detail_fields_stage_and_empty_children(self):
		if not frappe.db.exists("Job Applicant Source", "LinkedIn"):
			frappe.get_doc({"doctype": "Job Applicant Source", "source_name": "LinkedIn"}).insert()
		applicant = self.make_applicant(
			"detail", status="Hold", source="LinkedIn", phone_number="9876543210", cover_letter="Hello"
		)

		result = applicant_api.get_applicant(applicant)
		self.assertEqual(result["name"], applicant)
		self.assertEqual(result["applicant_name"], "Detail")
		self.assertEqual((result["stage"], result["stage_label"]), ("Applied", "Applied"))
		self.assertEqual(result["fact"], "LinkedIn")
		self.assertTrue(result["on_hold"])
		self.assertEqual(result["job_opening"], self.opening.name)
		self.assertEqual((result["job_title"], result["company"]), (self.opening.job_title, self.company))
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
		self.assertEqual(result["stage"], "Interviewing")
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
		self.assertEqual(result["stage"], "Hired")
		self.assertEqual(result["offer"]["name"], offer)
		self.assertEqual(result["offer"]["status"], "Accepted")
		self.assertIsNone(result["onboarding"])

		onboarding = self.make_onboarding(applicant)
		self.assertEqual(applicant_api.get_applicant(applicant)["onboarding"], onboarding)

	def test_applicant_detail_can_make_offer(self):
		applicant = self.make_applicant("cleared-detail", status="Shortlisted")
		self.make_interview(applicant, status="Cleared", days_ago=1, docstatus=1, panel=[INTERVIEWER])
		self.assertTrue(applicant_api.get_applicant(applicant)["can_make_offer"])

	def test_draft_cleared_interview_can_make_offer(self):
		applicant = self.make_applicant("cleared-draft", status="Shortlisted")
		self.make_interview(applicant, status="Cleared", days_ago=1, docstatus=0, panel=[INTERVIEWER])
		self.assertTrue(applicant_api.get_applicant(applicant)["can_make_offer"])

	def test_can_make_offer_only_while_the_latest_interview_is_cleared_and_no_offer_exists(self):
		offered = self.make_applicant("cleared-then-offered", status="Shortlisted")
		self.make_interview(offered, status="Cleared", days_ago=1, docstatus=1, panel=[INTERVIEWER])
		self.assertTrue(self.get_stages(offered)[offered]["can_make_offer"])
		self.make_offer(offered)
		self.assertFalse(self.get_stages(offered)[offered]["can_make_offer"])

		next_round = self.make_applicant("cleared-then-next-round", status="Shortlisted")
		self.make_interview(next_round, status="Cleared", days_ago=5, docstatus=1)
		self.make_interview(next_round, status="Pending", days_ago=-2)
		self.assertFalse(self.get_stages(next_round)[next_round]["can_make_offer"])

	def test_on_hold_follows_the_status(self):
		open_, held = self.make_applicant("not-held"), self.make_applicant("held", status="Hold")
		stages = self.get_stages(open_, held)
		self.assertEqual((stages[open_]["on_hold"], stages[held]["on_hold"]), (False, True))

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
		self.assertEqual(self.get_stage(applicant)["stage"], "Interviewing")

		applicant_api.set_interview_result(interview, "Cancelled")
		self.assertEqual(self.get_stage(applicant)["stage"], "Shortlisted")
		self.assertFalse(self.get_stages(applicant)[applicant]["can_make_offer"])
		listed = applicant_api.get_applicant(applicant)["interviews"]
		self.assertEqual([(row["name"], row["status"]) for row in listed], [(interview, "Cancelled")])

		applicant_api.set_interview_result(interview, "Pending")
		self.assertEqual(self.get_stage(applicant)["stage"], "Interviewing")

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
		self.assertEqual((result["stage"], result["stage_since"]), ("Shortlisted", get_datetime(changed_on)))

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

	def test_move_back_returns_a_rejected_applicant_to_their_stage(self):
		applicant = self.make_applicant("moves-back", status="Shortlisted")
		reject_applicant(applicant)
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "stage"), "Rejected")

		result = applicant_api.move_back_applicant(applicant)
		self.assertEqual(result, {"stage": "Applied", "stage_label": "Applied"})
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant, "status"), "Open")

		with self.assertRaises(frappe.ValidationError):
			applicant_api.move_back_applicant(applicant)

		interviewing = self.make_applicant("moves-back-interviewing", status="Shortlisted")
		self.make_saveable_interview(interviewing, status="Cleared")
		reject_applicant(interviewing)
		self.assertEqual(applicant_api.move_back_applicant(interviewing)["stage"], "Interviewing")

	def get_status_and_stage(self, applicant):
		return frappe.db.get_value("Job Applicant", applicant, ["status", "stage"])

	def test_shortlist_and_undo_restore_the_status_and_stage(self):
		applicant = self.make_applicant("to-shortlist")
		self.assertEqual(applicant_api.shortlist_applicant(applicant), {"previous_status": "Open"})
		self.assertEqual(self.get_status_and_stage(applicant), ("Shortlisted", "Shortlisted"))

		applicant_api.undo_shortlist_applicant(applicant, "Open")
		self.assertEqual(self.get_status_and_stage(applicant), ("Open", "Applied"))

	def test_undo_shortlist_keeps_an_applicant_held_in_applied_in_applied(self):
		applicant = self.make_applicant("held-shortlist", status="Hold")
		previous_status = applicant_api.shortlist_applicant(applicant)["previous_status"]
		self.assertEqual(self.get_status_and_stage(applicant), ("Shortlisted", "Shortlisted"))

		applicant_api.undo_shortlist_applicant(applicant, previous_status)
		self.assertEqual(self.get_status_and_stage(applicant), ("Hold", "Applied"))

	def test_shortlist_and_undo_require_write_access(self):
		applicant = self.make_applicant("guarded-shortlist")
		frappe.set_user(NO_ROLE_USER)
		self.assertRaises(frappe.PermissionError, applicant_api.shortlist_applicant, applicant)
		self.assertRaises(frappe.PermissionError, applicant_api.undo_shortlist_applicant, applicant, "Open")
		frappe.set_user("Administrator")
		self.assertEqual(self.get_status_and_stage(applicant), ("Open", "Applied"))

	def test_pipeline_page_grows_to_take_in_the_linked_applicant(self):
		names = [self.make_applicant(f"linked-{index}") for index in range(5)]
		for index, name in enumerate(names):
			frappe.db.set_value("Job Applicant", name, "creation", add_days(nowdate(), -index))

		def rows(applicant):
			result = hiring.get_pipeline(self.opening.name, page_length=2, applicant=applicant)
			return [row["name"] for row in result["rows"]]

		# newest first, the oldest is on the third page of two
		self.assertEqual(rows(names[4]), names)
		self.assertEqual(rows(names[1]), names[:2])
		self.assertEqual(rows(self.make_applicant("elsewhere", status="Shortlisted")), names[:2])

	def test_interviewing_page_grows_to_take_in_the_linked_applicant(self):
		names = [self.make_applicant(f"linked-round-{index}") for index in range(3)]
		for name in names:
			self.make_interview(name, days_ago=-1, panel=[INTERVIEWER])

		def rows(applicant):
			result = hiring.get_pipeline(
				self.opening.name, stage="Interviewing", page_length=1, applicant=applicant
			)
			return [row["name"] for row in result["rows"]]

		last = hiring.get_pipeline(self.opening.name, stage="Interviewing")["rows"][-1]["name"]
		self.assertEqual(len(rows(None)), 1)
		self.assertEqual(len(rows(last)), 3)

	def test_upcoming_interviews_window_ordering_limit_and_cancelled(self):
		interviews = {}
		for label, offset, time in (
			("later", 3, "09:00:00"),
			("late-today", 0, "15:00:00"),
			("early-today", 0, "09:30:00"),
			("outside", 7, "09:00:00"),
			("past", -1, "09:00:00"),
			("cancelled", 1, "09:00:00"),
			("finished-today", 0, "00:00:00"),
		):
			applicant = self.make_applicant(f"upcoming-{label}", status="Shortlisted")
			interview = self.make_saveable_interview(
				applicant, panel=[INTERVIEWER] if label == "later" else ()
			)
			frappe.db.set_value(
				"Interview",
				interview,
				{
					"scheduled_on": add_days(nowdate(), offset),
					"from_time": time,
					"to_time": "00:01:00" if label == "finished-today" else "23:59:00",
					"status": "Cancelled" if label == "cancelled" else "Pending",
				},
			)
			interviews[label] = interview

		result = overview.get_upcoming_interviews(limit=100)
		ours = [row for row in result["interviews"] if row["name"] in interviews.values()]
		self.assertEqual(
			[row["name"] for row in ours],
			[interviews["early-today"], interviews["late-today"], interviews["later"]],
		)
		first = ours[0]
		self.assertEqual(first["opening_title"], "Hiring Test Opening")
		self.assertEqual(first["job_opening"], self.opening.name)
		self.assertEqual(first["stage"], "Interviewing")
		self.assertEqual(first["panel"], [])
		self.assertEqual(
			ours[2]["panel"],
			[{"user": INTERVIEWER, "full_name": frappe.db.get_value("User", INTERVIEWER, "full_name")}],
		)

		self.assertLessEqual(len(overview.get_upcoming_interviews()["interviews"]), 6)
		limited = overview.get_upcoming_interviews(limit=1)
		self.assertEqual(len(limited["interviews"]), 1)
		self.assertEqual(limited["count"], result["count"])
		self.assertGreaterEqual(result["count"], 3)

		wider = overview.get_upcoming_interviews(days=8, limit=100)
		self.assertIn(interviews["outside"], [row["name"] for row in wider["interviews"]])
		self.assertNotIn(interviews["cancelled"], [row["name"] for row in wider["interviews"]])
		self.assertNotIn(interviews["past"], [row["name"] for row in wider["interviews"]])
		self.assertNotIn(interviews["finished-today"], [row["name"] for row in wider["interviews"]])

	def test_upcoming_interviews_needs_applicant_access(self):
		frappe.set_user(NO_ROLE_USER)
		self.assertRaises(frappe.PermissionError, overview.get_upcoming_interviews)
