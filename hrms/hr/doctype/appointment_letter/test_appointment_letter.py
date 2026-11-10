# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import fmt_money

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.appointment_letter.appointment_letter import (
	format_days,
	format_probation,
	get_working_days,
	get_working_hours,
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
		frappe.db.set_single_value("HR Settings", "retirement_age", "60")
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
				**args,
			}
		).insert()

	def test_fetch_offer_details(self):
		letter = self.make_letter()
		self.assertEqual(letter.applicant_name, "Gaurang Jha")
		self.assertEqual(letter.applicant_email, "gaurang@example.com")
		self.assertEqual(letter.company, self.job_offer.company)
		self.assertEqual(str(letter.appointment_date), "2026-12-01")

	def test_fetch_employee_address(self):
		employee = make_employee("gaurang@example.com", company=self.job_offer.company)
		frappe.db.set_value("Employee", employee, "current_address", "T17, Paras Tierea, Noida")
		self.assertEqual(self.make_letter(employee=employee).address, "T17, Paras Tierea, Noida")
		self.assertEqual(
			self.make_letter(employee=employee, address="Typed address").address, "Typed address"
		)

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

	def test_empty_placeholder_renders_blank(self):
		self.job_offer.db_set("branch", None)
		frappe.clear_document_cache("Job Offer", self.job_offer.name)
		html = self.make_letter(letter_body="<p>from {{ place_of_posting }}.</p>").get_letter_body_html()
		self.assertEqual(html, "<p>from .</p>")

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

	def test_any_print_format_renders_placeholders(self):
		letter = self.make_letter(letter_body="<p>Your CTC is {{ ctc }}.</p>")
		html = frappe.get_print("Appointment Letter", letter.name, print_format="Standard")
		self.assertIn(f"Your CTC is {fmt_money(1600000, currency='INR')}.", html)
		self.assertNotIn("{{", html)
		self.assertEqual(
			frappe.db.get_value("Appointment Letter", letter.name, "letter_body"),
			"<p>Your CTC is {{ ctc }}.</p>",
		)

	def test_letter_field_placeholder(self):
		letter = self.make_letter(letter_body="<p>Write to {{ doc.applicant_email }}.</p>")
		self.assertEqual(letter.get_letter_body_html(), "<p>Write to gaurang@example.com.</p>")

	def test_code_in_letter_body_prints_as_text(self):
		body = (
			"<p>{{ frappe.db.sql('select name from tabUser') }}"
			"{% for row in frappe.get_all('User') %}{{ row }}{% endfor %}"
			"{{ doc.db_set('applicant_name', 'Changed') }}</p>"
		)
		letter = self.make_letter(letter_body=body)
		self.assertEqual(letter.get_letter_body_html(), body)
		self.assertEqual(
			frappe.db.get_value("Appointment Letter", letter.name, "applicant_name"), "Gaurang Jha"
		)

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
		template = frappe.get_doc(
			{
				"doctype": "Appointment Letter Template",
				"template_name": "_Test Old Braces",
				"letter_body": get_letter_body("Use {{ role }} and {% x", [], None),
			}
		).insert()
		template.save()
		template.reload()
		self.assertIn("Use {{ role }} and {% x", template.letter_body)

	def test_period_and_working_days_text(self):
		self.assertEqual(format_probation(90), "three (3) months")
		self.assertEqual(format_probation(30), "one (1) month")
		self.assertEqual(format_probation(45), "forty five (45) days")
		self.assertEqual(format_days(1), "one (1) day")
		self.assertEqual(format_days(0), "")
		self.assertEqual(get_working_days("Sunday"), "Monday to Saturday")
		self.assertEqual(
			get_working_days("Wednesday, Sunday"), "Monday, Tuesday, Thursday, Friday, and Saturday"
		)
		self.assertEqual(get_working_days(""), "")

	def test_working_hours_from_times(self):
		self.assertEqual(get_working_hours("10:00:00", "18:30:00"), 8.5)
		self.assertEqual(get_working_hours("22:00:00", "06:00:00"), 8)
		self.assertEqual(get_working_hours(None, "18:00:00"), 0)
		self.assertEqual(self.make_letter().working_hours, 8)
		self.assertEqual(self.make_letter(working_hours=7.5).working_hours, 7.5)
