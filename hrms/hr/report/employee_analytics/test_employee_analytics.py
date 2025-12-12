import frappe
from frappe import _
from frappe.desk.page.setup_wizard.setup_wizard import make_records
from frappe.tests import IntegrationTestCase

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.report.employee_analytics.employee_analytics import execute
from hrms.tests.test_utils import create_company


class TestEmployeeAnalytics(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		create_branches()
		create_employee_grade()

	def setUp(self):
		self.company = "_Test Company"
		self.company_2 = create_company("_Test Company 2").name

	def test_branches(self):
		make_employee("test_analytics1@example.com", company=self.company, branch="Test Branch 1")
		make_employee("test_analytics2@example.com", company=self.company, branch="Test Branch 2")
		make_employee("test_analytics3@example.com", company=self.company, branch="Test Branch 2")
		make_employee("test_analytics4@Eexample.com", company=self.company_2)

		employees_with_no_branch = get_employees_without_set_parameter("branch", self.company)

		filters = frappe._dict({"company": self.company, "parameter": "Branch"})

		report = execute(filters=filters)
		employees_in_report = report[1]
		self.assertEqual(len(employees_in_report), 3)

		chart_data = report[3]["data"]

		values_to_assert = {"Test Branch 1": 1, "Test Branch 2": 2, "Not Set": employees_with_no_branch}
		test_data(self, values_to_assert, chart_data)

	def test_employee_grade(self):
		make_employee("test_analytics1@example.com", company=self.company, grade="1")
		make_employee("test_analytics2@example.com", company=self.company, grade="2")
		make_employee("test_analytics3@example.com", company=self.company, grade="2")

		employees_with_no_grade = get_employees_without_set_parameter("grade", self.company)
		values_to_assert = {"1": 1, "2": 2, "Not Set": employees_with_no_grade}
		filters = frappe._dict({"company": self.company, "parameter": "Grade"})
		report = execute(filters=filters)

		chart_data = report[3]["data"]
		test_data(self, values_to_assert, chart_data)

	def test_company_descendants_filter(self):
		"""Test that company descendants filter includes child company employees"""
		create_company("Test Parent Company", is_group=1)
		create_company("Test Child Company", parent_company="Test Parent Company")

		frappe.db.delete("Employee", {"company": ["in", ["Test Parent Company", "Test Child Company"]]})

		employee1 = make_employee("test_employee@parent.com", company="Test Parent Company")
		employee2 = make_employee("test_employee@child.com", company="Test Child Company")

		# Test with descendants enabled - use Branch parameter (no company constraint)
		filters = frappe._dict({
			"company": "Test Parent Company",
			"parameter": "Branch",
			"include_company_descendants": 1,
		})
		report = execute(filters=filters)
		employees_in_report = [row[0] for row in report[1]]

		self.assertIn(employee1, employees_in_report)
		self.assertIn(employee2, employees_in_report)

		# Test with descendants disabled
		filters.include_company_descendants = 0
		report = execute(filters=filters)
		employees_in_report = [row[0] for row in report[1]]

		self.assertIn(employee1, employees_in_report)
		self.assertNotIn(employee2, employees_in_report)


def test_data(self, values_to_assert, chart_data):
	values = list(zip(chart_data["labels"], chart_data["datasets"][0]["values"], strict=False))

	self.assertCountEqual(chart_data["labels"], values_to_assert.keys())

	for label, value in values:
		self.assertEqual(value, values_to_assert.get(label))


def create_employee_grade():
	records = [
		{"doctype": "Employee Grade", "name": "1"},
		{"doctype": "Employee Grade", "name": "2"},
	]
	make_records(records)


def create_branches():
	records = [
		{"doctype": "Branch", "branch": "Test Branch 1"},
		{"doctype": "Branch", "branch": "Test Branch 2"},
	]
	make_records(records)


def get_employees_without_set_parameter(parameter, company):
	return frappe.db.count("Employee", {parameter: ("is", "not set"), "company": company, "status": "Active"})
