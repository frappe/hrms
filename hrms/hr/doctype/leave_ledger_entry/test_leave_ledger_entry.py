# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils.data import add_days, add_to_date, today

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.leave_allocation.test_leave_allocation import create_leave_allocation
from hrms.hr.doctype.leave_application.test_leave_application import make_leave_application
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import expire_allocation
from hrms.hr.doctype.leave_type.test_leave_type import create_leave_type
from hrms.tests.utils import HRMSTestSuite


class TestLeaveLedgerEntry(HRMSTestSuite):
	def setUp(self):
		emp_id = make_employee("test_leave_allocation@salary.com", company="_Test Company")
		self.employee = frappe.get_doc("Employee", emp_id)

	def test_leave_cancellation_preserves_manual_expiry(self):
		leave_type = create_leave_type(leave_type_name="_Test Cancellation Expiry").name
		allocation = create_leave_allocation(
			employee=self.employee.name,
			leave_type=leave_type,
			from_date=add_days(today(), -30),
			to_date=add_days(today(), 30),
			new_leaves_allocated=10,
		).submit()
		application = make_leave_application(
			self.employee.name, add_days(today(), -10), add_days(today(), -10), leave_type
		)
		expire_allocation(allocation, expiry_date=add_days(today(), -1))
		expiry = frappe.db.get_value(
			"Leave Ledger Entry", {"transaction_name": allocation.name, "is_expired": 1}
		)
		self.assertTrue(expiry)

		application.reload().cancel()

		self.assertTrue(frappe.db.exists("Leave Ledger Entry", expiry))
		self.assertFalse(frappe.db.exists("Leave Ledger Entry", {"transaction_name": application.name}))

	def test_allocation_cancellation_only_reverts_carry_forward_expiry(self):
		for carry_forward in (0, 1):
			with self.subTest(carry_forward=carry_forward):
				leave_type = create_leave_type(
					leave_type_name=f"_Test Cancellation Carry Forward {carry_forward}", is_carry_forward=1
				).name
				previous = create_leave_allocation(
					employee=self.employee.name,
					leave_type=leave_type,
					from_date=add_days(today(), -60),
					to_date=add_days(today(), -31),
					new_leaves_allocated=10,
				).submit()
				if not carry_forward:
					expire_allocation(previous)
				allocation = create_leave_allocation(
					employee=self.employee.name,
					leave_type=leave_type,
					from_date=add_days(today(), -30),
					to_date=add_days(today(), 30),
					new_leaves_allocated=10,
					carry_forward=carry_forward,
				).submit()
				expiry = frappe.db.get_value(
					"Leave Ledger Entry", {"transaction_name": previous.name, "is_expired": 1}
				)
				self.assertTrue(expiry)

				allocation.cancel()

				self.assertEqual(bool(frappe.db.exists("Leave Ledger Entry", expiry)), not carry_forward)

	def test_expire_allocation(self):
		import json

		allocation = {
			"doctype": "Leave Allocation",
			"__islocal": 1,
			"employee": self.employee.name,
			"employee_name": self.employee.employee_name,
			"leave_type": "_Test Leave Type",
			"from_date": today(),
			"to_date": add_to_date(today(), days=30),
			"new_leaves_allocated": 5,
			"docstatus": 1,
		}

		allocation = frappe.get_doc(allocation).save()

		expire_allocation(json.dumps(allocation.as_dict()))
		allocation.reload()

		self.assertEqual(allocation.expired, 1)
