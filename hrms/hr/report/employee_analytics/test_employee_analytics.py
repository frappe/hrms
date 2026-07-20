import frappe
from frappe import _
from frappe.desk.page.setup_wizard.setup_wizard import make_records

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.report.employee_analytics.employee_analytics import execute
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeAnalytics(HRMSTestSuite):
	def setUp(self):
		create_branches()
		create_employee_grade()

	def test_branches(self):
		# Use a standalone company so the is_group expansion does not pull in other test data
		standalone_company = create_company("_Test Analytics Standalone Company")

		make_employee("test_analytics1@example.com", company=standalone_company, branch="Test Branch 1")
		make_employee("test_analytics2@example.com", company=standalone_company, branch="Test Branch 2")
		make_employee("test_analytics3@example.com", company=standalone_company, branch="Test Branch 2")

		employees_with_no_branch = get_employees_without_set_parameter("branch", standalone_company)

		filters = frappe._dict({"company": standalone_company, "parameter": "Branch"})

		report = execute(filters=filters)
		employees_in_report = report[1]
		self.assertEqual(len(employees_in_report), 3)

		chart_data = report[3]["data"]

		values_to_assert = {"Test Branch 1": 1, "Test Branch 2": 2, "Not Set": employees_with_no_branch}
		test_data(self, values_to_assert, chart_data)

	def test_employee_grade(self):
		# Use a standalone company so the is_group expansion does not pull in other test data
		standalone_company = create_company("_Test Analytics Standalone Company")

		make_employee("test_analytics1@example.com", company=standalone_company, grade="1")
		make_employee("test_analytics2@example.com", company=standalone_company, grade="2")
		make_employee("test_analytics3@example.com", company=standalone_company, grade="2")

		employees_with_no_grade = get_employees_without_set_parameter("grade", standalone_company)
		values_to_assert = {"1": 1, "2": 2, "Not Set": employees_with_no_grade}
		filters = frappe._dict({"company": standalone_company, "parameter": "Grade"})
		report = execute(filters=filters)

		chart_data = report[3]["data"]
		test_data(self, values_to_assert, chart_data)

	def test_group_company(self):
		parent_company = create_company("_Test Group Company", is_group=1)
		child_company_1 = create_company("_Test Child Company 1", parent_company=parent_company)
		child_company_2 = create_company("_Test Child Company 2", parent_company=parent_company)

		make_employee("test_group1@example.com", company=parent_company, branch="Test Branch 1")
		make_employee("test_group2@example.com", company=child_company_1, branch="Test Branch 1")
		make_employee("test_group3@example.com", company=child_company_2, branch="Test Branch 2")

		filters = frappe._dict({"company": parent_company, "parameter": "Branch"})
		report = execute(filters=filters)
		employees_in_report = report[1]

		self.assertEqual(len(employees_in_report), 3)

		chart_data = report[3]["data"]
		branch_1_idx = chart_data["labels"].index("Test Branch 1")
		branch_2_idx = chart_data["labels"].index("Test Branch 2")
		self.assertEqual(chart_data["datasets"][0]["values"][branch_1_idx], 2)
		self.assertEqual(chart_data["datasets"][0]["values"][branch_2_idx], 1)

		# selecting a child company should show only that company's data
		filters_child = frappe._dict({"company": child_company_1, "parameter": "Branch"})
		report_child = execute(filters=filters_child)
		self.assertEqual(len(report_child[1]), 1)


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


def create_company(company_name, parent_company=None, is_group=0):
	if frappe.db.exists("Company", company_name):
		return company_name

	doc = {
		"doctype": "Company",
		"company_name": company_name,
		"country": "India",
		"default_currency": "INR",
		"create_chart_of_accounts_based_on": "Standard Template",
		"chart_of_accounts": "Standard",
		"is_group": is_group,
	}
	if parent_company:
		doc["parent_company"] = parent_company

	return frappe.get_doc(doc).save().name
