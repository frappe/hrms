import frappe

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.api import get_company_currencies
from hrms.tests.utils import HRMSTestSuite, make_company_restricted_user


class TestAPI(HRMSTestSuite):
	def tearDown(self):
		frappe.set_user("Administrator")

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

		companies = get_company_currencies()
		self.assertEqual(list(companies), ["_Test Company"])
