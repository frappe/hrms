# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from contextlib import contextmanager

import frappe
from frappe.utils import add_months, get_year_ending, get_year_start, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.salary_slip.salary_slip import HOLIDAYS_BETWEEN_DATES
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import DuplicateAssignment
from hrms.tests.utils import HRMSTestSuite
from hrms.utils.holiday_list import get_holiday_dates_between_range, get_holiday_list_for_employee


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

	def test_holiday_list_assignment_clears_salary_slip_holiday_cache(self):
		cache_key = "test-holiday-cache"
		frappe.cache().hset(HOLIDAYS_BETWEEN_DATES, cache_key, [getdate()])
		assignment = create_holiday_list_assignment("Company", "_Test Company", self.holiday_list)
		self.assertIsNone(frappe.cache().hget(HOLIDAYS_BETWEEN_DATES, cache_key))

		frappe.cache().hset(HOLIDAYS_BETWEEN_DATES, cache_key, [getdate()])
		assignment.cancel()
		self.assertIsNone(frappe.cache().hget(HOLIDAYS_BETWEEN_DATES, cache_key))

	def test_default_holiday_list_fallback(self):
		employee = make_employee("test_hla_default_fallback@example.com", company="_Test Company")
		employee_holiday_list = make_holiday_list("Test HLA Default Employee", "2024-01-01", "2024-12-31")
		company_holiday_list = make_holiday_list("Test HLA Default Company", "2024-01-01", "2024-12-31")
		frappe.db.set_value("Employee", employee, "holiday_list", employee_holiday_list)
		frappe.db.set_value("Company", "_Test Company", "default_holiday_list", company_holiday_list)

		self.assertEqual(get_holiday_list_for_employee(employee, as_on="2024-01-01"), employee_holiday_list)
		frappe.db.set_value("Employee", employee, "holiday_list", None)
		self.assertEqual(get_holiday_list_for_employee(employee, as_on="2024-01-01"), company_holiday_list)

	def test_holidays_across_all_assignment_ranges(self):
		employee = make_employee("test_hla_ranges@example.com", company="_Test Company")
		holiday_lists = [
			make_holiday_list(f"Test HLA Range {index}", "2026-01-01", "2026-01-31") for index in range(1, 4)
		]
		for holiday_list, holiday_date, from_date in zip(
			holiday_lists,
			["2026-01-05", "2026-01-15", "2026-01-25"],
			["2026-01-01", "2026-01-11", "2026-01-21"],
			strict=False,
		):
			add_holiday(holiday_list, holiday_date)
			create_holiday_list_assignment("Employee", employee, holiday_list, from_date=from_date)

		self.assertEqual(
			get_holiday_dates_between_range(employee, "2026-01-01", "2026-01-31", skip_weekly_offs=True),
			[getdate("2026-01-05"), getdate("2026-01-15"), getdate("2026-01-25")],
		)

	def test_company_assignment_fills_employee_assignment_gap(self):
		employee = make_employee("test_hla_company_gap@example.com", company="_Test Company")
		company_holiday_list = make_holiday_list("Test HLA Company Gap", "2026-01-01", "2026-01-31")
		employee_holiday_list = make_holiday_list("Test HLA Employee Gap", "2026-01-01", "2026-01-31")
		add_holiday(company_holiday_list, "2026-01-05")
		add_holiday(employee_holiday_list, "2026-01-20")
		create_holiday_list_assignment(
			"Company", "_Test Company", company_holiday_list, from_date="2026-01-01"
		)
		create_holiday_list_assignment("Employee", employee, employee_holiday_list, from_date="2026-01-16")

		self.assertEqual(
			get_holiday_dates_between_range(employee, "2026-01-01", "2026-01-31", skip_weekly_offs=True),
			[getdate("2026-01-05"), getdate("2026-01-20")],
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


def add_holiday(holiday_list, holiday_date):
	doc = frappe.get_doc("Holiday List", holiday_list)
	doc.append("holidays", {"holiday_date": holiday_date, "description": "Test Holiday"})
	doc.save()


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
