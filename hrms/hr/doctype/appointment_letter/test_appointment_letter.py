# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from hrms.hr.doctype.appointment_letter.appointment_letter import get_appointment_letter_details
from hrms.tests.utils import HRMSTestSuite


class TestAppointmentLetter(HRMSTestSuite):
	def test_details_for_missing_template(self):
		self.assertRaises(
			frappe.DoesNotExistError, get_appointment_letter_details, "_Test Missing Appointment Template"
		)
