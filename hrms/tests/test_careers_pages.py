import frappe
from frappe.utils import getdate, set_request
from frappe.website.serve import get_response_content

from hrms.hr.doctype.job_opening.test_job_opening import get_job_opening
from hrms.hr.doctype.staffing_plan.test_staffing_plan import make_company
from hrms.hr.report.monthly_attendance_sheet.test_monthly_attendance_sheet import create_branch
from hrms.tests.test_utils import create_department
from hrms.tests.utils import HRMSTestSuite
from hrms.www.jobs.index import (
	FILTERS,
	get_filter_controls,
	get_filters_txt_sort_offset,
	get_hiring_company,
	get_job_openings,
	get_published_openings,
)

MACROS = "hrms/templates/includes/job_opening_macros.html"
XSS = "<img src=x onerror=alert(1)//"


def render_salary(**opening):
	opening = {"publish_salary_range": 1, "currency": "INR", "salary_per": "Year", **opening}
	template = "{% from '" + MACROS + "' import salary with context %}{{ salary(opening) }}"
	return frappe.render_template(template, {"opening": frappe._dict(opening), "frappe": frappe})


def render_body(path, query_string=""):
	"""The page after </head>; Frappe's base template puts the title, tag-stripped, in <title>."""
	set_request(method="GET", path=path, query_string=query_string)
	return get_response_content(path).split("</head>", 1)[1]


def get_listed_opening(**args):
	"""An opening with every detail a careers page shows, so publishing it is allowed."""
	make_company("_Test Opening Company", "_TOC")
	details = {
		"department": create_department("Careers"),
		"location": create_branch("Careers Pune"),
		"employment_type": "Full-time",
		"description": "<p>Build things.</p>",
	}
	return get_job_opening(**{**details, **args})


def get_options(controls, name):
	control = next((control for control in controls if control["name"] == name), None)
	return control and {option["value"]: option for option in control["options"]}


class TestCareersPages(HRMSTestSuite):
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

	def test_filter_with_one_value_hidden_unless_in_use(self):
		openings = [frappe._dict(location="Pune"), frappe._dict(location="Pune")]
		self.assertIsNone(get_options(get_filter_controls({}, openings, {}), "location"))

		options = get_options(get_filter_controls({"location": ["Pune"]}, openings, {}), "location")
		self.assertTrue(options["Pune"]["selected"])

	def test_filter_keeps_selected_value(self):
		openings = [frappe._dict(location="Pune"), frappe._dict(location="Mumbai")]
		options = get_options(get_filter_controls({"location": ["Mumbai"]}, openings, {}), "location")
		self.assertTrue(options["Mumbai"]["selected"])
		self.assertFalse(options["Pune"]["selected"])

	def test_filters_follow_toolbar_order(self):
		openings = [
			frappe._dict(company="B", department="D1", employment_type="Full-time", location="Pune"),
			frappe._dict(company="A", department="D2", employment_type="Intern", location="Mumbai"),
		]
		controls = get_filter_controls({}, openings, {})
		self.assertEqual([control["name"] for control in controls], list(FILTERS))

	def test_team_label_falls_back_to_department_when_names_repeat(self):
		openings = [
			frappe._dict(department="Design - A"),
			frappe._dict(department="Design - B"),
			frappe._dict(department="Sales - A"),
		]
		team_names = {"Design - A": "Design", "Design - B": "Design", "Sales - A": "Sales"}
		options = get_options(get_filter_controls({}, openings, team_names), "department")
		self.assertEqual(
			{value: option["label"] for value, option in options.items()},
			{"Design - A": "Design - A", "Design - B": "Design - B", "Sales - A": "Sales"},
		)

	def test_request_args_drop_empty_values(self):
		self.addCleanup(setattr, frappe.local, "request", getattr(frappe.local, "request", None))
		set_request(method="GET", path="/jobs", query_string="location=&location=Pune&company=&query=dev")
		filters, txt, sort, offset = get_filters_txt_sort_offset()
		self.assertEqual(filters, {"location": ["Pune"]})
		self.assertEqual((txt, sort, offset), ("dev", None, 0))

	def test_unpublished_and_closed_openings_stay_hidden(self):
		cases = {"Careers Open": (1, "Open"), "Careers Draft": (0, "Open"), "Careers Closed": (1, "Closed")}
		for title, (publish, status) in cases.items():
			frappe.get_doc({"doctype": "Branch", "branch": title}).insert(ignore_if_duplicate=True)
			opening = get_listed_opening(job_title=title, publish=publish, status=status, location=title)
			if status == "Closed":
				opening.closed_on = getdate()
			opening.insert()

		results = get_job_openings({}, "Careers", team_names={})
		self.assertEqual({d.job_title for d in results} & cases.keys(), {"Careers Open"})

		in_use = {"location": ["Careers Open"]}
		options = get_options(get_filter_controls(in_use, get_published_openings(), {}), "location")
		self.assertIn("Careers Open", options)
		self.assertNotIn("Careers Draft", options)
		self.assertNotIn("Careers Closed", options)

	def test_opening_fields_are_escaped(self):
		self.addCleanup(setattr, frappe.local, "request", getattr(frappe.local, "request", None))
		opening = get_listed_opening(
			job_title="Careers Escape", route="jobs/careers-escape", publish=1, description="<p>Hello</p>"
		).insert()
		# Set directly: a Branch name cannot hold "<"
		frappe.db.set_value("Job Opening", opening.name, {"job_title": XSS, "location": XSS})

		jobs = render_body("/jobs", "query=onerror")
		role = render_body("/jobs/careers-escape")
		for body in (jobs, role):
			self.assertIn("&lt;img src=x", body)
			self.assertNotIn("<img src=x", body)
		self.assertIn("<p>Hello</p>", role)
