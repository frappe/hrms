import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.staffing_plan.test_staffing_plan import make_company
from hrms.hr.report.employee_birthday.employee_birthday import execute


class TestEmployeeBirthday(IntegrationTestCase):
	def setUp(self):
		make_company(name="_New Test Company", abbr="_NTC")
		self.company = "_New Test Company"
		self.birthdate = getdate().replace(year=1990)

	def test_employee_birth_day_report(self):
		employee_1 = make_employee(
			"test_employee_birth_day1@example.com", company=self.company, date_of_birth=self.birthdate
		)
		employee_2 = make_employee(
			"test_employee_birth_day2@example.com", company=self.company, date_of_birth=self.birthdate
		)
		employee_3 = make_employee(
			"test_employee_birth_day3@example.com", company=self.company, date_of_birth=self.birthdate
		)

		filters = frappe._dict(
			{
				"month": self.birthdate.strftime("%b"),
				"company": self.company,
			}
		)
		data = execute(filters=filters)[1]
		self.assertEqual(len(data), 3)
		self.assertEqual(data[0][0], employee_1)
		self.assertEqual(data[1][0], employee_2)
		self.assertEqual(data[2][0], employee_3)

	def test_user_permissions_on_employees(self):
		employee_1 = make_employee(
			"test_employee_birth_day1@example.com", company=self.company, date_of_birth=self.birthdate
		)
		make_employee(
			"test_employee_birth_day2@example.com",
			company=self.company,
			date_of_birth=self.birthdate,
			reports_to=employee_1,
		)

		frappe.set_user("test_employee_birth_day1@example.com")
		filters = frappe._dict(
			{
				"month": self.birthdate.strftime("%b"),
				"company": self.company,
			}
		)
		data = execute(filters=filters)[1]
		self.assertEqual(len(data), 2)

		frappe.set_user("test_employee_birth_day2@example.com")
		data = execute(filters=filters)[1]
		self.assertEqual(len(data), 1)
