# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import datetime
import os

import frappe
from frappe import _
from frappe.core.doctype.user_permission.test_user_permission import create_user
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, get_datetime, get_time, getdate, nowtime

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.interview.interview import (
	DuplicateInterviewRoundError,
	get_feedback,
	get_skill_wise_average_rating,
	update_job_applicant_status,
)
from hrms.hr.doctype.job_applicant.job_applicant import get_interview_details
from hrms.tests.test_utils import create_job_applicant, get_email_by_subject


class TestInterview(IntegrationTestCase):
	def test_validations_for_designation(self):
		job_applicant = create_job_applicant()
		interview = create_interview_and_dependencies(
			job_applicant.name, designation="_Test_Sales_manager", save=0
		)
		self.assertRaises(DuplicateInterviewRoundError, interview.save)

	def test_notification_on_rescheduling(self):
		job_applicant = create_job_applicant()
		interview = create_interview_and_dependencies(
			job_applicant.name,
			scheduled_on=add_days(getdate(), -4),
			from_time="10:00:00",
			to_time="11:00:00",
		)

		previous_scheduled_date = interview.scheduled_on
		frappe.db.sql("DELETE FROM `tabEmail Queue`")

		interview.reschedule_interview(
			add_days(getdate(previous_scheduled_date), 2), from_time="11:00:00", to_time="12:00:00"
		)
		interview.reload()

		self.assertEqual(interview.scheduled_on, add_days(getdate(previous_scheduled_date), 2))
		self.assertEqual(get_time(interview.from_time), get_time("11:00:00"))
		self.assertEqual(get_time(interview.to_time), get_time("12:00:00"))

		notification = frappe.get_all(
			"Email Queue", filters={"message": ("like", "%Your Interview session is rescheduled from%")}
		)
		self.assertIsNotNone(notification)

	def test_notification_for_scheduling(self):
		from hrms.hr.doctype.interview.interview import send_interview_reminder

		setup_reminder_settings()

		job_applicant = create_job_applicant()
		scheduled_on = datetime.datetime.now() + datetime.timedelta(minutes=10)

		create_interview_and_dependencies(job_applicant.name, scheduled_on=scheduled_on)

		frappe.db.delete("Email Queue")

		frappe.db.set_single_value("HR Settings", "send_interview_reminder", 0)
		send_interview_reminder()
		self.assertFalse(get_email_by_subject("Subject: Interview Reminder"))

		frappe.db.set_single_value("HR Settings", "send_interview_reminder", 1)
		send_interview_reminder()
		import time

		time.sleep(1)
		self.assertTrue(get_email_by_subject("Subject: Interview Reminder"))

	def test_notification_for_feedback_submission(self):
		from hrms.hr.doctype.interview.interview import send_daily_feedback_reminder

		setup_reminder_settings()

		job_applicant = create_job_applicant()
		scheduled_on = add_days(getdate(), -4)
		create_interview_and_dependencies(
			job_applicant.name, scheduled_on=scheduled_on, status="Under Review"
		)

		frappe.db.delete("Email Queue")

		frappe.db.set_single_value("HR Settings", "send_interview_feedback_reminder", 0)
		send_daily_feedback_reminder()
		self.assertFalse(get_email_by_subject("Subject: Interview Feedback Reminder"))

		frappe.db.set_single_value("HR Settings", "send_interview_feedback_reminder", 1)
		send_daily_feedback_reminder()
		self.assertTrue(get_email_by_subject("Subject: Interview Feedback Reminder"))

	def test_get_interview_details_for_applicant_dashboard(self):
		job_applicant = create_job_applicant()
		interview = create_interview_and_dependencies(job_applicant.name)

		details = get_interview_details(job_applicant.name)
		self.assertEqual(details.get("stars"), 5)
		self.assertEqual(
			details.get("interviews").get(interview.name),
			{
				"name": interview.name,
				"interview_round": interview.interview_round,
				"scheduled_on": interview.scheduled_on,
				"average_rating": interview.average_rating * 5,
				"status": "Pending",
			},
		)

	def test_skill_wise_average_rating(self):
		from hrms.hr.doctype.interview_feedback.test_interview_feedback import create_interview_feedback

		job_applicant = create_job_applicant()
		interview = create_interview_and_dependencies(job_applicant.name)

		create_interview_feedback(
			interview.name,
			"test_interviewer1@example.com",
			[{"skill": "Python", "rating": 0.9}, {"skill": "JS", "rating": 0.8}],
		)
		create_interview_feedback(
			interview.name,
			"test_interviewer2@example.com",
			[{"skill": "Python", "rating": 0.6}, {"skill": "JS", "rating": 0.9}],
		)

		ratings = get_skill_wise_average_rating(interview.name)
		self.assertEqual(ratings, [{"skill": "Python", "rating": 0.75}, {"skill": "JS", "rating": 0.85}])

	def test_get_feedback(self):
		from hrms.hr.doctype.interview_feedback.test_interview_feedback import create_interview_feedback

		job_applicant = create_job_applicant()
		interview = create_interview_and_dependencies(job_applicant.name)
		make_employee(
			"test_interviewer2@example.com",
			company="_Test Company",
			first_name="Test",
			date_of_joining=frappe.utils.add_years(getdate(), -2),
			designation="Engineer",
			user_id="test_interviewer2@example.com",
		)

		feedback_1 = create_interview_feedback(
			interview.name,
			"test_interviewer1@example.com",
			[{"skill": "Python", "rating": 0.9}, {"skill": "JS", "rating": 0.8}],
		)
		feedback_2 = create_interview_feedback(
			interview.name,
			"test_interviewer2@example.com",
			[{"skill": "Python", "rating": 0.6}, {"skill": "JS", "rating": 0.9}],
		)

		feedback = get_feedback(interview.name)
		expected_data = [
			{
				"name": feedback_1.name,
				"added_on": get_datetime(feedback_1.modified),
				"user": feedback_1.interviewer,
				"feedback": feedback_1.feedback,
				"total_score": feedback_1.average_rating * 5,
				"reviewer_name": None,
				"reviewer_designation": None,
			},
			{
				"name": feedback_2.name,
				"added_on": get_datetime(feedback_2.modified),
				"user": feedback_2.interviewer,
				"feedback": feedback_2.feedback,
				"total_score": feedback_2.average_rating * 5,
				"reviewer_name": "Test",
				"reviewer_designation": "Engineer",
			},
		]

		self.assertEqual(feedback, expected_data)

	def test_job_applicant_status_update_on_interview_submit(self):
		job_applicant = create_job_applicant()
		create_interview_and_dependencies(job_applicant.name, status="Cleared")

		update_job_applicant_status(job_applicant=job_applicant.name, status="Accepted")
		job_applicant.reload()

		self.assertEqual(job_applicant.status, "Accepted")

	def test_status_on_discard(self):
		job_applicant = create_job_applicant()
		interview = create_interview_and_dependencies(job_applicant.name, status="Pending")

		interview.discard()
		interview.reload()

		self.assertEqual(interview.status, "Cancelled")

	def tearDown(self):
		frappe.db.rollback()


