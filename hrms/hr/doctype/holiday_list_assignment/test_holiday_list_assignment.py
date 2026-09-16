# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from contextlib import contextmanager

import frappe
from frappe.utils import add_days, add_months, get_year_ending, get_year_start, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import DuplicateAssignment
from hrms.tests.utils import HRMSTestSuite
from hrms.utils.holiday_list import (
	get_holiday_list_for_employee,
	get_holiday_list_ranges_for_employee,
	get_holiday_list_ranges_for_employees,
	get_holidays_in_ranges_map,
)


class IntegrationTestHolidayListAssignment(HRMSTestSuite):
	"""
	Integration tests for HolidayListAssignment.
	Use this class for testing interactions between multiple components.
	"""

	def setUp(self):
		for d in ["Holiday List Assignment"]:
			frappe.db.delete(d)

		self.holiday_list = make_holiday_list(
			list_name="Test HLA", from_date=get_year_start(getdate()), to_date=get_year_ending(getdate())
		)
		self.employee = frappe.get_value("Employee", {"first_name": "_Test Employee"}, "name")

	def test_exisitng_assignment(self):
		from_date = get_year_start(getdate())
		create_holiday_list_assignment(
			"Employee",
			assigned_to=self.employee,
			holiday_list=self.holiday_list,
			from_date=from_date,
		)

		self.assertRaises(
			DuplicateAssignment,
			create_holiday_list_assignment,
			"Employee",
			assigned_to=self.employee,
			from_date=from_date,
		)

	def test_fetch_correct_holiday_list_assignment(self):
		employee = make_employee("test_hla@example.com", company="_Test Company")
		new_holiday_list = make_holiday_list(
			list_name="Test HLA New", from_date=get_year_start(getdate()), to_date=get_year_ending(getdate())
		)
		create_holiday_list_assignment(
			"Employee",
			assigned_to=employee,
			holiday_list=self.holiday_list,
			from_date=get_year_start(getdate()),
		)
		create_holiday_list_assignment(
			"Employee",
			assigned_to=employee,
			holiday_list=new_holiday_list,
			from_date=add_months(get_year_start(getdate()), 6),
		)
		applicable_holiday_list = get_holiday_list_for_employee(
			employee=employee, as_on=add_months(get_year_start(getdate()), 7)
		)
		self.assertEqual(applicable_holiday_list, "Test HLA New")

	def test_default_to_company_holiday_list_assignment(self):
		create_holiday_list_assignment("Company", "_Test Company", self.holiday_list)
		employee = make_employee("test_default_hla@example.com", company="_Test Company")
		holiday_list = get_holiday_list_for_employee(employee, as_on=getdate())
		self.assertEqual(holiday_list, self.holiday_list)

	def test_dates_before_first_assignment_fall_back_to_earliest_assignment(self):
		employee = make_employee("test_hla_fallback@example.com", company="_Test Company")
		year_start = get_year_start(getdate())
		create_holiday_list_assignment(
			"Employee", employee, self.holiday_list, from_date=add_months(year_start, 6)
		)

		self.assertEqual(get_holiday_list_for_employee(employee, as_on=year_start), self.holiday_list)
		self.assertEqual(
			get_holiday_list_for_employee(employee, as_on=add_months(year_start, -12)), self.holiday_list
		)

	def test_holidays_in_ranges_map_restricts_each_key_to_its_ranges(self):
		year_start = get_year_start(getdate())
		other_holiday_list = make_holiday_list(
			list_name="Test HLA Holidays Map", from_date=year_start, to_date=get_year_ending(getdate())
		)
		for holiday_list in (self.holiday_list, other_holiday_list):
			doc = frappe.get_doc("Holiday List", holiday_list)
			doc.append("holidays", {"holiday_date": add_days(year_start, 1), "description": holiday_list})
			doc.append("holidays", {"holiday_date": add_days(year_start, 40), "description": holiday_list})
			doc.save()

		holidays = get_holidays_in_ranges_map(
			{
				"first": [
					{
						"holiday_list": self.holiday_list,
						"from_date": year_start,
						"to_date": add_days(year_start, 30),
					},
					{
						"holiday_list": other_holiday_list,
						"from_date": add_days(year_start, 31),
						"to_date": add_days(year_start, 60),
					},
				],
				"second": [
					{
						"holiday_list": other_holiday_list,
						"from_date": year_start,
						"to_date": add_days(year_start, 30),
					}
				],
				"none": [],
			},
			skip_weekly_offs=True,
		)

		self.assertEqual(
			[(h.parent, h.holiday_date) for h in holidays["first"]],
			[(self.holiday_list, add_days(year_start, 1)), (other_holiday_list, add_days(year_start, 40))],
		)
		self.assertEqual(
			[(h.parent, h.holiday_date) for h in holidays["second"]],
			[(other_holiday_list, add_days(year_start, 1))],
		)
		self.assertNotIn("none", holidays)

	def test_bulk_and_scalar_resolution_agree_for_backdated_periods(self):
		employee = make_employee("test_hla_backdated@example.com", company="_Test Company")
		year_start = get_year_start(getdate())
		period_start, period_end = add_months(year_start, -12), add_days(add_months(year_start, -11), -1)
		create_holiday_list_assignment(
			"Employee", employee, self.holiday_list, from_date=add_months(year_start, 6)
		)

		# no company assignment: both paths fall back to the employee's earliest assignment
		ranges = get_holiday_list_ranges_for_employees({employee: "_Test Company"}, period_start, period_end)
		self.assertEqual(
			ranges,
			{
				employee: [
					{"holiday_list": self.holiday_list, "from_date": period_start, "to_date": period_end}
				]
			},
		)
		self.assertEqual(
			get_holiday_list_for_employee(employee, as_on=period_start), ranges[employee][0]["holiday_list"]
		)

		# company assignment covering the period: both paths use it
		company_holiday_list = make_holiday_list(
			list_name="Test HLA Backdated Company", from_date=period_start, to_date=period_end
		)
		create_holiday_list_assignment(
			"Company", "_Test Company", company_holiday_list, from_date=period_start
		)
		ranges = get_holiday_list_ranges_for_employees({employee: "_Test Company"}, period_start, period_end)
		self.assertEqual(ranges[employee][0]["holiday_list"], company_holiday_list)
		self.assertEqual(get_holiday_list_for_employee(employee, as_on=period_start), company_holiday_list)

	def test_holiday_list_ranges_split_on_assignment_change(self):
		employee = make_employee("test_hla_ranges@example.com", company="_Test Company")
		year_start = get_year_start(getdate())
		new_holiday_list = make_holiday_list(
			list_name="Test HLA Ranges", from_date=year_start, to_date=get_year_ending(getdate())
		)
		create_holiday_list_assignment("Employee", employee, self.holiday_list, from_date=year_start)
		create_holiday_list_assignment(
			"Employee", employee, new_holiday_list, from_date=add_months(year_start, 6)
		)

		ranges = get_holiday_list_ranges_for_employee(
			employee, add_months(year_start, 5), add_days(add_months(year_start, 7), -1)
		)
		self.assertEqual(
			ranges,
			[
				{
					"holiday_list": self.holiday_list,
					"from_date": add_months(year_start, 5),
					"to_date": add_days(add_months(year_start, 6), -1),
				},
				{
					"holiday_list": new_holiday_list,
					"from_date": add_months(year_start, 6),
					"to_date": add_days(add_months(year_start, 7), -1),
				},
			],
		)

		ranges = get_holiday_list_ranges_for_employee(
			employee, add_months(year_start, 1), add_months(year_start, 2)
		)
		self.assertEqual(
			ranges,
			[
				{
					"holiday_list": self.holiday_list,
					"from_date": add_months(year_start, 1),
					"to_date": add_months(year_start, 2),
				}
			],
		)

	def test_holiday_list_ranges_include_assignments_inside_the_range(self):
		employee = make_employee("test_hla_inner_ranges@example.com", company="_Test Company")
		year_start = get_year_start(getdate())
		year_end = get_year_ending(getdate())
		inner_holiday_list = make_holiday_list(
			list_name="Test HLA Inner", from_date=year_start, to_date=year_end
		)
		# A -> B -> A: B is active only in the middle of the range
		create_holiday_list_assignment("Employee", employee, self.holiday_list, from_date=year_start)
		create_holiday_list_assignment(
			"Employee", employee, inner_holiday_list, from_date=add_months(year_start, 3)
		)
		frappe.get_doc(
			{
				"doctype": "Holiday List Assignment",
				"applicable_for": "Employee",
				"assigned_to": employee,
				"holiday_list": self.holiday_list,
				"from_date": add_months(year_start, 6),
			}
		).submit()

		ranges = get_holiday_list_ranges_for_employee(employee, year_start, year_end)
		self.assertEqual(
			ranges,
			[
				{
					"holiday_list": self.holiday_list,
					"from_date": year_start,
					"to_date": add_days(add_months(year_start, 3), -1),
				},
				{
					"holiday_list": inner_holiday_list,
					"from_date": add_months(year_start, 3),
					"to_date": add_days(add_months(year_start, 6), -1),
				},
				{
					"holiday_list": self.holiday_list,
					"from_date": add_months(year_start, 6),
					"to_date": year_end,
				},
			],
		)

	def test_holiday_list_ranges_after_holiday_list_expiry(self):
		employee = make_employee("test_hla_expired_ranges@example.com", company="_Test Company")
		year_start = get_year_start(getdate())
		year_end = get_year_ending(getdate())
		expiring_holiday_list = make_holiday_list(
			list_name="Test HLA Expiring",
			from_date=year_start,
			to_date=add_days(add_months(year_start, 6), -1),
		)
		create_holiday_list_assignment("Employee", employee, expiring_holiday_list, from_date=year_start)

		# the expired list stays in effect until the next assignment starts, even when a company
		# assignment covers the remaining period, matching get_holiday_list_for_employee
		create_holiday_list_assignment("Company", "_Test Company", self.holiday_list, from_date=year_start)
		ranges = get_holiday_list_ranges_for_employee(employee, year_start, year_end)
		self.assertEqual(
			ranges,
			[{"holiday_list": expiring_holiday_list, "from_date": year_start, "to_date": year_end}],
		)
		self.assertEqual(get_holiday_list_for_employee(employee, as_on=year_end), expiring_holiday_list)

	def test_bulk_holiday_list_ranges_fall_back_to_company(self):
		employee = make_employee("test_hla_bulk_ranges@example.com", company="_Test Company")
		year_start = get_year_start(getdate())
		year_end = get_year_ending(getdate())
		employee_holiday_list = make_holiday_list(
			list_name="Test HLA Bulk Ranges", from_date=year_start, to_date=year_end
		)
		create_holiday_list_assignment("Company", "_Test Company", self.holiday_list, from_date=year_start)
		create_holiday_list_assignment(
			"Employee", employee, employee_holiday_list, from_date=add_months(year_start, 6)
		)

		ranges = get_holiday_list_ranges_for_employees({employee: "_Test Company"}, year_start, year_end)
		self.assertEqual(
			ranges,
			{
				employee: [
					{
						"holiday_list": self.holiday_list,
						"from_date": year_start,
						"to_date": add_days(add_months(year_start, 6), -1),
					},
					{
						"holiday_list": employee_holiday_list,
						"from_date": add_months(year_start, 6),
						"to_date": year_end,
					},
				]
			},
		)


