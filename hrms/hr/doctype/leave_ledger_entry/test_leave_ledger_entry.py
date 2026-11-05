# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.permissions import get_role_permissions
from frappe.utils.data import add_days, add_to_date, getdate, today

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.leave_allocation.test_leave_allocation import create_leave_allocation
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import (
	expire_allocation,
	process_expired_allocation,
)
from hrms.hr.doctype.leave_type.test_leave_type import create_leave_type
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_leave_application
from hrms.tests.utils import HRMSTestSuite


class TestLeaveLedgerEntry(HRMSTestSuite):
	def setUp(self):
		emp_id = make_employee("test_leave_allocation@salary.com", company="_Test Company")
		self.employee = frappe.get_doc("Employee", emp_id)

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

	def test_employee_cannot_create_ledger_entries(self):
		user = "test_ledger_entry_employee@example.com"
		make_employee(user, company="_Test Company")
		frappe.get_doc("User", user).add_roles("Employee")
		doctype = frappe.get_doc(
			frappe.get_file_json(
				frappe.get_app_path("hrms", "hr", "doctype", "leave_ledger_entry", "leave_ledger_entry.json")
			)
		)

		frappe.local.role_permissions = {}
		perms = get_role_permissions(doctype, user=user)
		frappe.local.role_permissions = {}
		for ptype in ("create", "write", "submit", "cancel", "delete"):
			self.assertFalse(perms.get(ptype), ptype)
			self.assertFalse(perms.if_owner.get(ptype), ptype)

	def test_cancelling_leave_application_keeps_manual_expiry(self):
		leave_type = create_leave_type(leave_type_name="_Test Manual Expiry Cancel").name
		allocation = create_leave_allocation(
			employee=self.employee.name,
			leave_type=leave_type,
			from_date=add_days(today(), -30),
			to_date=add_days(today(), 30),
			new_leaves_allocated=10,
		)
		allocation.submit()
		application = make_leave_application(
			self.employee.name, add_days(today(), -20), add_days(today(), -20), leave_type
		)
		expire_allocation(allocation, expiry_date=add_days(today(), -1))

		application.reload()
		application.cancel()

		self.assertTrue(
			frappe.db.exists("Leave Ledger Entry", {"transaction_name": allocation.name, "is_expired": 1})
		)

	def test_expiry_of_allocation_with_multiple_ledger_entries(self):
		leave_type = create_leave_type(leave_type_name="_Test Multi Row Expiry").name
		allocation = create_leave_allocation(
			employee=self.employee.name,
			leave_type=leave_type,
			from_date=add_days(today(), -60),
			to_date=add_days(today(), -31),
			new_leaves_allocated=10,
		)
		allocation.submit()
		allocation.new_leaves_allocated = 12
		allocation.save()

		next_allocation = create_leave_allocation(
			employee=self.employee.name,
			leave_type=leave_type,
			from_date=add_days(today(), -30),
			to_date=add_days(today(), -1),
			new_leaves_allocated=5,
		)
		next_allocation.submit()

		process_expired_allocation()

		def expired_leaves(name):
			return frappe.get_all(
				"Leave Ledger Entry", filters={"transaction_name": name, "is_expired": 1}, pluck="leaves"
			)

		self.assertEqual(expired_leaves(allocation.name), [-12])
		self.assertEqual(expired_leaves(next_allocation.name), [-5])
		self.assertEqual(frappe.db.get_value("Leave Allocation", allocation.name, "expired"), 1)
