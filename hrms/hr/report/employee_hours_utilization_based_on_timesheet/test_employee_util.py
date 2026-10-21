from unittest.mock import patch

import frappe
from frappe.utils.make_random import get_random

from erpnext.projects.doctype.project.test_project import make_project
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.holiday_list_assignment.test_holiday_list_assignment import (
	create_holiday_list_assignment,
)
from hrms.hr.report.employee_hours_utilization_based_on_timesheet.employee_hours_utilization_based_on_timesheet import (
	EmployeeHoursReport,
	execute,
)
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeUtilization(HRMSTestSuite):
	def setUp(self):
		# Create test employee
		self.test_emp1 = make_employee("test1@employeeutil.com", "_Test Company")
		self.test_emp2 = make_employee("test2@employeeutil.com", "_Test Company")

		self.holiday_list = self.make_holiday_list()
		for employee in (self.test_emp1, self.test_emp2):
			create_holiday_list_assignment("Employee", employee, self.holiday_list, from_date="2021-01-01")

		# Create test project
		self.test_project = make_project({"project_name": "_Test Project"})

		# Create test timesheets
		self.create_test_timesheets()

		frappe.db.set_single_value("HR Settings", "standard_working_hours", 9)

	def make_holiday_list(self):
		name = "Employee Util Test Holidays"
		if not frappe.db.exists("Holiday List", name):
			frappe.get_doc(
				{
					"doctype": "Holiday List",
					"holiday_list_name": name,
					"from_date": "2021-01-01",
					"to_date": "2021-12-31",
				}
			).insert()
		return name

	def create_test_timesheets(self):
		timesheet1 = frappe.new_doc("Timesheet")
		timesheet1.employee = self.test_emp1
		timesheet1.company = "_Test Company"

		timesheet1.append(
			"time_logs",
			{
				"activity_type": get_random("Activity Type"),
				"hours": 5,
				"is_billable": 1,
				"from_time": "2021-04-01 13:30:00.000000",
				"to_time": "2021-04-01 18:30:00.000000",
			},
		)

		timesheet1.save()
		timesheet1.submit()

		timesheet2 = frappe.new_doc("Timesheet")
		timesheet2.employee = self.test_emp2
		timesheet2.company = "_Test Company"

		timesheet2.append(
			"time_logs",
			{
				"activity_type": get_random("Activity Type"),
				"hours": 10,
				"is_billable": 0,
				"from_time": "2021-04-01 13:30:00.000000",
				"to_time": "2021-04-01 23:30:00.000000",
				"project": self.test_project.name,
			},
		)

		timesheet2.save()
		timesheet2.submit()

	def test_utilization_report_with_required_filters_only(self):
		filters = {"company": "_Test Company", "from_date": "2021-04-01", "to_date": "2021-04-03"}

		report = execute(filters)

		expected_data = self.get_expected_data_for_test_employees()
		self.assertEqual(report[1], expected_data)

	def test_utilization_report_for_single_employee(self):
		filters = {
			"company": "_Test Company",
			"from_date": "2021-04-01",
			"to_date": "2021-04-03",
			"employee": self.test_emp1,
		}

		report = execute(filters)

		emp1_data = frappe.get_doc("Employee", self.test_emp1)
		expected_data = [
			{
				"employee": self.test_emp1,
				"employee_name": "test1@employeeutil.com",
				"billed_hours": 5.0,
				"non_billed_hours": 0.0,
				"department": emp1_data.department,
				"total_hours": 27.0,
				"untracked_hours": 22.0,
				"per_util": 18.52,
				"per_util_billed_only": 18.52,
			}
		]

		self.assertEqual(report[1], expected_data)

	def test_utilization_report_for_project(self):
		filters = {
			"company": "_Test Company",
			"from_date": "2021-04-01",
			"to_date": "2021-04-03",
			"project": self.test_project.name,
		}

		report = execute(filters)

		emp2_data = frappe.get_doc("Employee", self.test_emp2)
		expected_data = [
			{
				"employee": self.test_emp2,
				"employee_name": "test2@employeeutil.com",
				"billed_hours": 0.0,
				"non_billed_hours": 10.0,
				"department": emp2_data.department,
				"total_hours": 27.0,
				"untracked_hours": 17.0,
				"per_util": 37.04,
				"per_util_billed_only": 0.0,
			}
		]

		self.assertEqual(report[1], expected_data)

	def test_utilization_report_for_department(self):
		emp1_data = frappe.get_doc("Employee", self.test_emp1)
		filters = {
			"company": "_Test Company",
			"from_date": "2021-04-01",
			"to_date": "2021-04-03",
			"department": emp1_data.department,
		}

		report = execute(filters)

		expected_data = self.get_expected_data_for_test_employees()
		self.assertEqual(report[1], expected_data)

	def test_report_summary_data(self):
		filters = {"company": "_Test Company", "from_date": "2021-04-01", "to_date": "2021-04-03"}

		report = execute(filters)
		summary = report[4]
		expected_summary_values = ["27.78%", "9.26%", 5.0, 10.0]

		self.assertEqual(len(summary), 4)

		for i in range(4):
			self.assertEqual(summary[i]["value"], expected_summary_values[i])

	def test_employee_metadata_is_fetched_in_one_query(self):
		report = EmployeeHoursReport.__new__(EmployeeHoursReport)
		report.stats_by_employee = frappe._dict({self.test_emp1: {}, self.test_emp2: {}})

		with patch.object(frappe, "get_list", wraps=frappe.get_list) as get_list:
			report.set_employee_department_and_name()

		self.assertEqual([c.args[0] for c in get_list.call_args_list].count("Employee"), 1)
		self.assertEqual(report.stats_by_employee[self.test_emp1]["employee_name"], "test1@employeeutil.com")
		self.assertEqual(report.stats_by_employee[self.test_emp2]["employee_name"], "test2@employeeutil.com")

	def test_only_submitted_time_logs_within_period_are_counted(self):
		def make_timesheet(time_logs, submit=True, cancel=False):
			timesheet = frappe.new_doc("Timesheet")
			timesheet.employee = self.test_emp1
			timesheet.company = "_Test Company"
			for from_time, hours in time_logs:
				timesheet.append(
					"time_logs",
					{"activity_type": get_random("Activity Type"), "hours": hours, "from_time": from_time},
				)
			timesheet.save()
			if submit:
				timesheet.submit()
			if cancel:
				timesheet.cancel()

		make_timesheet([("2021-04-02 09:00:00", 3)], submit=False)
		make_timesheet([("2021-04-02 13:00:00", 3)], cancel=True)
		make_timesheet([("2021-03-30 09:00:00", 4), ("2021-04-03 09:00:00", 2)])

		filters = {
			"company": "_Test Company",
			"from_date": "2021-04-01",
			"to_date": "2021-04-03",
			"employee": self.test_emp1,
		}
		row = execute(filters)[1][0]
		self.assertEqual(row["billed_hours"], 5.0)
		self.assertEqual(row["non_billed_hours"], 2.0)
		self.assertEqual(row["total_hours"], 27.0)

		filters.update({"from_date": "2021-04-01", "to_date": "2021-04-01"})
		row = execute(filters)[1][0]
		self.assertEqual(row["total_hours"], 9.0)
		self.assertEqual(row["non_billed_hours"], 0.0)

	def test_chart_and_summary_respect_user_permissions(self):
		from frappe.desk.query_report import run
		from frappe.permissions import add_user_permission

		user = "employeeutil_restricted@example.com"
		make_employee(user, "_Test Company")
		frappe.get_doc("User", user).add_roles("HR User")
		add_user_permission("Employee", self.test_emp1, user)

		frappe.set_user(user)
		try:
			report = run(
				"Employee Hours Utilization Based On Timesheet",
				filters={"company": "_Test Company", "from_date": "2021-04-01", "to_date": "2021-04-03"},
			)
		finally:
			frappe.set_user("Administrator")

		self.assertEqual([row["employee"] for row in report["result"]], [self.test_emp1])
		self.assertEqual(report["chart"]["data"]["labels"], ["test1@employeeutil.com"])
		summary = {d["label"]: d["value"] for d in report["report_summary"]}
		self.assertEqual(summary["Total Non-Billed Hours"], 0.0)

	def test_holidays_are_excluded_from_total_hours(self):
		holiday_list = frappe.get_doc("Holiday List", self.holiday_list)
		holiday_list.append("holidays", {"holiday_date": "2021-04-02", "description": "Test Holiday"})
		holiday_list.save()

		filters = {
			"company": "_Test Company",
			"from_date": "2021-04-01",
			"to_date": "2021-04-03",
			"employee": self.test_emp1,
		}
		row = execute(filters)[1][0]
		self.assertEqual(row["total_hours"], 18.0)
		self.assertEqual(row["untracked_hours"], 13.0)
		self.assertEqual(row["per_util"], 27.78)

		timesheet = frappe.new_doc("Timesheet")
		timesheet.employee = self.test_emp1
		timesheet.company = "_Test Company"
		timesheet.append(
			"time_logs",
			{"activity_type": get_random("Activity Type"), "hours": 2, "from_time": "2021-04-02 09:00:00"},
		)
		timesheet.save()
		timesheet.submit()

		filters.update({"from_date": "2021-04-02", "to_date": "2021-04-02"})
		row = execute(filters)[1][0]
		self.assertEqual(row["total_hours"], 0.0)
		self.assertEqual(row["per_util"], 0.0)

	def get_expected_data_for_test_employees(self):
		emp1_data = frappe.get_doc("Employee", self.test_emp1)
		emp2_data = frappe.get_doc("Employee", self.test_emp2)

		return [
			{
				"employee": self.test_emp2,
				"employee_name": "test2@employeeutil.com",
				"billed_hours": 0.0,
				"non_billed_hours": 10.0,
				"department": emp2_data.department,
				"total_hours": 27.0,
				"untracked_hours": 17.0,
				"per_util": 37.04,
				"per_util_billed_only": 0.0,
			},
			{
				"employee": self.test_emp1,
				"employee_name": "test1@employeeutil.com",
				"billed_hours": 5.0,
				"non_billed_hours": 0.0,
				"department": emp1_data.department,
				"total_hours": 27.0,
				"untracked_hours": 22.0,
				"per_util": 18.52,
				"per_util_billed_only": 18.52,
			},
		]
