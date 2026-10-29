from unittest.mock import patch

import frappe
from frappe.utils import getdate

from hrms.setup_wizard import create_default_holiday_list, get_setup_stages, holiday_list_from_wizard_args
from hrms.tests.utils import HRMSTestSuite

COMPANY = "_Test Company"


class TestDefaultHolidayList(HRMSTestSuite):
	def setUp(self):
		frappe.db.set_value("Company", COMPANY, "default_holiday_list", None)

	def wizard_args(self, country="India", **kwargs):
		return {
			"company": COMPANY,
			"country": country,
			"from_date": "2027-04-01",
			"to_date": "2028-03-31",
			**kwargs,
		}

	def default_holiday_list(self):
		name = frappe.db.get_value("Company", COMPANY, "default_holiday_list")
		return frappe.get_doc("Holiday List", name) if name else None

	def test_creates_fiscal_year_list_with_public_holidays_and_sundays(self):
		create_default_holiday_list(self.wizard_args())

		holiday_list = self.default_holiday_list()
		self.assertEqual(holiday_list.name, f"{COMPANY} 2027-2028")
		self.assertEqual(getdate(holiday_list.from_date), getdate("2027-04-01"))
		self.assertEqual(getdate(holiday_list.to_date), getdate("2028-03-31"))

		weekly_offs = {getdate(h.holiday_date).strftime("%A") for h in holiday_list.holidays if h.weekly_off}
		self.assertEqual(weekly_offs, {"Sunday"})

		public = {getdate(h.holiday_date) for h in holiday_list.holidays if not h.weekly_off}
		self.assertIn(getdate("2027-08-15"), public)
		self.assertIn(getdate("2028-01-26"), public)

	def test_public_holiday_on_a_weekly_off_keeps_its_name(self):
		create_default_holiday_list(self.wizard_args())

		# 15 Aug 2027 is a Sunday
		holiday = next(
			h
			for h in self.default_holiday_list().holidays
			if getdate(h.holiday_date) == getdate("2027-08-15")
		)
		self.assertFalse(holiday.weekly_off)
		self.assertNotEqual(holiday.description, "Sunday")

	def test_uses_the_countrys_weekend(self):
		create_default_holiday_list(self.wizard_args(country="Saudi Arabia"))

		weekly_offs = {
			getdate(h.holiday_date).strftime("%A")
			for h in self.default_holiday_list().holidays
			if h.weekly_off
		}
		self.assertEqual(weekly_offs, {"Friday", "Saturday"})

	def test_country_without_holiday_data_gets_sundays_only(self):
		with patch("hrms.setup_wizard.is_supported_by_holidays_library", return_value=False):
			create_default_holiday_list(self.wizard_args())

		holidays = self.default_holiday_list().holidays
		self.assertTrue(holidays)
		self.assertTrue(all(h.weekly_off for h in holidays))

	def test_falls_back_to_calendar_year_without_fiscal_year_dates(self):
		create_default_holiday_list(self.wizard_args(from_date=None, to_date=None))

		holiday_list = self.default_holiday_list()
		year = getdate().year
		self.assertEqual(holiday_list.name, f"{COMPANY} {year}")
		self.assertEqual(getdate(holiday_list.from_date), getdate(f"{year}-01-01"))
		self.assertEqual(getdate(holiday_list.to_date), getdate(f"{year}-12-31"))

	def test_keeps_an_existing_default_holiday_list(self):
		existing = frappe.get_all("Holiday List", pluck="name", limit=1)[0]
		frappe.db.set_value("Company", COMPANY, "default_holiday_list", existing)

		create_default_holiday_list(self.wizard_args())

		self.assertEqual(frappe.db.get_value("Company", COMPANY, "default_holiday_list"), existing)
		self.assertFalse(frappe.db.exists("Holiday List", f"{COMPANY} 2027-2028"))

	def test_failure_is_logged_without_failing_the_setup(self):
		with patch(
			"erpnext.setup.doctype.holiday_list.holiday_list.HolidayList.get_local_holidays",
			side_effect=Exception("holidays library broke"),
		):
			create_default_holiday_list(self.wizard_args())

		self.assertIsNone(self.default_holiday_list())
		self.assertFalse(frappe.db.exists("Holiday List", f"{COMPANY} 2027-2028"))

	def test_skips_a_company_that_does_not_exist(self):
		create_default_holiday_list(self.wizard_args(company="Nonexistent Company"))

		self.assertFalse(frappe.db.exists("Holiday List", "Nonexistent Company 2027-2028"))

	def test_stage_runs_for_every_site_with_narrowed_args(self):
		wizard_args = {
			"company_name": COMPANY,
			"country": "India",
			"fy_start_date": "2027-04-01",
			"fy_end_date": "2028-03-31",
			"email": "admin@example.com",
		}

		with patch.dict(frappe.conf, {"sk_hrms": 0}):
			stages = get_setup_stages(wizard_args)

		task = stages[0]["tasks"][0]
		self.assertEqual(len(stages), 1)
		self.assertIs(task["fn"], create_default_holiday_list)
		self.assertEqual(task["args"], holiday_list_from_wizard_args(wizard_args))
		self.assertNotIn("email", task["args"])
