# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from contextlib import contextmanager

import frappe
from frappe.utils import add_months, get_year_ending, get_year_start, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import DuplicateAssignment
from hrms.tests.utils import HRMSTestSuite
from hrms.utils.holiday_list import get_holiday_list_for_employee

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list


class IntegrationTestHolidayListAssignment(HRMSTestSuite):
	"""
	Integration tests for HolidayListAssignment.
	Use this class for testing interactions between multiple components.
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.make_employees()

	def setUp(self):
		for d in ["Holiday List Assignment"]:
			frappe.db.delete(d)

		self.holiday_list = make_holiday_list(
			list_name="Test HLA", from_date=get_year_start(getdate()), to_date=get_year_ending(getdate())
		)

	def test_exisitng_assignment(self):
		from_date = get_year_start(getdate())
		create_holiday_list_assignment(
			"Employee",
			assigned_to=self.employees[0].name,
			holiday_list=self.holiday_list,
			from_date=from_date,
		)

		self.assertRaises(
			DuplicateAssignment,
			create_holiday_list_assignment,
			"Employee",
			assigned_to=self.employees[0].name,
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
