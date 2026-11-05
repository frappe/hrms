# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, today

from hrms.payroll.doctype.salary_structure.test_salary_structure import make_employee
from hrms.tests.utils import HRMSTestSuite


class TestTrainingEvent(HRMSTestSuite):
	def setUp(self):
		create_training_program("Basic Training")
		employee = make_employee("robert_loan@trainig.com", company="_Test Company")
		employee2 = make_employee("suzie.tan@trainig.com", company="_Test Company")
		self.attendees = [{"employee": employee}, {"employee": employee2}]

	def test_training_event_status_update(self):
		training_event = create_training_event(self.attendees)
		training_event.submit()

		training_event.event_status = "Completed"
		training_event.save()
		training_event.reload()

		for entry in training_event.employees:
			self.assertEqual(entry.status, "Completed")

		training_event.event_status = "Scheduled"
		training_event.save()
		training_event.reload()

		for entry in training_event.employees:
			self.assertEqual(entry.status, "Open")

	def test_attendee_status_on_submit_of_completed_event(self):
		training_event = create_training_event(self.attendees, event_status="Completed")
		training_event.submit()
		training_event.reload()

		for entry in training_event.employees:
			self.assertEqual(entry.status, "Completed")

	def test_feedback_submitted_status_kept_on_update_after_submit(self):
		from hrms.hr.doctype.training_feedback.test_training_feedback import create_training_feedback

		training_event = create_training_event(self.attendees)
		training_event.submit()
		create_training_feedback(training_event.name, self.attendees[0]["employee"]).submit()

		employee3 = make_employee("training_late@trainig.com", company="_Test Company")
		training_event.reload()
		training_event.append("employees", {"employee": employee3})
		training_event.save()
		training_event.reload()

		statuses = {d.employee: d.status for d in training_event.employees}
		self.assertEqual(statuses[self.attendees[0]["employee"]], "Feedback Submitted")
		self.assertEqual(statuses[employee3], "Open")

	def test_attendee_validations(self):
		employee = self.attendees[0]["employee"]
		self.assertRaises(
			frappe.ValidationError, create_training_event, [{"employee": employee}, {"employee": employee}]
		)

		self.assertRaises(
			frappe.ValidationError, create_training_event, self.attendees, company="_Test Company 1"
		)

		frappe.db.set_value("Employee", employee, {"status": "Left", "relieving_date": today()})
		self.assertRaises(frappe.ValidationError, create_training_event, [{"employee": employee}])

	def test_employee_sees_only_attended_events(self):
		from hrms.hr.doctype.training_event.training_event import (
			get_permission_query_conditions,
			has_permission,
		)

		event = create_training_event(self.attendees)
		attendee_user = frappe.db.get_value("Employee", self.attendees[0]["employee"], "user_id")
		outsider = "training_outsider@trainig.com"
		make_employee(outsider, company="_Test Company")

		def visible_events(user):
			condition = get_permission_query_conditions(user)
			self.assertTrue(condition)
			return frappe.db.sql_list(f"select name from `tabTraining Event` where {condition}")

		self.assertFalse(has_permission(event, "read", outsider))
		self.assertNotIn(event.name, visible_events(outsider))
		self.assertTrue(has_permission(event, "read", attendee_user))
		self.assertIn(event.name, visible_events(attendee_user))
		self.assertTrue(has_permission(event, "read", "Administrator"))
		self.assertFalse(get_permission_query_conditions("Administrator"))

	def test_mandatory_note_in_scheduled_notification(self):
		template = frappe.read_file(
			frappe.get_app_path("hrms", "hr", "notification", "training_scheduled", "training_scheduled.md")
		)
		note = "This Training Event is mandatory"

		event = create_training_event(self.attendees)
		self.assertIn(note, frappe.render_template(template, {"doc": event}))

		event.employees[1].is_mandatory = 0
		self.assertNotIn(note, frappe.render_template(template, {"doc": event}))

		event.employees[0].is_mandatory = 0
		self.assertNotIn(note, frappe.render_template(template, {"doc": event}))


def create_training_program(training_program, company="_Test Company"):
	if not frappe.db.get_value("Training Program", training_program):
		frappe.get_doc(
			{
				"doctype": "Training Program",
				"training_program": training_program,
				"description": training_program,
				"company": company,
			}
		).insert()


def create_training_event(attendees, **kwargs):
	return frappe.get_doc(
		{
			"doctype": "Training Event",
			"event_name": "Basic Training Event",
			"training_program": "Basic Training",
			"location": "Union Square",
			"start_time": add_days(today(), -6),
			"end_time": add_days(today(), -5),
			"introduction": "Welcome to the Basic Training Event",
			"company": "_Test Company",
			"employees": attendees,
			**kwargs,
		}
	).insert()
