# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, get_year_ending, get_year_start, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee
from erpnext.setup.doctype.holiday_list.test_holiday_list import set_holiday_list

from hrms.hr.doctype.leave_allocation.leave_allocation import get_unused_leaves
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import process_expired_allocation
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


class TestLeaveEncashment(IntegrationTestCase):
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

		create_assignment_for_multiple_employees([self.employee], frappe._dict(data))

		make_salary_structure(
			"Salary Structure for Encashment",
			"Monthly",
			self.employee,
			other_details={"leave_encashment_amount_per_day": 50},
		)

	@set_holiday_list("_Test Leave Encashment", "_Test Company")
	def test_leave_balance_value_and_amount(self):
		leave_encashment = self.create_test_leave_encashment()

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
		make_leave_application(
			self.employee,
			add_days(first_sunday, 1),
			add_days(first_sunday, 3),
			"_Test Leave Type Encashment",
		)

		leave_encashment = self.create_test_leave_encashment()

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
		make_leave_application(
			self.employee,
			add_days(first_sunday, 1),
			add_days(first_sunday, 3),
			"_Test Leave Type Encashment",
		)

		leave_encashment = self.create_test_leave_encashment()

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
		make_leave_application(
			self.employee,
			add_days(first_sunday, 1),
			add_days(first_sunday, 3),
			"_Test Leave Type Encashment",
		)

		leave_encashment = self.create_test_leave_encashment()

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
		leave_encashment = self.create_test_leave_encashment()
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
		self.assertFalse(frappe.db.exists("Leave Ledger Entry", {"transaction_name": leave_encashment.name}))

	@set_holiday_list("_Test Leave Encashment", "_Test Company")
	def test_unused_leaves_after_leave_encashment_for_carry_forwarding_leave_type(self):
		employee = make_employee("test_employee2_encashment@example.com", company="_Test Company")
		# allocated 10 leaves, encashed 5
		leave_encashment = self.get_encashment_created_after_leave_period(
			employee, is_carry_forward=1, encashment_days=5
		)
		# check if unused leaves are 5 before processing expired allocation runs
		unused_leaves = get_unused_leaves(
			employee, self.leave_type, self.leave_period.from_date, self.leave_period.to_date
		)
		self.assertEqual(unused_leaves, 5)

		# check if a single leave ledger entry is created
		self.assertEqual(frappe.get_value("Leave Type", self.leave_type, "is_carry_forward"), 1)
		leave_ledger_entry = frappe.get_all(
			"Leave Ledger Entry", fields=["leaves"], filters={"transaction_name": leave_encashment.name}
		)
		self.assertEqual(len(leave_ledger_entry), 1)
		self.assertEqual(leave_ledger_entry[0].leaves, leave_encashment.encashment_days * -1)

		# check if unused leaves are 5 after processing expired allocation runs
		process_expired_allocation()
		unused_leaves = get_unused_leaves(
			employee, self.leave_type, self.leave_period.from_date, self.leave_period.to_date
		)
		self.assertEqual(unused_leaves, 5)

	@set_holiday_list("_Test Leave Encashment", "_Test Company")
	def test_leave_expiry_after_leave_encashment_for_non_carry_forwarding_leave_type(self):
		employee = make_employee("test_employee3_encashment@example.com", company="_Test Company")
		# allocated 10 leaves, encashed 3

		leave_encashment = self.get_encashment_created_after_leave_period(
			employee, is_carry_forward=0, encashment_days=3
		)
		# when leave encashment is created after leave allocation period is over,
		# it's assumed that process expired allocation has expired the leaves,
		# hence a reverse ledger entry should be created for the encashment
		# check if two leave ledger entries are created
		self.assertEqual(frappe.get_value("Leave Type", self.leave_type, "is_carry_forward"), 0)
		leave_ledger_entry = frappe.get_all(
			"Leave Ledger Entry",
			fields="*",
			filters={"transaction_name": leave_encashment.name},
			order_by="leaves",
		)
		self.assertEqual(len(leave_ledger_entry), 2)
		self.assertEqual(leave_ledger_entry[0].leaves, leave_encashment.encashment_days * -1)
		self.assertEqual(leave_ledger_entry[1].leaves, leave_encashment.encashment_days * 1)

		# check if 10 leaves are expired after processing expired allocation runs
		process_expired_allocation()

		expired_leaves = frappe.get_value(
			"Leave Ledger Entry",
			{"employee": employee, "leave_type": self.leave_type, "is_expired": 1},
			"leaves",
		)
		self.assertEqual(expired_leaves, -10)

	def get_encashment_created_after_leave_period(self, employee, is_carry_forward, encashment_days):
		frappe.db.delete("Leave Period", {"name": self.leave_period.name})
		# create new leave period that has end date of yesterday
		start_date = add_days(getdate(), -30)
		end_date = add_days(getdate(), -1)
		self.leave_period = create_leave_period(start_date, end_date, "_Test Company")
		frappe.db.set_value(
			"Leave Type",
			self.leave_type,
			{
				"is_carry_forward": is_carry_forward,
			},
		)

		leave_policy = frappe.get_value("Leave Policy", {"title": "Test Leave Policy"}, "name")
		data = {
			"assignment_based_on": "Leave Period",
			"leave_policy": leave_policy,
			"leave_period": self.leave_period.name,
		}
		create_assignment_for_multiple_employees([employee], frappe._dict(data))

		make_salary_structure(
			"Salary Structure for Encashment",
			"Monthly",
			employee,
			from_date=start_date,
			other_details={"leave_encashment_amount_per_day": 50},
		)

		leave_encashment = self.create_test_leave_encashment(
			employee=employee, encashment_days=encashment_days, leave_type=self.leave_type
		)
		leave_encashment.submit()
		return leave_encashment

	@set_holiday_list("_Test Leave Encashment", "_Test Company")
	def test_status_of_leave_encashment_after_payment_via_salary_slip(self):
		from hrms.payroll.doctype.salary_slip.test_salary_slip import make_employee_salary_slip
		from hrms.payroll.doctype.salary_structure.test_salary_structure import (
			create_salary_structure_assignment,
		)

		salary_structure = make_salary_structure(
			"Salary Structure for Encashment",
			"Monthly",
			self.employee,
			other_details={"leave_encashment_amount_per_day": 50},
		)

		create_salary_structure_assignment(
			employee=self.employee,
			salary_structure=salary_structure.name,
			company="_Test Company",
			currency="INR",
		)

		leave_encashment = self.create_test_leave_encashment(encashment_date=getdate())
		leave_encashment.submit()

		ss = make_employee_salary_slip(self.employee, "Monthly", salary_structure=salary_structure.name)

		ss.submit()
		leave_encashment.reload()
		self.assertEqual(leave_encashment.status, "Paid")

		ss.cancel()
		leave_encashment.reload()
		self.assertEqual(leave_encashment.status, "Unpaid")

	def test_status_of_leave_encashment_after_payment_via_payment_entry_and_fnf(self):
		from hrms.hr.doctype.full_and_final_statement.test_full_and_final_statement import (
			create_full_and_final_statement,
		)
		from hrms.overrides.employee_payment_entry import get_payment_entry_for_employee

		leave_encashment = self.create_test_leave_encashment(
			pay_via_payment_entry=1, payable_account="Payroll Payable - _TC"
		)
		leave_encashment.submit()

		pe = get_payment_entry_for_employee(leave_encashment.doctype, leave_encashment.name)
		pe.reference_no = "1"
		pe.reference_date = getdate()
		pe.save()
		pe.submit()

		leave_encashment.reload()
		self.assertEqual(leave_encashment.status, "Paid")

		pe.cancel()
		leave_encashment.reload()
		self.assertEqual(leave_encashment.status, "Unpaid")

		frappe.db.set_value("Employee", self.employee, "relieving_date", getdate())

		fnf = create_full_and_final_statement(self.employee)
		fnf.payables = []
		fnf.receivables = []
		fnf.append(
			"payables",
			{
				"component": "Leave Encashment",
				"reference_document_type": "Leave Encashment",
				"reference_document": leave_encashment.name,
				"amount": leave_encashment.encashment_amount,
				"account": leave_encashment.payable_account,
				"status": "Settled",
			},
		)
		fnf.submit()

		jv = fnf.create_journal_entry()
		jv.accounts[1].account = frappe.get_cached_value("Company", "_Test Company", "default_bank_account")
		jv.cheque_no = "123456"
		jv.cheque_date = getdate()
		jv.save()
		jv.submit()

		leave_encashment.reload()
		self.assertEqual(leave_encashment.status, "Paid")

		jv.cancel()
		leave_encashment.reload()
		self.assertEqual(leave_encashment.status, "Unpaid")

	def create_test_leave_encashment(self, **kwargs):
		"""Helper method to create leave encashment with default values"""
		args = {
			"employee": self.employee,
			"leave_type": "_Test Leave Type Encashment",
			"leave_period": self.leave_period.name,
			"encashment_date": self.leave_period.to_date,
			"currency": "INR",
		}
		args.update(kwargs)
		return create_leave_encashment(**args)


def create_leave_encashment(**args):
	if args:
		args = frappe._dict(args)
	leave_encashment = frappe.new_doc("Leave Encashment")
	leave_encashment.company = args.company or "_Test Company"
	leave_encashment.employee = args.employee
	leave_encashment.posting_date = args.posting_date or getdate()
	leave_encashment.leave_type = args.leave_type
	leave_encashment.leave_period = args.leave_period
	leave_encashment.encashment_date = args.encashment_date or getdate()
	leave_encashment.currency = args.currency or frappe.get_cached_value(
		"Company", "_Test Company", "default_currency"
	)
	leave_encashment.pay_via_payment_entry = args.pay_via_payment_entry or 0
	if leave_encashment.pay_via_payment_entry:
		leave_encashment.payable_account = args.payable_account or frappe.get_cached_value(
			"Company", "_Test Company", "default_payable_account"
		)
		leave_encashment.expense_account = args.expense_account or "Administrative Expenses - _TC"
		leave_encashment.cost_center = args.cost_center or "Main - _TC"

	if args.encashment_days:
		leave_encashment.encashment_days = args.encashment_days

	leave_encashment.insert()

	return leave_encashment
