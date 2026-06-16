import frappe
from frappe.utils import add_days, getdate

from hrms.api.roster import get_shifts
from hrms.tests.utils import HRMSTestSuite


class TestRoster(HRMSTestSuite):
	def test_get_shifts_returns_shift_type_details(self):
		date = getdate()
		employee_name = f"_Test Roster Employee {frappe.generate_hash(length=8)}"
		employee = create_employee(employee_name)
		shift_type = create_shift_type(
			f"_Test Roster Shift {frappe.generate_hash(length=8)}",
			start_time="10:00:00",
			end_time="18:00:00",
			color="Violet",
		)
		shift_assignment = create_shift_assignment(shift_type.name, employee.name, date)

		shifts = get_shifts(add_days(date, -1), add_days(date, 1), {"employee_name": employee_name}, {})

		self.assertEqual(len(shifts[employee.name]), 1)
		self.assertEqual(shifts[employee.name][0]["name"], shift_assignment.name)
		self.assertEqual(str(shifts[employee.name][0]["start_time"]), "10:00:00")
		self.assertEqual(str(shifts[employee.name][0]["end_time"]), "18:00:00")
		self.assertEqual(shifts[employee.name][0]["color"], "Violet")


def create_employee(employee_name: str):
	create_company()
	if not frappe.db.exists("Gender", "Female"):
		frappe.get_doc({"doctype": "Gender", "gender": "Female"}).insert()

	return frappe.get_doc(
		{
			"doctype": "Employee",
			"first_name": employee_name,
			"company": "_Test Company",
			"gender": "Female",
			"date_of_birth": "1990-01-01",
			"date_of_joining": "2020-01-01",
			"status": "Active",
		}
	).insert()


def create_company():
	if frappe.db.exists("Company", "_Test Company"):
		return

	frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": "_Test Company",
			"default_currency": "INR",
			"country": "India",
		}
	).insert()


def create_shift_type(shift_type: str, start_time: str, end_time: str, color: str):
	return frappe.get_doc(
		{
			"doctype": "Shift Type",
			"__newname": shift_type,
			"start_time": start_time,
			"end_time": end_time,
			"color": color,
		}
	).insert()


def create_shift_assignment(shift_type: str, employee: str, date: str):
	shift_assignment = frappe.get_doc(
		{
			"doctype": "Shift Assignment",
			"employee": employee,
			"company": "_Test Company",
			"shift_type": shift_type,
			"start_date": date,
			"end_date": date,
		}
	)
	shift_assignment.submit()
	return shift_assignment
