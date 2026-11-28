# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.desk.doctype.kanban_board.kanban_board import update_order, update_order_for_single_card

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.interview.test_interview import create_interview_and_dependencies, create_interview_type
from hrms.hr.doctype.job_applicant.job_applicant import create_interview, get_stage
from hrms.hr.doctype.job_applicant.job_applicant import make_employee as map_applicant_to_employee
from hrms.hr.doctype.job_offer.test_job_offer import create_job_offer
from hrms.hr.doctype.job_opening.test_job_opening import get_job_opening
from hrms.patches.v16_0.set_job_applicant_stage import execute as set_job_applicant_stage
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


class TestJobApplicantStage(HRMSTestSuite):
	def setUp(self):
		super().setUp()
		frappe.db.set_single_value("HR Settings", "check_vacancies", 0)

	def make_applicant(self, key: str, status: str = "Open"):
		return create_job_applicant(email_id=f"stage_{key}@example.com", status=status)

	def make_offer(self, applicant, status: str = "Draft", submit: bool = False):
		offer = create_job_offer(job_applicant=applicant.name, status=status)
		offer.save()
		if submit:
			offer.submit()
		return offer

	def stored_stage(self, applicant) -> str:
		return frappe.db.get_value("Job Applicant", applicant.name, "stage")

	def rules_stage(self, applicant) -> str:
		return get_stage(frappe.get_doc("Job Applicant", applicant.name))

	def move_to(self, applicant, stage: str):
		applicant.reload()
		applicant.stage = stage
		applicant.save()
		applicant.reload()

	def test_stage_follows_status(self):
		applicant = self.make_applicant("status")
		self.assertEqual(applicant.stage, "Applied")

		for status, stage in (
			("Replied", "Applied"),
			("Hold", "Applied"),
			("Shortlisted", "Shortlisted"),
			("Accepted", "Shortlisted"),
			("Rejected", "Rejected"),
			("Open", "Applied"),
		):
			applicant.status = status
			applicant.save()
			self.assertEqual(applicant.stage, stage, status)
			self.assertEqual(self.rules_stage(applicant), stage, status)

	def test_rejected_wins_over_everything(self):
		applicant = self.make_applicant("rejected_wins")
		create_interview_and_dependencies(applicant.name)
		self.make_offer(applicant)

		applicant.reload()
		applicant.status = "Rejected"
		applicant.save()
		self.assertEqual(applicant.stage, "Rejected")

	def test_interview_makes_interviewing(self):
		applicant = self.make_applicant("interviewing", status="Shortlisted")
		self.assertEqual(applicant.stage, "Shortlisted")

		interview = create_interview_and_dependencies(applicant.name)
		self.assertEqual(self.rules_stage(applicant), "Interviewing")

		interview.db_set("status", "Cancelled")
		self.assertEqual(self.rules_stage(applicant), "Shortlisted")

	def test_draft_offer_makes_offered(self):
		applicant = self.make_applicant("draft_offer")
		self.make_offer(applicant)
		self.assertEqual(self.rules_stage(applicant), "Offered")

	def test_rejected_or_cancelled_offer_is_not_offered(self):
		applicant = self.make_applicant("rejected_offer")
		offer = self.make_offer(applicant, status="Rejected")
		self.assertEqual(self.rules_stage(applicant), "Applied")

		offer.status = "Cancelled"
		offer.save()
		self.assertEqual(self.rules_stage(applicant), "Applied")

	def test_offer_wins_over_interview(self):
		applicant = self.make_applicant("offer_over_interview")
		create_interview_and_dependencies(applicant.name)
		self.make_offer(applicant)
		self.assertEqual(self.rules_stage(applicant), "Offered")

	def test_accepted_offer_makes_hired(self):
		applicant = self.make_applicant("accepted_offer")
		self.make_offer(applicant, status="Accepted", submit=True)
		self.assertEqual(self.rules_stage(applicant), "Hired")

	def test_draft_accepted_offer_is_not_hired(self):
		applicant = self.make_applicant("draft_accepted_offer")
		self.make_offer(applicant, status="Accepted")
		self.assertEqual(self.rules_stage(applicant), "Applied")

	def test_employee_makes_hired(self):
		applicant = self.make_applicant("employee")
		make_employee(user=applicant.name, job_applicant=applicant.name, company="_Test Company")
		self.assertEqual(self.rules_stage(applicant), "Hired")
		self.assertEqual(self.stored_stage(applicant), "Hired")

	def test_hired_sets_status_accepted(self):
		applicant = self.make_applicant("hired_status")
		self.make_offer(applicant, status="Accepted", submit=True)
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant.name, "status"), "Accepted")

		other = self.make_applicant("hired_status_employee")
		make_employee(user=other.name, job_applicant=other.name, company="_Test Company")
		self.assertEqual(frappe.db.get_value("Job Applicant", other.name, "status"), "Accepted")

	def test_rejected_sets_status_rejected(self):
		applicant = self.make_applicant("rejected_status")
		self.move_to(applicant, "Rejected")
		self.assertEqual(applicant.status, "Rejected")

	def test_hold_survives_a_save_and_keeps_the_stage(self):
		for stage in ("Applied", "Shortlisted"):
			applicant = self.make_applicant(f"hold_{stage}")
			self.move_to(applicant, stage)
			applicant.put_on_hold()
			applicant.reload()
			self.assertEqual((applicant.status, applicant.stage), ("Hold", stage))

			applicant.notes = "Called back"
			applicant.save()
			self.assertEqual((applicant.status, applicant.stage), ("Hold", stage))

	def test_hold_keeps_interviewing(self):
		applicant = self.make_applicant("hold_interview")
		create_interview_and_dependencies(applicant.name)
		applicant.reload()
		applicant.put_on_hold()
		applicant.reload()
		self.assertEqual((applicant.status, applicant.stage), ("Hold", "Interviewing"))

	def test_resume_goes_back_to_the_status_of_the_stage(self):
		applicant = self.make_applicant("resume_applied")
		applicant.put_on_hold()
		applicant.reload()
		applicant.resume()
		applicant.reload()
		self.assertEqual((applicant.status, applicant.stage), ("Open", "Applied"))

		applicant = self.make_applicant("resume_shortlisted", status="Shortlisted")
		applicant.put_on_hold()
		applicant.reload()
		applicant.resume()
		applicant.reload()
		self.assertEqual((applicant.status, applicant.stage), ("Shortlisted", "Shortlisted"))

	def test_rejected_and_hired_cannot_be_put_on_hold(self):
		rejected = self.make_applicant("hold_rejected", status="Rejected")
		self.assertRaises(frappe.ValidationError, rejected.put_on_hold)

		hired = self.make_applicant("hold_hired")
		self.make_offer(hired, status="Accepted", submit=True)
		hired.reload()
		self.assertRaises(frappe.ValidationError, hired.put_on_hold)

	def test_manual_move_while_on_hold_clears_the_hold(self):
		applicant = self.make_applicant("hold_move")
		applicant.put_on_hold()
		self.move_to(applicant, "Shortlisted")
		self.assertEqual((applicant.status, applicant.stage), ("Shortlisted", "Shortlisted"))

	def test_stage_syncs_with_interview(self):
		applicant = self.make_applicant("sync_interview")
		self.assertEqual(self.stored_stage(applicant), "Applied")

		interview = create_interview_and_dependencies(applicant.name)
		self.assertEqual(self.stored_stage(applicant), "Interviewing")

		interview.status = "Cleared"
		interview.save()
		interview.submit()
		self.assertEqual(self.stored_stage(applicant), "Interviewing")

		interview.cancel()
		self.assertEqual(self.stored_stage(applicant), "Applied")

	def test_stage_syncs_when_interview_is_deleted(self):
		applicant = self.make_applicant("sync_interview_delete")
		interview = create_interview_and_dependencies(applicant.name)
		self.assertEqual(self.stored_stage(applicant), "Interviewing")

		frappe.delete_doc("Interview", interview.name, force=True)
		self.assertEqual(self.stored_stage(applicant), "Applied")

	def test_stage_syncs_with_job_offer(self):
		applicant = self.make_applicant("sync_offer", status="Shortlisted")

		offer = self.make_offer(applicant)
		self.assertEqual(self.stored_stage(applicant), "Offered")

		offer.submit()
		self.assertEqual(self.stored_stage(applicant), "Offered")

		offer.db_set("status", "Awaiting Response")
		self.assertEqual(self.stored_stage(applicant), "Offered")

		offer.reload()
		offer.status = "Accepted"
		offer.save()
		self.assertEqual(self.stored_stage(applicant), "Hired")

		offer.cancel()
		self.assertEqual(self.stored_stage(applicant), "Shortlisted")

	def test_stage_syncs_when_offer_is_rejected_or_deleted(self):
		applicant = self.make_applicant("sync_offer_rejected")
		offer = self.make_offer(applicant)
		self.assertEqual(self.stored_stage(applicant), "Offered")

		offer.status = "Rejected"
		offer.save()
		self.assertEqual(self.stored_stage(applicant), "Applied")

		offer.status = "Draft"
		offer.save()
		self.assertEqual(self.stored_stage(applicant), "Offered")

		frappe.delete_doc("Job Offer", offer.name, force=True)
		self.assertEqual(self.stored_stage(applicant), "Applied")

	def test_repointed_interview_moves_both_applicants(self):
		first = self.make_applicant("repoint_interview_first")
		second = self.make_applicant("repoint_interview_second")
		interview = create_interview_and_dependencies(first.name)
		self.assertEqual(self.stored_stage(first), "Interviewing")

		interview.reload()
		interview.job_applicant = second.name
		interview.save()
		self.assertEqual((self.stored_stage(first), self.stored_stage(second)), ("Applied", "Interviewing"))

	def test_repointed_offer_moves_both_applicants(self):
		first = self.make_applicant("repoint_offer_first")
		second = self.make_applicant("repoint_offer_second")
		offer = self.make_offer(first)
		self.assertEqual(self.stored_stage(first), "Offered")

		offer.job_applicant = second.name
		offer.save()
		self.assertEqual((self.stored_stage(first), self.stored_stage(second)), ("Applied", "Offered"))

	def test_held_applicant_falls_back_to_shortlisted_when_the_interview_or_offer_goes(self):
		interviewed = self.make_applicant("hold_interview_gone")
		interview = create_interview_and_dependencies(interviewed.name)
		interviewed.reload()
		interviewed.put_on_hold()
		interview.reload()
		interview.status = "Cancelled"
		interview.save()
		interviewed.reload()
		self.assertEqual((interviewed.status, interviewed.stage), ("Hold", "Shortlisted"))

		offered = self.make_applicant("hold_offer_gone")
		offer = self.make_offer(offered)
		offered.reload()
		offered.put_on_hold()
		frappe.delete_doc("Job Offer", offer.name, force=True)
		offered.reload()
		self.assertEqual((offered.status, offered.stage), ("Hold", "Shortlisted"))

	def test_stage_syncs_with_employee(self):
		applicant = self.make_applicant("sync_employee")
		employee = make_employee(user=applicant.name, job_applicant=applicant.name, company="_Test Company")
		self.assertEqual(self.stored_stage(applicant), "Hired")

		frappe.db.set_value("Employee", employee, "job_applicant", None)
		frappe.get_doc("Employee", employee).save()
		frappe.db.set_value("Job Applicant", applicant.name, "status", "Open")
		self.assertEqual(self.rules_stage(applicant), "Applied")

	def test_manual_move_between_applied_shortlisted_and_rejected(self):
		applicant = self.make_applicant("manual")

		self.move_to(applicant, "Shortlisted")
		self.assertEqual((applicant.status, applicant.stage), ("Shortlisted", "Shortlisted"))

		self.move_to(applicant, "Rejected")
		self.assertEqual((applicant.status, applicant.stage), ("Rejected", "Rejected"))

		self.move_to(applicant, "Applied")
		self.assertEqual((applicant.status, applicant.stage), ("Open", "Applied"))

	def test_manual_move_to_stages_that_follow_records(self):
		applicant = self.make_applicant("manual_blocked")
		name = applicant.applicant_name

		for stage, message in (
			("Interviewing", f"Schedule an interview to move {name} to Interviewing."),
			("Offered", f"Create a job offer to move {name} to Offered."),
			("Hired", f"Mark the job offer as accepted to move {name} to Hired."),
		):
			applicant.reload()
			applicant.stage = stage
			with self.assertRaises(frappe.ValidationError) as error:
				applicant.save()
			self.assertEqual(str(error.exception), message)

		applicant.reload()
		self.assertEqual((applicant.status, applicant.stage), ("Open", "Applied"))

	def test_manual_move_back_is_blocked_by_interview(self):
		applicant = self.make_applicant("manual_interview", status="Shortlisted")
		create_interview_and_dependencies(applicant.name)

		for stage in ("Applied", "Shortlisted"):
			applicant.reload()
			applicant.stage = stage
			with self.assertRaises(frappe.ValidationError) as error:
				applicant.save()
			self.assertIn("has an interview, so they stay in Interviewing", str(error.exception))

		applicant.reload()
		self.assertEqual(applicant.stage, "Interviewing")

	def test_manual_move_back_is_blocked_by_offer(self):
		applicant = self.make_applicant("manual_offer")
		self.make_offer(applicant)

		for stage in ("Applied", "Shortlisted"):
			applicant.reload()
			applicant.stage = stage
			with self.assertRaises(frappe.ValidationError) as error:
				applicant.save()
			self.assertIn("has a job offer, so they stay in Offered", str(error.exception))

	def test_manual_move_to_rejected_works_with_interview(self):
		applicant = self.make_applicant("manual_reject_interview")
		create_interview_and_dependencies(applicant.name)

		self.move_to(applicant, "Rejected")
		self.assertEqual((applicant.status, applicant.stage), ("Rejected", "Rejected"))

	def test_reopening_a_rejected_applicant_follows_records(self):
		applicant = self.make_applicant("reopen")
		create_interview_and_dependencies(applicant.name)
		self.move_to(applicant, "Rejected")

		self.move_to(applicant, "Shortlisted")
		self.assertEqual((applicant.status, applicant.stage), ("Shortlisted", "Interviewing"))

		self.move_to(applicant, "Rejected")
		self.move_to(applicant, "Applied")
		self.assertEqual((applicant.status, applicant.stage), ("Open", "Interviewing"))

	def test_changing_status_alone_is_not_a_manual_move(self):
		applicant = self.make_applicant("status_only")
		create_interview_and_dependencies(applicant.name)

		applicant.reload()
		applicant.status = "Shortlisted"
		applicant.save()
		self.assertEqual(applicant.stage, "Interviewing")

	def test_new_applicant_with_a_stage(self):
		applicant = frappe.get_doc(
			{
				"doctype": "Job Applicant",
				"applicant_name": "Stage On Insert",
				"email_id": "stage_on_insert@example.com",
				"status": "Open",
				"stage": "Shortlisted",
			}
		).insert()
		self.assertEqual((applicant.status, applicant.stage), ("Shortlisted", "Shortlisted"))

		applicant = frappe.get_doc(
			{
				"doctype": "Job Applicant",
				"applicant_name": "Hired On Insert",
				"email_id": "hired_on_insert@example.com",
				"status": "Open",
				"stage": "Hired",
			}
		)
		self.assertRaises(frappe.ValidationError, applicant.insert)

	def test_patch_sets_stage_without_touching_modified(self):
		applicant = self.make_applicant("patch", status="Shortlisted")
		create_interview_and_dependencies(applicant.name)
		offer = self.make_offer(applicant)
		rejected = self.make_applicant("patch_rejected", status="Rejected")

		frappe.db.set_value("Job Applicant", applicant.name, "stage", "Applied", update_modified=False)
		frappe.db.set_value("Job Applicant", rejected.name, "stage", "Applied", update_modified=False)
		modified = frappe.db.get_value("Job Applicant", applicant.name, "modified")

		with patch.object(frappe.db, "commit"):
			set_job_applicant_stage()

		self.assertEqual(self.stored_stage(applicant), "Offered")
		self.assertEqual(self.stored_stage(rejected), "Rejected")
		self.assertEqual(frappe.db.get_value("Job Applicant", applicant.name, "modified"), modified)
		self.assertTrue(frappe.db.exists("Job Offer", offer.name))

	# Kanban drags and the client's set_value write a stage too; they follow the same rules as the form

	def make_stage_board(self, applicants):
		stages = ["Applied", "Shortlisted", "Interviewing", "Offered", "Hired", "Rejected"]
		board = frappe.get_doc(
			{
				"doctype": "Kanban Board",
				"kanban_board_name": "Test Stage Board",
				"reference_doctype": "Job Applicant",
				"field_name": "stage",
				"columns": [
					{
						"column_name": stage,
						"order": frappe.as_json([a.name for a in applicants if a.stage == stage]),
					}
					for stage in stages
				],
			}
		).insert()
		return board

	def test_kanban_drag_to_a_stage_that_follows_records_is_refused(self):
		applicant = self.make_applicant("kanban_refused")
		board = self.make_stage_board([applicant])

		for stage, message in (
			("Interviewing", f"Schedule an interview to move {applicant.applicant_name} to Interviewing."),
			("Offered", f"Create a job offer to move {applicant.applicant_name} to Offered."),
			("Hired", f"Mark the job offer as accepted to move {applicant.applicant_name} to Hired."),
		):
			with self.assertRaises(frappe.ValidationError) as error:
				update_order_for_single_card(
					board.name, applicant.name, "Applied", stage, from_order=[applicant.name], to_order=[]
				)
			self.assertEqual(str(error.exception), message)
			self.assertEqual(self.stored_stage(applicant), "Applied")

	def test_kanban_drag_between_manual_stages_moves_the_applicant(self):
		applicant = self.make_applicant("kanban_manual")
		board = self.make_stage_board([applicant])

		update_order_for_single_card(
			board.name, applicant.name, "Applied", "Shortlisted", from_order=[], to_order=[applicant.name]
		)
		applicant.reload()
		self.assertEqual((applicant.status, applicant.stage), ("Shortlisted", "Shortlisted"))

	def test_kanban_drag_back_is_blocked_by_an_interview(self):
		applicant = self.make_applicant("kanban_back", status="Shortlisted")
		create_interview_and_dependencies(applicant.name)
		board = self.make_stage_board([applicant])

		with self.assertRaises(frappe.ValidationError):
			update_order_for_single_card(
				board.name,
				applicant.name,
				"Interviewing",
				"Shortlisted",
				from_order=[],
				to_order=[applicant.name],
			)
		self.assertEqual(self.stored_stage(applicant), "Interviewing")

	def test_kanban_order_sync_does_not_write_a_refused_stage(self):
		applicant = self.make_applicant("kanban_sync")
		board = self.make_stage_board([applicant])

		update_order(board.name, {"Applied": [], "Offered": [applicant.name]})
		self.assertEqual(self.stored_stage(applicant), "Applied")

	def test_kanban_drag_out_of_rejected_follows_the_interview(self):
		applicant = self.make_applicant("kanban_reopen")
		create_interview_and_dependencies(applicant.name)
		self.move_to(applicant, "Rejected")
		board = self.make_stage_board([applicant])

		update_order_for_single_card(
			board.name, applicant.name, "Rejected", "Shortlisted", from_order=[], to_order=[applicant.name]
		)
		applicant.reload()
		self.assertEqual((applicant.status, applicant.stage), ("Shortlisted", "Interviewing"))

	def test_client_set_value_follows_the_stage_rules(self):
		applicant = self.make_applicant("client_set_value")

		with self.assertRaises(frappe.ValidationError):
			frappe.client.set_value("Job Applicant", applicant.name, "stage", "Offered")
		self.assertEqual(self.stored_stage(applicant), "Applied")

		frappe.client.set_value("Job Applicant", applicant.name, "stage", "Shortlisted")
		self.assertEqual(self.stored_stage(applicant), "Shortlisted")
