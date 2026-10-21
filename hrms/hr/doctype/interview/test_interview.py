# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import datetime
import os

import frappe
from frappe import _
from frappe.core.doctype.user_permission.test_user_permission import create_user
from frappe.utils import add_days, get_datetime, get_time, getdate, now_datetime

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.interview.interview import (
	DuplicateInterviewRoundError,
	create_interview_feedback,
	get_feedback,
	get_skill_wise_average_rating,
	update_job_applicant_status,
)
from hrms.hr.doctype.job_applicant.job_applicant import get_interview_details
from hrms.tests.test_utils import create_job_applicant, get_email_by_subject
from hrms.tests.utils import HRMSTestSuite


class TestInterview(HRMSTestSuite):
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
		email_queue = frappe.qb.DocType("Email Queue")
		frappe.qb.from_(email_queue).delete().run()

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
		scheduled_on = now_datetime() + datetime.timedelta(minutes=10)

		create_interview_and_dependencies(
			job_applicant.name,
			scheduled_on=scheduled_on,
			from_time=scheduled_on.time().replace(microsecond=0),
			to_time=datetime.time(23, 59, 59),
		)

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

	def test_interview_reminder_window(self):
		from hrms.hr.doctype.interview.interview import send_interview_reminder

		setup_reminder_settings()
		frappe.db.set_single_value("HR Settings", "send_interview_reminder", 1)
		frappe.db.set_single_value("HR Settings", "remind_before", "01:00:00")

		now = now_datetime()
		due = now + datetime.timedelta(minutes=30)
		over = now - datetime.timedelta(hours=3)
		later = now + datetime.timedelta(hours=3)

		def make(start):
			end = min(
				start + datetime.timedelta(minutes=5),
				datetime.datetime.combine(start, datetime.time(23, 59, 59)),
			)
			return create_interview_and_dependencies(
				create_job_applicant().name,
				scheduled_on=start.date(),
				from_time=start.time().replace(microsecond=0),
				to_time=end.time().replace(microsecond=0),
			)

		due_interview, over_interview, later_interview = make(due), make(over), make(later)
		send_interview_reminder()

		self.assertEqual(frappe.db.get_value("Interview", due_interview.name, "reminded"), 1)
		self.assertEqual(frappe.db.get_value("Interview", over_interview.name, "reminded"), 0)
		self.assertEqual(frappe.db.get_value("Interview", later_interview.name, "reminded"), 0)

	def test_feedback_reminder_for_interview_ended_yesterday(self):
		from hrms.hr.doctype.interview.interview import send_daily_feedback_reminder

		setup_reminder_settings()
		frappe.db.set_single_value("HR Settings", "send_interview_feedback_reminder", 1)

		interview = create_interview_and_dependencies(
			create_job_applicant().name,
			scheduled_on=add_days(getdate(), -1),
			from_time="22:00:00",
			to_time="23:00:00",
			status="Under Review",
		)
		frappe.db.delete("Email Queue")

		send_daily_feedback_reminder()
		self.assertTrue(
			frappe.db.exists(
				"Email Queue", {"reference_doctype": "Interview", "reference_name": interview.name}
			)
		)

	def test_feedback_reminder_for_pending_interview(self):
		from hrms.hr.doctype.interview.interview import send_daily_feedback_reminder

		setup_reminder_settings()
		frappe.db.set_single_value("HR Settings", "send_interview_feedback_reminder", 1)

		interview = create_interview_and_dependencies(
			create_job_applicant().name, scheduled_on=add_days(getdate(), -1)
		)
		frappe.db.delete("Email Queue")

		send_daily_feedback_reminder()
		self.assertTrue(
			frappe.db.exists(
				"Email Queue", {"reference_doctype": "Interview", "reference_name": interview.name}
			)
		)

	def test_overlap_warning(self):
		scheduled_on = add_days(getdate(), 5)
		first = create_interview_and_dependencies(
			create_job_applicant().name, scheduled_on=scheduled_on, from_time="10:00:00", to_time="11:00:00"
		)

		frappe.clear_messages()
		second = create_interview_and_dependencies(
			create_job_applicant().name, scheduled_on=scheduled_on, from_time="10:30:00", to_time="11:30:00"
		)
		self.assertTrue(second.name)
		self.assertIn(first.name, str(frappe.get_message_log()))

		frappe.clear_messages()
		create_interview_and_dependencies(
			create_job_applicant().name, scheduled_on=scheduled_on, from_time="11:00:00", to_time="12:00:00"
		)
		self.assertNotIn(first.name, str(frappe.get_message_log()))

	def test_interviewer_sees_only_own_panel(self):
		from hrms.hr.doctype.interview.interview import get_events

		interview = create_interview_and_dependencies(create_job_applicant().name)
		create_user("test_interviewer3@example.com", "Interviewer")

		frappe.set_user("test_interviewer3@example.com")
		try:
			self.assertFalse(frappe.has_permission("Interview", "read", interview.name))
			self.assertFalse(frappe.get_list("Interview", filters={"name": interview.name}))
			self.assertNotIn(
				interview.name,
				[d.name for d in get_events(str(interview.scheduled_on), str(interview.scheduled_on))],
			)
			self.assertRaises(frappe.PermissionError, get_feedback, interview.name)
		finally:
			frappe.set_user("Administrator")

		frappe.set_user("test_interviewer1@example.com")
		try:
			self.assertTrue(frappe.has_permission("Interview", "read", interview.name))
			self.assertTrue(frappe.get_list("Interview", filters={"name": interview.name}))
		finally:
			frappe.set_user("Administrator")

	def test_time_validation(self):
		interview = create_interview_and_dependencies(
			create_job_applicant().name, from_time="15:00:00", to_time="11:00:00", save=False
		)
		self.assertRaises(frappe.ValidationError, interview.save)

	def test_reschedule_validations(self):
		interview = create_interview_and_dependencies(
			create_job_applicant().name,
			scheduled_on=add_days(getdate(), 2),
			from_time="10:00:00",
			to_time="11:00:00",
		)
		interview.db_set("reminded", 1)

		self.assertRaises(
			frappe.ValidationError,
			interview.reschedule_interview,
			add_days(getdate(), 3),
			datetime.time(9, 0),
			datetime.time(8, 0),
		)

		interview.reschedule_interview(add_days(getdate(), 3), datetime.time(9, 0), datetime.time(10, 0))
		self.assertEqual(frappe.db.get_value("Interview", interview.name, "reminded"), 0)

		frappe.db.delete("Email Queue")
		interview.reload()
		interview.reschedule_interview(str(interview.scheduled_on), "09:00:00", "10:00:00")
		self.assertFalse(frappe.db.exists("Email Queue", {"reference_name": interview.name}))

		create_user("test_interview_reader@example.com", "Employee")
		frappe.set_user("test_interview_reader@example.com")
		try:
			self.assertRaises(
				frappe.PermissionError,
				interview.reschedule_interview,
				add_days(getdate(), 4),
				datetime.time(9, 0),
				datetime.time(10, 0),
			)
		finally:
			frappe.set_user("Administrator")

		interview.reload()
		interview.status = "Cleared"
		interview.submit()
		self.assertRaises(
			frappe.ValidationError,
			interview.reschedule_interview,
			add_days(getdate(), 4),
			datetime.time(9, 0),
			datetime.time(10, 0),
		)

	def test_status_on_cancel(self):
		interview = create_interview_and_dependencies(create_job_applicant().name, status="Cleared")
		interview.submit()
		interview.cancel()
		self.assertEqual(frappe.db.get_value("Interview", interview.name, "status"), "Cancelled")

	def test_create_interview_feedback_with_dict_data(self):
		interview = create_interview_and_dependencies(
			create_job_applicant().name, scheduled_on=add_days(getdate(), -1)
		)
		frappe.set_user("test_interviewer1@example.com")
		try:
			create_interview_feedback(
				{"skill_set": [{"skill": "Python", "rating": 0.8}], "result": "Cleared"},
				interview.name,
				"test_interviewer1@example.com",
				interview.job_applicant,
			)
		finally:
			frappe.set_user("Administrator")

		self.assertTrue(
			frappe.db.exists(
				"Interview Feedback",
				{"interview": interview.name, "interviewer": "test_interviewer1@example.com", "docstatus": 1},
			)
		)

	def test_get_interview_details_for_applicant_dashboard(self):
		job_applicant = create_job_applicant()
		interview = create_interview_and_dependencies(job_applicant.name)

		details = get_interview_details(job_applicant.name)
		self.assertEqual(details.get("stars"), 5)
		self.assertEqual(
			details.get("interviews").get(interview.name),
			{
				"name": interview.name,
				"interview_type": interview.interview_type,
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

	def test_update_job_applicant_status_invalid_input(self):
		# Ensure passing empty or non-existent job applicant string does not raise AttributeError
		try:
			update_job_applicant_status("Accepted", "")
		except AttributeError:
			self.fail("update_job_applicant_status raised AttributeError on empty job applicant string")

		try:
			update_job_applicant_status("Accepted", "NON_EXISTENT_JOB_APPLICANT")
		except AttributeError:
			self.fail("update_job_applicant_status raised AttributeError on invalid job applicant ID")


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

	interview_type = create_interview_type(
		"Technical Round",
		["Python", "JS"],
		["test_interviewer1@example.com", "test_interviewer2@example.com"],
		designation,
		True,
	)

	interview = frappe.new_doc("Interview")
	interview.interview_type = interview_type.name
	interview.job_applicant = job_applicant
	interview.scheduled_on = scheduled_on or getdate()
	interview.from_time = from_time or "10:00:00"
	interview.to_time = to_time or "11:00:00"
	interview.append("interview_details", {"interviewer": "test_interviewer1@example.com"})
	interview.append("interview_details", {"interviewer": "test_interviewer2@example.com"})

	if status:
		interview.status = status

	if save:
		interview.save()

	return interview


def create_interview_type(name, skill_set, interviewers=None, designation=None, save=True):
	create_skill_set(skill_set)
	if frappe.db.exists("Interview Type", name):
		interview_type = frappe.get_doc("Interview Type", name)
		interview_type.designation = None
		interview_type.expected_skill_set = []
		interview_type.interviewers = []
	else:
		interview_type = frappe.new_doc("Interview Type")
	interview_type.interview_type_name = name
	interview_type.description = "_Test_Description"
	# average rating = 4
	interview_type.expected_average_rating = 0.8
	if designation:
		interview_type.designation = designation

	for skill in skill_set:
		interview_type.append("expected_skill_set", {"skill": skill})

	for interviewer in interviewers:
		interview_type.append("interviewers", {"user": interviewer})

	if save:
		interview_type.save()
	return interview_type


def create_skill_set(skill_set):
	for skill in skill_set:
		if not frappe.db.exists("Skill", skill):
			doc = frappe.new_doc("Skill")
			doc.skill_name = skill
			doc.save()


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
