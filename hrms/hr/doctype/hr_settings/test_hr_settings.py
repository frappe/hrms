# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe

from hrms.hr.doctype.hr_settings.hr_settings import HRSettings
from hrms.tests.utils import HRMSTestSuite


class TestHRSettings(HRMSTestSuite):
	def test_invalid_retirement_age(self):
		for value in ("sixty", "0", "-5"):
			hr_settings = frappe.get_doc("HR Settings")
			hr_settings.retirement_age = value
			self.assertRaises(frappe.ValidationError, hr_settings.save)

		hr_settings = frappe.get_doc("HR Settings")
		hr_settings.retirement_age = "58"
		hr_settings.save()

	def test_frequency_change_confirmation_is_per_save(self):
		hr_settings = frappe.get_doc("HR Settings")

		with patch.object(HRSettings, "validate_frequency_change") as validate_frequency_change:
			hr_settings.set("__proceed_with_frequency_change", 1)
			hr_settings.save()
			validate_frequency_change.assert_not_called()

			hr_settings = frappe.get_doc("HR Settings")
			hr_settings.save()
			validate_frequency_change.assert_called_once()
