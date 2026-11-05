import frappe
from frappe.utils import getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.staffing_plan.test_staffing_plan import make_company
from hrms.hr.report.employee_birthday.employee_birthday import execute
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeBirthday(HRMSTestSuite):
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

	def test_sorted_by_day_of_birth(self):
		employees = [
			make_employee(
				f"test_employee_birth_day{day}@example.com",
				company=self.company,
				date_of_birth=self.birthdate.replace(day=day),
			)
			for day in (28, 2, 15)
		]

		filters = frappe._dict({"month": self.birthdate.strftime("%b"), "company": self.company})
		data = execute(filters=filters)[1]
		self.assertEqual([row[0] for row in data], [employees[1], employees[2], employees[0]])

	def test_mandatory_filters(self):
		self.assertRaises(frappe.ValidationError, execute, frappe._dict({"month": "Jan"}))
		self.assertRaises(frappe.ValidationError, execute, frappe._dict({"company": self.company}))
