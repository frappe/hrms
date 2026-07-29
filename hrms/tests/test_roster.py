import frappe
from frappe.utils import add_days, getdate

from hrms.api.roster import get_shifts, insert_shift
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

	def test_insert_shift_ignores_cancelled_assignment(self):
		"""Cancelled Shift Assignments should not block or be mutated by insert_shift."""
		employee_name = f"_Test Roster Cancel {frappe.generate_hash(length=8)}"
		employee = create_employee(employee_name)
		shift_type = create_shift_type(
			f"_Test Cancel Shift {frappe.generate_hash(length=8)}",
			start_time="08:00:00",
			end_time="17:00:00",
			color="Red",
		)

		# Create a shift assignment with a date range, submit it, then cancel it
		original = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"employee": employee.name,
				"company": "_Test Company",
				"shift_type": shift_type.name,
				"start_date": "2026-07-01",
				"end_date": "2026-07-10",
			}
		)
		original.submit()
		original.cancel()
		original.reload()
		self.assertEqual(original.docstatus, 2)
		original_end_date = original.end_date

		# Attempt to insert an adjacent shift (Jul 11 = day after Jul 10)
		insert_shift(
			employee=employee.name,
			company="_Test Company",
			shift_type=shift_type.name,
			start_date="2026-07-11",
			end_date="2026-07-20",
			status="Active",
		)

		# The cancelled record must remain untouched
		original.reload()
		self.assertEqual(original.end_date, original_end_date)

		# A new, non-cancelled assignment must exist for the new range
		new_assignment = frappe.db.exists(
			"Shift Assignment",
			{
				"employee": employee.name,
				"start_date": "2026-07-11",
				"end_date": "2026-07-20",
				"docstatus": ["!=", 2],
			},
		)
		self.assertTrue(new_assignment)

	def test_insert_shift_rejects_adjacent_submitted_shift(self):
		"""Submitted Shift Assignments should not be mutated. A new Draft should be created."""
		employee_name = f"_Test Roster Sub {frappe.generate_hash(length=8)}"
		employee = create_employee(employee_name)
		shift_type = create_shift_type(
			f"_Test Sub Shift {frappe.generate_hash(length=8)}",
			start_time="08:00:00",
			end_time="17:00:00",
			color="Blue",
		)

		original = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"employee": employee.name,
				"company": "_Test Company",
				"shift_type": shift_type.name,
				"start_date": "2026-07-01",
				"end_date": "2026-07-10",
				"status": "Active",
			}
		)
		original.submit()
		original_end_date = original.end_date

		insert_shift(
			employee=employee.name,
			company="_Test Company",
			shift_type=shift_type.name,
			start_date="2026-07-11",
			end_date="2026-07-20",
			status="Active",
		)

		original.reload()
		self.assertEqual(getdate(original.end_date), getdate(original_end_date))
		self.assertEqual(original.docstatus, 1)

		new_assignment = frappe.db.get_value(
			"Shift Assignment",
			{
				"employee": employee.name,
				"start_date": "2026-07-11",
				"end_date": "2026-07-20",
				"docstatus": 1,
			},
		)
		self.assertTrue(new_assignment)

	def test_insert_shift_rejects_merging_two_submitted_shifts(self):
		"""When inserted between two submitted shifts, neither should be deleted/mutated. A new Draft should be created in between."""
		employee_name = f"_Test Roster Merge {frappe.generate_hash(length=8)}"
		employee = create_employee(employee_name)
		shift_type = create_shift_type(
			f"_Test Merge Shift {frappe.generate_hash(length=8)}",
			start_time="08:00:00",
			end_time="17:00:00",
			color="Green",
		)

		left = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"employee": employee.name,
				"company": "_Test Company",
				"shift_type": shift_type.name,
				"start_date": "2026-07-01",
				"end_date": "2026-07-10",
				"status": "Active",
			}
		)
		left.submit()
		left_end_date = left.end_date

		right = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"employee": employee.name,
				"company": "_Test Company",
				"shift_type": shift_type.name,
				"start_date": "2026-07-21",
				"end_date": "2026-07-30",
				"status": "Active",
			}
		)
		right.submit()
		right_start_date = right.start_date

		insert_shift(
			employee=employee.name,
			company="_Test Company",
			shift_type=shift_type.name,
			start_date="2026-07-11",
			end_date="2026-07-20",
			status="Active",
		)

		left.reload()
		right.reload()
		self.assertEqual(getdate(left.end_date), getdate(left_end_date))
		self.assertEqual(getdate(right.start_date), getdate(right_start_date))

		new_assignment = frappe.db.get_value(
			"Shift Assignment",
			{
				"employee": employee.name,
				"start_date": "2026-07-11",
				"end_date": "2026-07-20",
				"docstatus": 1,
			},
		)
		self.assertTrue(new_assignment)


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