def create_interview_and_dependencies(
	job_applicant,
	scheduled_on=None,
	from_time=None,
	to_time=None,
	designation=None,
	status=None,
	save=True,
):
	if designation:
		designation = create_designation(designation_name="_Test_Sales_manager").name

	create_user("test_interviewer1@example.com", "Interviewer")
	create_user("test_interviewer2@example.com", "Interviewer")

	interview_round = create_interview_round(
		"Technical Round",
		["Python", "JS"],
		["test_interviewer1@example.com", "test_interviewer2@example.com"],
		designation,
		True,
	)

	interview = frappe.new_doc("Interview")
	interview.interview_round = interview_round.name
	interview.job_applicant = job_applicant
	interview.scheduled_on = scheduled_on or getdate()
	interview.from_time = from_time or nowtime()
	interview.to_time = to_time or nowtime()
	interview.append("interview_details", {"interviewer": "test_interviewer1@example.com"})
	interview.append("interview_details", {"interviewer": "test_interviewer2@example.com"})

	if status:
		interview.status = status

	if save:
		interview.save()

	return interview


def create_interview_round(name, skill_set, interviewers=None, designation=None, save=True):
	create_skill_set(skill_set)
	interview_round = frappe.new_doc("Interview Round")
	interview_round.round_name = name
	interview_round.interview_type = create_interview_type()
	# average rating = 4
	interview_round.expected_average_rating = 0.8
	if designation:
		interview_round.designation = designation

	for skill in skill_set:
		interview_round.append("expected_skill_set", {"skill": skill})

	for interviewer in interviewers:
		interview_round.append("interviewers", {"user": interviewer})

	if save:
		interview_round.save()

	return interview_round


def create_skill_set(skill_set):
	for skill in skill_set:
		if not frappe.db.exists("Skill", skill):
			doc = frappe.new_doc("Skill")
			doc.skill_name = skill
			doc.save()


def create_interview_type(name="test_interview_type"):
	if frappe.db.exists("Interview Type", name):
		return frappe.get_doc("Interview Type", name).name
	else:
		doc = frappe.new_doc("Interview Type")
		doc.name = name
		doc.description = "_Test_Description"
		doc.save()

		return doc.name


def setup_reminder_settings():
	if not frappe.db.exists("Email Template", _("Interview Reminder")):
		base_path = frappe.get_app_path("erpnext", "hr", "doctype")
		response = frappe.read_file(
			os.path.join(base_path, "interview/interview_reminder_notification_template.html")
		)

		frappe.get_doc(
			{
				"doctype": "Email Template",
				"name": _("Interview Reminder"),
				"response": response,
				"subject": _("Interview Reminder"),
				"owner": frappe.session.user,
			}
		).insert(ignore_permissions=True)

	if not frappe.db.exists("Email Template", _("Interview Feedback Reminder")):
		base_path = frappe.get_app_path("erpnext", "hr", "doctype")
		response = frappe.read_file(
			os.path.join(base_path, "interview/interview_feedback_reminder_template.html")
		)

		frappe.get_doc(
			{
				"doctype": "Email Template",
				"name": _("Interview Feedback Reminder"),
				"response": response,
				"subject": _("Interview Feedback Reminder"),
				"owner": frappe.session.user,
			}
		).insert(ignore_permissions=True)

	hr_settings = frappe.get_doc("HR Settings")
	hr_settings.interview_reminder_template = _("Interview Reminder")
	hr_settings.feedback_reminder_notification_template = _("Interview Feedback Reminder")
	hr_settings.save()