def create_holiday_list_assignment(
	applicable_for,
	assigned_to,
	holiday_list="Salary Slip Test Holiday List",
	company="_Test Company",
	do_not_submit=False,
	from_date=None,
):
	if not frappe.db.exists(
		"Holiday List Assignment",
		{"applicable_for": applicable_for, "assigned_to": assigned_to, "holiday_list": holiday_list},
	):
		hla = frappe.new_doc("Holiday List Assignment")
		hla.applicable_for = applicable_for
		hla.assigned_to = assigned_to
		hla.holiday_list = holiday_list
		hla.employee_company = company
		if not from_date:
			from_date = frappe.db.get_value("Holiday List", holiday_list, "from_date")
		hla.from_date = from_date
		hla.save()
		if do_not_submit:
			return hla
		hla.submit()
	else:
		hla = frappe.get_doc(
			"Holiday List Assignment",
			{"applicable_for": applicable_for, "assigned_to": assigned_to, "holiday_list": holiday_list},
		)
	return hla


@contextmanager
def assign_holiday_list(holiday_list, company_name):
	"""
	Context manager for assigning holiday list in tests
	"""
	HolidayList = frappe.qb.DocType("Holiday List")
	HolidayListAssignment = frappe.qb.DocType("Holiday List Assignment")
	try:
		previous_assignment = (
			frappe.qb.from_(HolidayListAssignment)
			.join(HolidayList)
			.on(HolidayListAssignment.holiday_list == HolidayList.name)
			.select(HolidayListAssignment.name, HolidayListAssignment.holiday_list, HolidayList.from_date)
			.where(HolidayListAssignment.assigned_to == company_name)
			.limit(1)
		).run(as_dict=True)[0]
		from_date = frappe.get_value("Holiday List", holiday_list, "from_date")
		frappe.db.set_value(
			"Holiday List Assignment",
			previous_assignment.name,
			{"holiday_list": holiday_list, "from_date": from_date},
		)
		yield

	finally:
		# restore holiday list setup
		frappe.db.set_value(
			"Holiday List Assignment",
			previous_assignment.name,
			{"holiday_list": previous_assignment.holiday_list, "from_date": previous_assignment.from_date},
		)
