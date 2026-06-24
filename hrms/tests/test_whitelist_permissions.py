# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
"""
Real-user permission scenarios for the whitelisted endpoints
Each test switches `frappe.session.user` to a concrete
user (owner / leave approver / unrelated employee / roleless user) and asserts:

  * an unauthorized user is blocked with `frappe.PermissionError`, and
  * a legitimately authorized user (the owner, the approver, or an admin) is NOT
    blocked by the added check (self-service is preserved).

Coverage maps to the audit findings:
  - leave_ledger_entry.expire_allocation ............ High (write bypass)
  - employee_payment_entry.set_exchange_rate_in_advance High (write bypass)
  - leave_application.get_leave_approver / get_holidays / get_number_of_leave_days
                                                       self-service read gate
  - attendance.get_unmarked_days .................... Employee-data read leak
  - api.get_company_cost_center_and_expense_account .. company-config read leak
  - team_updates.get_data ........................... restored only_for role gate
"""

import json

import frappe
from frappe.permissions import add_user_permission
from frappe.utils import add_days, getdate
from frappe.utils.user import add_role

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.api import get_company_cost_center_and_expense_account
from hrms.hr.doctype.attendance.attendance import get_unmarked_days
from hrms.hr.doctype.leave_allocation.test_leave_allocation import create_leave_allocation
from hrms.hr.doctype.leave_application.leave_application import (
	get_holidays,
	get_leave_approver,
	get_number_of_leave_days,
)
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import expire_allocation
from hrms.hr.page.team_updates.team_updates import get_data as get_team_updates
from hrms.overrides.employee_payment_entry import set_exchange_rate_in_advance
from hrms.tests.utils import HRMSTestSuite


