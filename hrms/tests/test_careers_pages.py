import frappe
from frappe.tests import IntegrationTestCase

from hrms.www.jobs.index import get_hiring_company

MACROS = "hrms/templates/includes/job_opening_macros.html"


def render_salary(**opening):
	opening = {"publish_salary_range": 1, "currency": "INR", "salary_per": "Year", **opening}
	template = "{% from '" + MACROS + "' import salary with context %}{{ salary(opening) }}"
	return frappe.render_template(template, {"opening": frappe._dict(opening), "frappe": frappe})


class TestCareersPages(IntegrationTestCase):
	def test_salary_uses_short_form_for_rupees(self):
		self.assertEqual(render_salary(lower_range=1800000, upper_range=2800000), "₹18L – ₹28L a year")
		self.assertEqual(render_salary(lower_range=1850000, upper_range=0), "₹18.5L a year")

	def test_salary_hidden_unless_published_with_amounts(self):
		self.assertEqual(render_salary(lower_range=1800000, upper_range=2800000, publish_salary_range=0), "")
		self.assertEqual(render_salary(lower_range=0, upper_range=0), "")

	def test_salary_uses_currency_format_outside_rupees(self):
		result = render_salary(lower_range=5000, upper_range=7000, currency="USD", salary_per="Month")
		self.assertIn("5,000", result)
		self.assertTrue(result.endswith("a month"))

	def test_intro_names_company_only_when_single(self):
		openings = [frappe._dict(company="Frappe"), frappe._dict(company="Frappe")]
		self.assertEqual(get_hiring_company(openings), "Frappe")
		openings.append(frappe._dict(company="Other"))
		self.assertEqual(get_hiring_company(openings), "")
