# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import fmt_money

from hrms.hr.doctype.appointment_letter.appointment_letter import (
	format_days,
	format_probation,
	get_working_days,
)
from hrms.hr.doctype.appointment_letter_template.appointment_letter_template import (
	create_default_template,
	get_default_letter_body,
	get_default_template,
)
from hrms.hr.doctype.job_offer.test_job_offer import create_job_offer
from hrms.patches.v16_0.move_appointment_letter_terms_to_letter_body import get_letter_body
from hrms.tests.utils import HRMSTestSuite


class TestAppointmentLetter(HRMSTestSuite):
	def setUp(self):
		self.job_offer = create_job_offer(
			applicant_name="Gaurang Jha",
			applicant_email="gaurang@example.com",
			designation="Engineer",
			date_of_joining="2026-12-01",
			probation_period_days=90,
			notice_number_of_days=30,
		).insert()
		if not frappe.db.exists("Branch", "Mumbai"):
			frappe.get_doc({"doctype": "Branch", "branch": "Mumbai"}).insert()
		self.job_offer.db_set(
			{"weekly_off_days": "Saturday, Sunday", "ctc": 1600000, "currency": "INR", "branch": "Mumbai"}
		)

	def make_letter(self, **args):
		return frappe.get_doc(
			{
				"doctype": "Appointment Letter",
				"job_offer": self.job_offer.name,
				"start_time": "10:00:00",
				"end_time": "18:00:00",
				"retirement_age": 60,
				**args,
			}
		).insert()

	def test_fetch_offer_details(self):
		letter = self.make_letter()
		self.assertEqual(letter.applicant_name, "Gaurang Jha")
		self.assertEqual(letter.applicant_email, "gaurang@example.com")
		self.assertEqual(letter.company, self.job_offer.company)
		self.assertEqual(str(letter.appointment_date), "2026-12-01")

	def test_default_template_selected(self):
		frappe.db.set_value("Appointment Letter Template", {"is_default": 1}, "is_default", 0)
		create_default_template()
		template = get_default_template()

		letter = self.make_letter()
		self.assertEqual(letter.appointment_letter_template, template)
		self.assertEqual(
			letter.letter_body, frappe.db.get_value("Appointment Letter Template", template, "letter_body")
		)

	def test_one_default_template(self):
		create_default_template()
		old_default = get_default_template()
		new_default = frappe.get_doc(
			{
				"doctype": "Appointment Letter Template",
				"template_name": "_Test New Default",
				"is_default": 1,
				"letter_body": "<p>Hello</p>",
			}
		).insert()

		self.assertEqual(get_default_template(), new_default.name)
		self.assertFalse(frappe.db.get_value("Appointment Letter Template", old_default, "is_default"))

	def test_default_body_renders_placeholders(self):
		letter = self.make_letter(letter_body=get_default_letter_body())
		self.assertIn("{{ probation }}", letter.letter_body)

		html = letter.get_letter_body_html()
		for text in (
			"<strong>Engineer</strong>",
			"effect from December 1, 2026, and you will be working from Mumbai",
			"probation for three (3) months",
			"You will work Monday to Friday, from 10:00 AM to 6:00 PM",
			"thirty (30) days written notice",
			"age of 60 years",
			f"<strong>{fmt_money(1600000, currency='INR')}</strong> per annum",
		):
			self.assertIn(text, html)
		self.assertNotIn("{{", html)

	def test_template_body_on_insert(self):
		template = frappe.get_doc(
			{
				"doctype": "Appointment Letter Template",
				"template_name": "_Test Short Terms",
				"letter_body": "<p>Welcome, {{ applicant_name }}.</p>",
			}
		).insert()
		letter = self.make_letter(appointment_letter_template=template.name)
		self.assertEqual(letter.get_letter_body_html(), "<p>Welcome, Gaurang Jha.</p>")

	def test_invalid_placeholder_syntax(self):
		self.assertRaises(frappe.ValidationError, self.make_letter, letter_body="<p>{{ ctc </p>")

	def test_old_terms_become_letter_body(self):
		terms = [
			frappe._dict(title="Probation", description="Six months.\nExtendable."),
			frappe._dict(title="", description="A < B"),
		]
		body = get_letter_body("Dear candidate", terms, "Regards")
		self.assertIn("<p>Dear candidate</p><ol>", body)
		self.assertIn("<strong>Probation:</strong> Six months.<br>Extendable.</li>", body)
		self.assertIn("A &lt; B</li></ol><p>Regards</p>", body)
		self.assertEqual(get_letter_body(None, [], None), "")

	def test_period_and_working_days_text(self):
		self.assertEqual(format_probation(90), "three (3) months")
		self.assertEqual(format_probation(30), "one (1) month")
		self.assertEqual(format_probation(45), "forty five (45) days")
		self.assertEqual(format_days(1), "one (1) day")
		self.assertEqual(format_days(0), "")
		self.assertEqual(get_working_days("Sunday"), "Monday to Saturday")
		self.assertEqual(
			get_working_days("Wednesday, Sunday"), "Monday, Tuesday, Thursday, Friday and Saturday"
		)
		self.assertEqual(get_working_days(""), "")
