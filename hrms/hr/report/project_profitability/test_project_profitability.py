import frappe
from frappe.utils import add_days, flt, getdate

from erpnext.projects.doctype.timesheet.test_timesheet import make_timesheet
from erpnext.projects.doctype.timesheet.timesheet import make_sales_invoice
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.report.project_profitability.project_profitability import execute
from hrms.payroll.doctype.salary_slip.salary_slip import make_salary_slip_from_timesheet
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_salary_structure_for_timesheet
from hrms.tests.utils import HRMSTestSuite


class TestProjectProfitability(HRMSTestSuite):
	def setUp(self):
		emp = make_employee("test_employee_9@salary.com", company="_Test Company")

		frappe.db.set_single_value("HR Settings", "standard_working_hours", 8)
		frappe.db.set_single_value("Payroll Settings", "include_holidays_in_total_working_days", 0)

		if not frappe.db.exists("Salary Component", "Timesheet Component"):
			frappe.get_doc(
				{"doctype": "Salary Component", "salary_component": "Timesheet Component"}
			).insert()

		make_salary_structure_for_timesheet(emp, company="_Test Company")
		date = getdate()

		activity_type = create_activity_type("_Test Employee Timesheet")
		self.timesheet = make_timesheet(emp, is_billable=1, activity_type=activity_type)
		self.salary_slip = make_salary_slip_from_timesheet(self.timesheet.name)
		self.salary_slip.submit()

		self.sales_invoice = make_sales_invoice(
			self.timesheet.name, "_Test Item", "_Test Customer", currency="INR"
		)
		self.sales_invoice.due_date = date
		self.sales_invoice.submit()

	def test_project_profitability(self):
		filters = {
			"company": "_Test Company",
			"start_date": add_days(self.timesheet.start_date, -3),
			"end_date": add_days(self.timesheet.end_date, 1),
		}

		report = execute(filters)

		row = report[1][0]
		timesheet = frappe.get_doc("Timesheet", self.timesheet.name)

		self.assertEqual(self.sales_invoice.customer, row.customer)
		self.assertEqual(timesheet.employee_name, row.employee_name)
		self.assertEqual(
			flt(self.sales_invoice.timesheets[0].billing_amount * self.sales_invoice.conversion_rate),
			row.base_grand_total,
		)
		self.assertEqual(self.salary_slip.base_gross_pay, row.base_gross_pay)
		self.assertEqual(timesheet.total_billed_hours, row.total_billed_hours)
		self.assertEqual(self.salary_slip.total_working_days, row.total_working_days)
		self.assertEqual(self.salary_slip.name, row.salary_slip)
		self.assertEqual(
			frappe.get_cached_value("Company", "_Test Company", "default_currency"), row.currency
		)

		standard_working_hours = frappe.db.get_single_value("HR Settings", "standard_working_hours")
		utilization = timesheet.total_billed_hours / (
			self.salary_slip.total_working_days * standard_working_hours
		)

		self.assertEqual(flt(utilization * 100, 2), row.utilization)

		fractional_cost = flt(self.salary_slip.base_gross_pay * utilization, 2)
		self.assertEqual(fractional_cost, row.fractional_cost)

		profit = flt(row.base_grand_total - fractional_cost, 2)
		self.assertEqual(profit, row.profit)

	def test_cost_hidden_without_salary_slip_permission(self):
		from frappe.desk.query_report import run

		user = "project_profitability_projects_user@example.com"
		if not frappe.db.exists("User", user):
			frappe.get_doc(
				{"doctype": "User", "email": user, "first_name": "Projects", "send_welcome_email": 0}
			).insert()
		frappe.get_doc("User", user).add_roles("Projects User")

		filters = {
			"company": "_Test Company",
			"start_date": add_days(self.timesheet.start_date, -3),
			"end_date": add_days(self.timesheet.end_date, 1),
		}
		frappe.set_user(user)
		try:
			report = run("Project Profitability", filters=filters)
		finally:
			frappe.set_user("Administrator")

		fieldnames = {column["fieldname"] for column in report["columns"]}
		self.assertTrue(report["result"])
		self.assertFalse(fieldnames & {"base_gross_pay", "fractional_cost", "profit"})
		for row in report["result"]:
			self.assertFalse({"base_gross_pay", "fractional_cost", "profit"} & set(row))


def create_activity_type(activity_type: str) -> str:
	doc = frappe.new_doc("Activity Type")
	doc.activity_type = activity_type
	doc.insert()
	return doc.name