class TestWhitelistPermissions(HRMSTestSuite):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.company = "_Test Company"
		cls.leave_type = "_Test Leave Type"

		def ensure_employee(user):
			# make_employee returns None if the user/employee already exists (re-runs)
			return make_employee(user, cls.company) or frappe.db.get_value("Employee", {"user_id": user})

		# owner: an employee acting on their own records
		cls.owner_user = "wl_owner@example.com"
		cls.owner_emp = ensure_employee(cls.owner_user)

		# the owner's leave approver
		cls.approver_user = "wl_approver@example.com"
		cls.approver_emp = ensure_employee(cls.approver_user)
		add_role(cls.approver_user, "Leave Approver")
		frappe.db.set_value("Employee", cls.owner_emp, "leave_approver", cls.approver_user)

		# outsider: an unrelated employee with no access to the owner's records
		cls.outsider_user = "wl_outsider@example.com"
		cls.outsider_emp = ensure_employee(cls.outsider_user)

		# each employee gets read on their OWN Employee record (standard self-service)
		for user, emp in (
			(cls.owner_user, cls.owner_emp),
			(cls.approver_user, cls.approver_emp),
			(cls.outsider_user, cls.outsider_emp),
		):
			if not frappe.db.exists("User Permission", {"user": user, "allow": "Employee", "for_value": emp}):
				add_user_permission("Employee", emp, user)

		# a user with no roles at all — used to exercise role/permission gates deterministically
		cls.roleless_user = "wl_roleless@example.com"
		if not frappe.db.exists("User", cls.roleless_user):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": cls.roleless_user,
					"first_name": "Roleless",
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)

		# a submitted leave allocation owned by the owner (target for expire_allocation)
		allocation = create_leave_allocation(
			employee=cls.owner_emp,
			leave_type=cls.leave_type,
			from_date=getdate(),
			to_date=add_days(getdate(), 364),
			new_leaves_allocated=15,
		)
		allocation.insert()
		allocation.submit()
		cls.allocation = allocation

	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")

	def assert_not_blocked(self, fn, *args, **kwargs):
		"""The added permission check must NOT raise for an authorized user.

		Unrelated downstream errors are ignored — we only assert the gate lets the
		caller through.
		"""
		try:
			fn(*args, **kwargs)
		except frappe.PermissionError as e:
			self.fail(f"{getattr(fn, '__name__', fn)} blocked an authorized user: {e}")
		except Exception:
			pass

	# ------------------------------------------------------------------ High: writes

	def test_expire_allocation_blocks_unauthorized_user(self):
		payload = self.allocation.as_dict()

		# an unrelated employee must not be able to expire someone else's allocation
		frappe.set_user(self.outsider_user)
		self.assertRaises(frappe.PermissionError, expire_allocation, payload)

		# an admin (HR-equivalent) may
		frappe.set_user("Administrator")
		self.assert_not_blocked(expire_allocation, payload)

	def test_set_exchange_rate_in_advance_blocks_unauthorized_user(self):
		# crafts the Payment-Entry-shaped doc the endpoint accepts; the reference name
		# need not exist — the write-permission check fires before any DB write.
		doc = frappe._dict(
			references=[
				frappe._dict(reference_doctype="Employee Advance", reference_name="FAKE-ADVANCE-001")
			],
			target_exchange_rate=80.0,
		)

		frappe.set_user(self.outsider_user)
		self.assertRaises(frappe.PermissionError, set_exchange_rate_in_advance, doc)

	# --------------------------------------------------- self-service leave endpoints

	def test_leave_endpoints_allow_owner_and_approver(self):
		from_date = getdate()
		to_date = add_days(getdate(), 2)

		# the employee themselves
		frappe.set_user(self.owner_user)
		self.assert_not_blocked(get_leave_approver, self.owner_emp)
		self.assert_not_blocked(get_holidays, self.owner_emp, from_date, to_date)
		self.assert_not_blocked(get_number_of_leave_days, self.owner_emp, self.leave_type, from_date, to_date)

		# their leave approver
		frappe.set_user(self.approver_user)
		self.assert_not_blocked(get_leave_approver, self.owner_emp)

	def test_leave_endpoints_block_unrelated_employee(self):
		from_date = getdate()
		to_date = add_days(getdate(), 2)

		frappe.set_user(self.outsider_user)
		self.assertRaises(frappe.PermissionError, get_leave_approver, self.owner_emp)
		self.assertRaises(frappe.PermissionError, get_holidays, self.owner_emp, from_date, to_date)
		self.assertRaises(
			frappe.PermissionError,
			get_number_of_leave_days,
			self.owner_emp,
			self.leave_type,
			from_date,
			to_date,
		)

	# -------------------------------------------------------------- read-leak: employee

	def test_get_unmarked_days_respects_employee_read_permission(self):
		from_date = getdate()
		to_date = add_days(getdate(), 5)

		# owner reading their own attendance gaps is allowed
		frappe.set_user(self.owner_user)
		self.assert_not_blocked(get_unmarked_days, self.owner_emp, from_date, to_date)

		# an unrelated employee cannot read the owner's attendance data
		frappe.set_user(self.outsider_user)
		self.assertRaises(frappe.PermissionError, get_unmarked_days, self.owner_emp, from_date, to_date)

	# ----------------------------------------------------------- read-leak: company config

	def test_company_cost_center_requires_company_read(self):
		# a user with no Company read permission is blocked
		frappe.set_user(self.roleless_user)
		self.assertRaises(frappe.PermissionError, get_company_cost_center_and_expense_account, self.company)

		# an admin is not
		frappe.set_user("Administrator")
		self.assert_not_blocked(get_company_cost_center_and_expense_account, self.company)

	# ------------------------------------------------------------- restored only_for gate

	def test_team_updates_enforces_role_gate(self):
		# user without the Employee / System Manager role is blocked
		frappe.set_user(self.roleless_user)
		self.assertRaises(frappe.PermissionError, get_team_updates)

		# a regular employee passes the gate
		frappe.set_user(self.owner_user)
		self.assert_not_blocked(get_team_updates)
