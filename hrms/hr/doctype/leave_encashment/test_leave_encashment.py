# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, get_year_ending, get_year_start, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee
from erpnext.setup.doctype.holiday_list.test_holiday_list import set_holiday_list

from hrms.hr.doctype.leave_period.test_leave_period import create_leave_period
from hrms.hr.doctype.leave_policy.test_leave_policy import create_leave_policy
from hrms.hr.doctype.leave_policy_assignment.leave_policy_assignment import (
	create_assignment_for_multiple_employees,
)
from hrms.payroll.doctype.salary_slip.test_salary_slip import (
	make_holiday_list,
	make_leave_application,
)
from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from hrms.tests.test_utils import get_first_sunday

test_records = frappe.get_test_records("Leave Type")


class TestLeaveEncashment(FrappeTestCase):
	def setUp(self):
		for dt in [
			"Leave Period",
			"Leave Policy Assignment",
			"Leave Allocation",
			"Leave Ledger Entry",
			"Additional Salary",
			"Leave Encashment",
			"Leave Application",
		]:
			frappe.db.delete(dt)

		self.leave_type = "_Test Leave Type Encashment"
		if frappe.db.exists("Leave Type", self.leave_type):
			frappe.delete_doc("Leave Type", self.leave_type, force=True)
		frappe.get_doc(test_records[2]).insert()

		date = getdate()
		year_start = getdate(get_year_start(date))
		year_end = getdate(get_year_ending(date))

		self.holiday_list = make_holiday_list("_Test Leave Encashment", year_start, year_end)

		# create the leave policy
		leave_policy = create_leave_policy(leave_type=self.leave_type, annual_allocation=10)
		leave_policy.submit()

		# create employee, salary structure and assignment
		self.employee = make_employee("test_employee_encashment@example.com", company="_Test Company")

		self.leave_period = create_leave_period(year_start, year_end, "_Test Company")

		data = {
			"assignment_based_on": "Leave Period",
			"leave_policy": leave_policy.name,
			"leave_period": self.leave_period.name,
		}

		leave_policy_assignments = create_assignment_for_multiple_employees(
			[self.employee], frappe._dict(data)
		)

		salary_structure = make_salary_structure(
			"Salary Structure for Encashment",
			"Monthly",
			self.employee,
			other_details={"leave_encashment_amount_per_day": 50},
		)

	@set_holiday_list("_Test Leave Encashment", "_Test Company")
	def test_leave_balance_value_and_amount(self):
		leave_encashment = frappe.get_doc(
			dict(
				doctype="Leave Encashment",
				employee=self.employee,
				leave_type="_Test Leave Type Encashment",
				leave_period=self.leave_period.name,
				encashment_date=self.leave_period.to_date,
				currency="INR",
			)
		).insert()

		self.assertEqual(leave_encashment.leave_balance, 10)
		self.assertTrue(leave_encashment.actual_encashable_days, 5)
		self.assertTrue(leave_encashment.encashment_days, 5)
		self.assertEqual(leave_encashment.encashment_amount, 250)

		# assert links
		leave_encashment.submit()
		self.assertIsNotNone(leave_encashment.leave_allocation)
		additional_salary_amount = frappe.db.get_value(
			"Additional Salary", {"ref_docname": leave_encashment.name}, "amount"
		)
		self.assertEqual(additional_salary_amount, leave_encashment.encashment_amount)

	@set_holiday_list("_Test Leave Encashment", "_Test Company")
	def test_non_encashable_leaves_setting(self):
		frappe.db.set_value(
			"Leave Type",
			self.leave_type,
			{
				"max_encashable_leaves": 0,
				"non_encashable_leaves": 5,
			},
		)

		first_sunday = get_first_sunday(self.holiday_list, for_date=self.leave_period.from_date)
		# 3 day leave application
		leave_application = make_leave_application(
			self.employee,
			add_days(first_sunday, 1),
			add_days(first_sunday, 3),
			"_Test Leave Type Encashment",
		)

		leave_encashment = frappe.get_doc(
			dict(
				doctype="Leave Encashment",
				employee=self.employee,
				leave_type="_Test Leave Type Encashment",
				leave_period=self.leave_period.name,
				encashment_date=self.leave_period.to_date,
				currency="INR",
			)
		).insert()

		self.assertEqual(leave_encashment.leave_balance, 7)
		# non-encashable leaves = 5, total leaves are 7, so encashable days = 7-5 = 2
		# with a charge of 50 per day
		self.assertTrue(leave_encashment.actual_encashable_days, 2)
		self.assertTrue(leave_encashment.encashment_days, 2)
		self.assertEqual(leave_encashment.encashment_amount, 100)

		# assert links
		leave_encashment.submit()
		additional_salary_amount = frappe.db.get_value(
			"Additional Salary", {"ref_docname": leave_encashment.name}, "amount"
		)
		self.assertEqual(additional_salary_amount, leave_encashment.encashment_amount)

	@set_holiday_list("_Test Leave Encashment", "_Test Company")
	def test_max_encashable_leaves_setting(self):
		frappe.db.set_value(
			"Leave Type",
			self.leave_type,
			{
				"max_encashable_leaves": 3,
				"non_encashable_leaves": 0,
			},
		)

		# 3 day leave application
		first_sunday = get_first_sunday(self.holiday_list, for_date=self.leave_period.from_date)
		leave_application = make_leave_application(
			self.employee,
			add_days(first_sunday, 1),
			add_days(first_sunday, 3),
			"_Test Leave Type Encashment",
		)

		leave_encashment = frappe.get_doc(
			dict(
				doctype="Leave Encashment",
				employee=self.employee,
				leave_type="_Test Leave Type Encashment",
				leave_period=self.leave_period.name,
				encashment_date=self.leave_period.to_date,
				currency="INR",
			)
		).insert()

		self.assertEqual(leave_encashment.leave_balance, 7)
		# leave balance = 7, but encashment limit = 3 so encashable days = 3
		self.assertTrue(leave_encashment.actual_encashable_days, 3)
		self.assertTrue(leave_encashment.encashment_days, 3)
		self.assertEqual(leave_encashment.encashment_amount, 150)

		# assert links
		leave_encashment.submit()
		additional_salary_amount = frappe.db.get_value(
			"Additional Salary", {"ref_docname": leave_encashment.name}, "amount"
		)
		self.assertEqual(additional_salary_amount, leave_encashment.encashment_amount)

	@set_holiday_list("_Test Leave Encashment", "_Test Company")
	def test_max_encashable_leaves_and_non_encashable_leaves_setting(self):
		frappe.db.set_value(
			"Leave Type",
			self.leave_type,
			{
				"max_encashable_leaves": 1,
				"non_encashable_leaves": 5,
			},
		)

		# 3 day leave application
		first_sunday = get_first_sunday(self.holiday_list, for_date=self.leave_period.from_date)
		leave_application = make_leave_application(
			self.employee,
			add_days(first_sunday, 1),
			add_days(first_sunday, 3),
			"_Test Leave Type Encashment",
		)

		leave_encashment = frappe.get_doc(
			dict(
				doctype="Leave Encashment",
				employee=self.employee,
				leave_type="_Test Leave Type Encashment",
				leave_period=self.leave_period.name,
				encashment_date=self.leave_period.to_date,
				currency="INR",
			)
		).insert()

		self.assertEqual(leave_encashment.leave_balance, 7)
		# 1. non-encashable leaves = 5, total leaves are 7, so encashable days = 7-5 = 2
		# 2. even though this leaves 2 encashable days, max encashable leaves = 1, so encashable days = 1
		self.assertTrue(leave_encashment.actual_encashable_days, 1)
		self.assertTrue(leave_encashment.encashment_days, 1)
		self.assertEqual(leave_encashment.encashment_amount, 50)

		# assert links
		leave_encashment.submit()
		additional_salary_amount = frappe.db.get_value(
			"Additional Salary", {"ref_docname": leave_encashment.name}, "amount"
		)
		self.assertEqual(additional_salary_amount, leave_encashment.encashment_amount)

	@set_holiday_list("_Test Leave Encashment", "_Test Company")
	def test_creation_of_leave_ledger_entry_on_submit(self):
		leave_encashment = frappe.get_doc(
			dict(
				doctype="Leave Encashment",
				employee=self.employee,
				leave_type="_Test Leave Type Encashment",
				leave_period=self.leave_period.name,
				encashment_date=self.leave_period.to_date,
				currency="INR",
			)
		).insert()

		leave_encashment.submit()

		leave_ledger_entry = frappe.get_all(
			"Leave Ledger Entry", fields="*", filters=dict(transaction_name=leave_encashment.name)
		)

		self.assertEqual(len(leave_ledger_entry), 1)
		self.assertEqual(leave_ledger_entry[0].employee, leave_encashment.employee)
		self.assertEqual(leave_ledger_entry[0].leave_type, leave_encashment.leave_type)
		self.assertEqual(leave_ledger_entry[0].leaves, leave_encashment.encashment_days * -1)

		# check if leave ledger entry is deleted on cancellation
		frappe.db.delete("Additional Salary", {"ref_docname": leave_encashment.name})
		leave_encashment.cancel()
		self.assertFalse(
			frappe.db.exists("Leave Ledger Entry", {"transaction_name": leave_encashment.name})
		)
