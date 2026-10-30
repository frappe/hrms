# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.permissions import get_role_permissions

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.tests.utils import HRMSTestSuite


class TestLeaveLedgerPermissions(HRMSTestSuite):
	def test_employee_cannot_modify_leave_ledger(self):
		employee = make_employee("test_ledger_permissions@salary.com", company="_Test Company")
		user = frappe.db.get_value("Employee", employee, "user_id")
		doctype = frappe.get_doc(
			frappe.get_file_json(
				frappe.get_app_path("hrms", "hr", "doctype", "leave_ledger_entry", "leave_ledger_entry.json")
			)
		)
		frappe.local.role_permissions = {}
		try:
			permissions = get_role_permissions(doctype, user=user, is_owner=True)
			for action in ("create", "write", "submit", "cancel", "delete", "share"):
				with self.subTest(action=action):
					self.assertFalse(permissions.get(action))
					self.assertFalse(permissions.if_owner.get(action))
			self.assertTrue(permissions.if_owner.get("read"))
		finally:
			frappe.local.role_permissions = {}
