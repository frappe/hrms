# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import change_settings
from frappe.utils import add_days, add_to_date, get_first_day, get_last_day, getdate

from hrms.hr.doctype.leave_allocation.test_leave_allocation import (
	create_leave_allocation,
	process_expired_allocation,
)
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
from hrms.hr.doctype.leave_type.test_leave_type import create_leave_type
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_leave_application
from hrms.tests.utils import HRMSTestSuite


class TestLeaveAdjustment(HRMSTestSuite):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.make_employees()
		cls.make_leave_types()

	def setUp(self):
		for dt in ["Leave Adjustment", "Leave Allocation", "Leave Application", "Leave Ledger Entry"]:
			frappe.db.delete(dt)

		self.leave_allocation = create_leave_allocation(
			employee=self.employees[0].name,
			employee_name=self.employees[0].employee_name,
			leave_type=self.leave_types[0].name,
			new_leaves_allocated=10,
			from_date=get_first_day(getdate()),
			to_date=get_last_day(getdate()),
		)
		self.leave_allocation.submit()

	def test_duplicate_leave_adjustment(self):
		create_leave_adjustment(self.leave_allocation, adjustment_type="Reduce", leaves_to_adjust=3).submit()
		duplicate_adjustment = create_leave_adjustment(
			self.leave_allocation, adjustment_type="Allocate", leaves_to_adjust=10
		)
		self.assertRaises(frappe.ValidationError, duplicate_adjustment.save)

	def test_adjustment_for_over_allocation(self):
		leave_type = create_leave_type(leave_type_name="Test Over Allocation", max_leaves_allowed=30)
		leave_allocation = create_leave_allocation(
			employee=self.employees[0].name,
			employee_name=self.employees[0].employee_name,
			leave_type=leave_type.name,
			new_leaves_allocated=25,
		)
		leave_allocation.submit()
		leave_adjustment = create_leave_adjustment(
			leave_allocation, adjustment_type="Allocate", leaves_to_adjust=10
		)

		self.assertRaises(frappe.ValidationError, leave_adjustment.save)

	def test_adjustment_for_negative_leave_balance(self):
		make_leave_application(
			employee=self.employees[0].name,
			from_date=get_first_day(getdate()),
			to_date=add_days(get_first_day(getdate()), 6),
			leave_type=self.leave_types[0].name,
		)

		leave_adjustment = create_leave_adjustment(
			self.leave_allocation,
			adjustment_type="Reduce",
			leaves_to_adjust=5,
			posting_date=add_days(get_first_day(getdate()), 20),
		)

		self.assertRaises(frappe.ValidationError, leave_adjustment.save)

	def test_increase_balance_with_adjustment(self):
		create_leave_adjustment(
			self.leave_allocation, adjustment_type="Allocate", leaves_to_adjust=6
		).submit()

		leave_balance = get_leave_balance_on(
			employee=self.employees[0].name, leave_type=self.leave_types[0].name, date=getdate()
		)

		self.assertEqual(leave_balance, 16)

	def test_decrease_balance_with_adjustment(self):
		create_leave_adjustment(self.leave_allocation, adjustment_type="Reduce", leaves_to_adjust=3).submit()
		leave_balance = get_leave_balance_on(
			employee=self.employees[0].name, leave_type=self.leave_types[0].name, date=getdate()
		)
		self.assertEqual(leave_balance, 7)

	def test_decrease_balance_after_leave_is_applied(self):
		# allocation of 10 leaves, leave application for 3 days
		mid_month = add_days(get_first_day(getdate()), 15)
		make_leave_application(
			employee=self.employees[0].name,
			from_date=mid_month,
			to_date=add_days(mid_month, 2),
			leave_type=self.leave_types[0].name,
		)
		# adjustment of 6 days made after applications
		create_leave_adjustment(
			self.leave_allocation,
			adjustment_type="Allocate",
			leaves_to_adjust=6,
			posting_date=get_last_day(getdate()),
		).submit()
		# so total balance should be 10 - 3 + 6 = 13
		leave_balance = get_leave_balance_on(
			employee=self.employees[0].name, leave_type=self.leave_types[0].name, date=get_last_day(getdate())
		)
		self.assertEqual(leave_balance, 13)

	@change_settings("System Settings", {"float_precision": 2})
	def test_precision(self):
		leave_adjustment = create_leave_adjustment(
			self.leave_allocation, adjustment_type="Allocate", leaves_to_adjust=5.126
		)
		leave_adjustment.submit()
		leave_adjustment.reload()
		self.assertEqual(leave_adjustment.leaves_to_adjust, 5.13)

	def test_back_dated_leave_adjustment(self):
		for dt in ["Leave Allocation", "Leave Ledger Entry"]:
			frappe.db.delete(dt)

		# backdated leave allocation
		leave_allocation = create_leave_allocation(
			employee=self.employees[0].name,
			employee_name=self.employees[0].employee_name,
			leave_type=self.leave_types[0].name,
			from_date=add_to_date(getdate(), months=-13),
			to_date=add_to_date(getdate(), months=-1),
			new_leaves_allocated=10,
		)
		leave_allocation.submit()
		# backdated leave adjustment
		create_leave_adjustment(
			leave_allocation,
			adjustment_type="Reduce",
			leaves_to_adjust=5,
			posting_date=add_to_date(getdate(), months=-10),
		).submit()
		# leave balance in previous period
		leave_balance = get_leave_balance_on(
			employee=self.employees[0].name,
			leave_type=self.leave_types[0].name,
			date=add_to_date(getdate(), months=-1),
		)
		self.assertEqual(leave_balance, 5.0)
		# leave balance now, should be 0 because everything has expired
		leave_balance = get_leave_balance_on(
			employee=self.employees[0].name, leave_type=self.leave_types[0].name, date=getdate()
		)
		self.assertEqual(leave_balance, 0.0)

	def test_reduction_type_adjustment_while_carry_forwarding_leaves(self):
		for dt in ["Leave Allocation", "Leave Ledger Entry"]:
			frappe.db.delete(dt)

		leave_type = create_leave_type(leave_type_name="CF Adjustment", is_carry_forward=1)
		leave_allocation = create_leave_allocation(
			employee=self.employees[0].name,
			employee_name=self.employees[0].employee_name,
			leave_type=leave_type.name,
			from_date=add_to_date(getdate(), months=-13),
			to_date=add_to_date(getdate(), months=-1),
			new_leaves_allocated=10,
		)
		leave_allocation.submit()
		create_leave_adjustment(
			leave_allocation,
			adjustment_type="Reduce",
			leaves_to_adjust=5,
			posting_date=add_to_date(getdate(), months=-10),
		).submit()

		create_leave_allocation(
			employee=self.employees[0].name,
			employee_name=self.employees[0].employee_name,
			leave_type=leave_type.name,
			from_date=add_to_date(getdate(), days=-15),
			to_date=getdate(),
			new_leaves_allocated=10,
			carry_forward=1,
		).submit()
		leave_balance = get_leave_balance_on(
			employee=self.employees[0].name, leave_type=leave_type.name, date=getdate()
		)

		# 5 carried forward + 10 new
		self.assertEqual(leave_balance, 15.0)

	def test_allocate_type_adjustment_while_carry_forwarding_leaves(self):
		for dt in ["Leave Allocation", "Leave Ledger Entry"]:
			frappe.db.delete(dt)

		leave_type = create_leave_type(leave_type_name="CF Adjustment", is_carry_forward=1)
		leave_allocation = create_leave_allocation(
			employee=self.employees[0].name,
			employee_name=self.employees[0].employee_name,
			leave_type=leave_type.name,
			from_date=add_to_date(getdate(), months=-13),
			to_date=add_to_date(getdate(), months=-1),
			new_leaves_allocated=10,
		)
		leave_allocation.submit()
		create_leave_adjustment(
			leave_allocation,
			adjustment_type="Allocate",
			leaves_to_adjust=5,
			posting_date=add_to_date(getdate(), months=-10),
		).submit()

		create_leave_allocation(
			employee=self.employees[0].name,
			employee_name=self.employees[0].employee_name,
			leave_type=leave_type.name,
			from_date=add_to_date(getdate(), days=-25),
			to_date=getdate(),
			new_leaves_allocated=5,
			carry_forward=1,
		).submit()
		leave_balance = get_leave_balance_on(
			employee=self.employees[0].name, leave_type=leave_type.name, date=getdate()
		)

		# 15 carried forward + 5 new
		self.assertEqual(leave_balance, 20.0)


def create_leave_adjustment(leave_allocation, adjustment_type, leaves_to_adjust=None, posting_date=None):
	leave_adjustment = frappe.new_doc(
		"Leave Adjustment",
		employee=leave_allocation.employee,
		leave_allocation=leave_allocation.name,
		leave_type=leave_allocation.leave_type,
		posting_date=posting_date or getdate(),
		adjustment_type=adjustment_type,
		leaves_to_adjust=leaves_to_adjust or 10,
	)
	return leave_adjustment
