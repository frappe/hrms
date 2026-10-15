import frappe

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.api import (
	get_company_currencies,
	get_expense_approval_details,
	get_holidays_for_employee,
	get_leave_approval_details,
	get_shift_request_approvers,
)
from hrms.overrides.employee_master import get_timeline_data
from hrms.tests.utils import HRMSTestSuite, make_company_restricted_user
from hrms.utils.holiday_list import get_holiday_list_for_employee


class TestAPI(HRMSTestSuite):
	def test_get_company_currencies_respects_company_scope(self):
		companies = get_company_currencies()
		self.assertIn("_Test Company", companies)
		self.assertIn("_Test Company 1", companies)
		self.assertEqual(
			companies["_Test Company"][0], frappe.db.get_value("Company", "_Test Company", "default_currency")
		)

		user = "test_scoped_employee@example.com"
		make_employee(user, company="_Test Company")
		make_company_restricted_user(user, "_Test Company", role="Employee")
		frappe.set_user(user)
		try:
			companies = get_company_currencies()
		finally:
			frappe.set_user("Administrator")

		self.assertEqual(list(companies), ["_Test Company"])

	def test_get_timeline_data_only_for_employee(self):
		employee = make_employee("test_timeline_employee@example.com", company="_Test Company")
		self.assertIn("timeline_data", get_timeline_data("Employee", employee))
		self.assertRaises(frappe.ValidationError, get_timeline_data, "Company", "_Test Company")

	def test_employee_can_load_own_holidays_and_approvers(self):
		user = "test_pwa_employee@example.com"
		employee = make_employee(user, company="_Test Company")
		self.assertTrue(frappe.db.get_value("Employee", employee, "department"))
		self.assertTrue(get_holiday_list_for_employee(employee, raise_exception=False))

		frappe.set_user(user)
		try:
			self.assertIsInstance(get_holidays_for_employee(employee), list)
			self.assertIn("department_approvers", get_leave_approval_details(employee))
			self.assertIn("department_approvers", get_expense_approval_details(employee))
			get_shift_request_approvers(employee)
		finally:
			frappe.set_user("Administrator")
