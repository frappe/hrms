# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from hrms.hr.doctype.training_event.test_training_event import (
	create_training_event,
	create_training_program,
)
from hrms.hr.doctype.training_feedback.test_training_feedback import create_training_feedback
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_employee
from hrms.tests.utils import HRMSTestSuite


class TestTrainingResult(HRMSTestSuite):
	def setUp(self):
		create_training_program("Basic Training")
		self.employee = make_employee("robert_loan@trainig.com", company="_Test Company")
		self.employee2 = make_employee("suzie.tan@trainig.com", company="_Test Company")
		self.employee3 = make_employee("training_late@trainig.com", company="_Test Company")
		self.training_event = create_training_event(
			[{"employee": self.employee}, {"employee": self.employee2}]
		)
		self.training_event.submit()

	def test_event_and_attendee_status_on_submit(self):
		create_training_feedback(self.training_event.name, self.employee2).submit()
		create_training_result(self.training_event.name, [self.employee, self.employee2]).submit()

		self.training_event.reload()
		self.assertEqual(self.training_event.event_status, "Completed")
		statuses = {d.employee: d.status for d in self.training_event.employees}
		self.assertEqual(statuses[self.employee], "Completed")
		self.assertEqual(statuses[self.employee2], "Feedback Submitted")

	def test_duplicate_result_for_event(self):
		create_training_result(self.training_event.name, [self.employee]).submit()
		result = create_training_result(self.training_event.name, [self.employee2])
		self.assertRaises(frappe.ValidationError, result.insert)

	def test_employee_validations(self):
		result = create_training_result(self.training_event.name, [self.employee, self.employee3])
		self.assertRaises(frappe.ValidationError, result.insert)

		result = create_training_result(self.training_event.name, [self.employee, self.employee])
		self.assertRaises(frappe.ValidationError, result.insert)

	def test_cancel_restores_event_and_attendee_status(self):
		create_training_feedback(self.training_event.name, self.employee2).submit()
		result = create_training_result(self.training_event.name, [self.employee, self.employee2])
		result.submit()

		frappe.db.set_value("Employee", self.employee, "status", "Left")
		result.cancel()

		self.training_event.reload()
		self.assertEqual(self.training_event.event_status, "Scheduled")
		statuses = {d.employee: d.status for d in self.training_event.employees}
		self.assertEqual(statuses[self.employee], "Open")
		self.assertEqual(statuses[self.employee2], "Feedback Submitted")


def create_training_result(event, employees):
	return frappe.get_doc(
		{
			"doctype": "Training Result",
			"training_event": event,
			"employees": [{"employee": employee, "hours": 2, "grade": "A"} for employee in employees],
		}
	)
