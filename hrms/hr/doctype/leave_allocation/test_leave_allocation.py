import frappe
from frappe.tests import IntegrationTestCase, change_settings
from frappe.utils import add_days, add_months, getdate, nowdate

import erpnext
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.leave_allocation.leave_allocation import (
	BackDatedAllocationError,
	OverAllocationError,
)
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import process_expired_allocation
from hrms.hr.doctype.leave_type.test_leave_type import create_leave_type


class TestLeaveAllocation(IntegrationTestCase):
	def setUp(self):
		frappe.db.delete("Leave Period")
		frappe.db.delete("Leave Allocation")
		frappe.db.delete("Leave Application")
		frappe.db.delete("Leave Ledger Entry")

		emp_id = make_employee("test_leave_allocation@salary.com", company="_Test Company")
		self.employee = frappe.get_doc("Employee", emp_id)

	def test_overlapping_allocation(self):
		leaves = [
			{
				"doctype": "Leave Allocation",
				"__islocal": 1,
				"employee": self.employee.name,
				"employee_name": self.employee.employee_name,
				"leave_type": "_Test Leave Type",
				"from_date": getdate("2015-10-01"),
				"to_date": getdate("2015-10-31"),
				"new_leaves_allocated": 5,
				"docstatus": 1,
			},
			{
				"doctype": "Leave Allocation",
				"__islocal": 1,
				"employee": self.employee.name,
				"employee_name": self.employee.employee_name,
				"leave_type": "_Test Leave Type",
				"from_date": getdate("2015-09-01"),
				"to_date": getdate("2015-11-30"),
				"new_leaves_allocated": 5,
			},
		]

		frappe.get_doc(leaves[0]).save()
		self.assertRaises(frappe.ValidationError, frappe.get_doc(leaves[1]).save)

	def test_invalid_period(self):
		doc = frappe.get_doc(
			{
				"doctype": "Leave Allocation",
				"__islocal": 1,
				"employee": self.employee.name,
				"employee_name": self.employee.employee_name,
				"leave_type": "_Test Leave Type",
				"from_date": getdate("2015-09-30"),
				"to_date": getdate("2015-09-1"),
				"new_leaves_allocated": 5,
			}
		)

		# invalid period
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_validation_for_over_allocation(self):
		leave_type = create_leave_type(leave_type_name="Test Over Allocation", is_carry_forward=1)

		doc = frappe.get_doc(
			{
				"doctype": "Leave Allocation",
				"__islocal": 1,
				"employee": self.employee.name,
				"employee_name": self.employee.employee_name,
				"leave_type": leave_type.name,
				"from_date": getdate("2015-09-1"),
				"to_date": getdate("2015-09-30"),
				"new_leaves_allocated": 35,
				"carry_forward": 1,
			}
		)

		# allocated leave more than period
		self.assertRaises(OverAllocationError, doc.save)

		leave_type.allow_over_allocation = 1
		leave_type.save()

		# allows creating a leave allocation with more leave days than period days
		doc = frappe.get_doc(
			{
				"doctype": "Leave Allocation",
				"__islocal": 1,
				"employee": self.employee.name,
				"employee_name": self.employee.employee_name,
				"leave_type": leave_type.name,
				"from_date": getdate("2015-09-1"),
				"to_date": getdate("2015-09-30"),
				"new_leaves_allocated": 35,
				"carry_forward": 1,
			}
		).insert()

	def test_validation_for_over_allocation_post_submission(self):
		allocation = frappe.get_doc(
			{
				"doctype": "Leave Allocation",
				"__islocal": 1,
				"employee": self.employee.name,
				"employee_name": self.employee.employee_name,
				"leave_type": "_Test Leave Type",
				"from_date": getdate("2015-09-1"),
				"to_date": getdate("2015-09-30"),
				"new_leaves_allocated": 15,
			}
		).submit()
		allocation.reload()
		# allocated leaves more than period after submission
		allocation.new_leaves_allocated = 35
		self.assertRaises(OverAllocationError, allocation.save)

	def test_validation_for_over_allocation_based_on_leave_setup(self):
		frappe.delete_doc_if_exists("Leave Period", "Test Allocation Period")
		leave_period = frappe.get_doc(
			dict(
				name="Test Allocation Period",
				doctype="Leave Period",
				from_date=add_months(nowdate(), -6),
				to_date=add_months(nowdate(), 6),
				company="_Test Company",
				is_active=1,
			)
		).insert()

		leave_type = create_leave_type(
			leave_type_name="_Test Allocation Validation", is_carry_forward=1, max_leaves_allowed=25
		)

		# 15 leaves allocated in this period
		allocation = create_leave_allocation(
			leave_type=leave_type.name,
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			from_date=leave_period.from_date,
			to_date=nowdate(),
		)
		allocation.submit()

		# trying to allocate additional 15 leaves
		allocation = create_leave_allocation(
			leave_type=leave_type.name,
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			from_date=add_days(nowdate(), 1),
			to_date=leave_period.to_date,
		)
		self.assertRaises(OverAllocationError, allocation.save)

	def test_validation_for_over_allocation_based_on_leave_setup_post_submission(self):
		frappe.delete_doc_if_exists("Leave Period", "Test Allocation Period")
		leave_period = frappe.get_doc(
			dict(
				name="Test Allocation Period",
				doctype="Leave Period",
				from_date=add_months(nowdate(), -6),
				to_date=add_months(nowdate(), 6),
				company="_Test Company",
				is_active=1,
			)
		).insert()

		leave_type = create_leave_type(
			leave_type_name="_Test Allocation Validation", is_carry_forward=1, max_leaves_allowed=30
		)

		# 15 leaves allocated
		allocation = create_leave_allocation(
			leave_type=leave_type.name,
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			from_date=leave_period.from_date,
			to_date=nowdate(),
		)
		allocation.submit()
		allocation.reload()

		# allocate additional 15 leaves
		allocation = create_leave_allocation(
			leave_type=leave_type.name,
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			from_date=add_days(nowdate(), 1),
			to_date=leave_period.to_date,
		)
		allocation.submit()
		allocation.reload()

		# trying to allocate 25 leaves in 2nd alloc within leave period
		# total leaves = 40 which is more than `max_leaves_allowed` setting i.e. 30
		allocation.new_leaves_allocated = 25
		self.assertRaises(OverAllocationError, allocation.save)

	def test_validate_back_dated_allocation_update(self):
		create_leave_type(leave_type_name="_Test_CF_leave", is_carry_forward=1)

		# initial leave allocation = 15
		leave_allocation = create_leave_allocation(
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			leave_type="_Test_CF_leave",
			from_date=add_months(nowdate(), -12),
			to_date=add_months(nowdate(), -1),
			carry_forward=0,
		)
		leave_allocation.submit()

		# new_leaves = 15, carry_forwarded = 10
		leave_allocation_1 = create_leave_allocation(
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			leave_type="_Test_CF_leave",
			carry_forward=1,
		)
		leave_allocation_1.submit()

		# try updating initial leave allocation
		leave_allocation.reload()
		leave_allocation.new_leaves_allocated = 20
		self.assertRaises(BackDatedAllocationError, leave_allocation.save)

	def test_carry_forward_calculation(self):
		create_leave_type(
			leave_type_name="_Test_CF_leave",
			is_carry_forward=1,
			maximum_carry_forwarded_leaves=10,
			max_leaves_allowed=30,
		)

		# initial leave allocation = 15
		leave_allocation = create_leave_allocation(
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			leave_type="_Test_CF_leave",
			from_date=add_months(nowdate(), -12),
			to_date=add_months(nowdate(), -1),
			carry_forward=0,
		)
		leave_allocation.submit()

		# carry forwarded leaves considering maximum_carry_forwarded_leaves
		# new_leaves = 15, carry_forwarded = 10
		leave_allocation_1 = create_leave_allocation(
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			leave_type="_Test_CF_leave",
			carry_forward=1,
		)
		leave_allocation_1.submit()
		leave_allocation_1.reload()

		self.assertEqual(leave_allocation_1.unused_leaves, 10)
		self.assertEqual(leave_allocation_1.total_leaves_allocated, 25)

		leave_allocation_1.cancel()

		# carry forwarded leaves considering max_leave_allowed
		# max_leave_allowed = 30, new_leaves = 25, carry_forwarded = 5
		leave_allocation_2 = create_leave_allocation(
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			leave_type="_Test_CF_leave",
			carry_forward=1,
			new_leaves_allocated=25,
		)
		leave_allocation_2.submit()

		self.assertEqual(leave_allocation_2.unused_leaves, 5)

	@change_settings("System Settings", {"float_precision": 2})
	def test_precision(self):
		create_leave_type(
			leave_type_name="_Test_CF_leave",
			is_carry_forward=1,
		)

		# initial leave allocation = 0.416333
		leave_allocation = create_leave_allocation(
			employee=self.employee.name,
			new_leaves_allocated=0.416333,
			leave_type="_Test_CF_leave",
			from_date=add_months(nowdate(), -12),
			to_date=add_months(nowdate(), -1),
			carry_forward=0,
		)
		leave_allocation.submit()

		# carry forwarded leaves considering
		# new_leaves = 0.58, carry_forwarded = 0.42
		leave_allocation_1 = create_leave_allocation(
			employee=self.employee.name,
			new_leaves_allocated=0.58,
			leave_type="_Test_CF_leave",
			carry_forward=1,
		)
		leave_allocation_1.submit()
		leave_allocation_1.reload()

		self.assertEqual(leave_allocation_1.unused_leaves, 0.42)
		self.assertEqual(leave_allocation_1.total_leaves_allocated, 1)

	def test_carry_forward_leaves_expiry(self):
		create_leave_type(
			leave_type_name="_Test_CF_leave_expiry",
			is_carry_forward=1,
			expire_carry_forwarded_leaves_after_days=90,
		)

		# initial leave allocation
		leave_allocation = create_leave_allocation(
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			leave_type="_Test_CF_leave_expiry",
			from_date=add_months(nowdate(), -24),
			to_date=add_months(nowdate(), -12),
			carry_forward=0,
		)
		leave_allocation.submit()

		leave_allocation = create_leave_allocation(
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			leave_type="_Test_CF_leave_expiry",
			from_date=add_days(nowdate(), -90),
			to_date=add_days(nowdate(), 100),
			carry_forward=1,
		)
		leave_allocation.submit()

		# expires all the carry forwarded leaves after 90 days
		process_expired_allocation()

		# leave allocation with carry forward of only new leaves allocated
		leave_allocation_1 = create_leave_allocation(
			employee=self.employee.name,
			employee_name=self.employee.employee_name,
			leave_type="_Test_CF_leave_expiry",
			carry_forward=1,
			from_date=add_months(nowdate(), 6),
			to_date=add_months(nowdate(), 12),
		)
		leave_allocation_1.submit()

		self.assertEqual(leave_allocation_1.unused_leaves, leave_allocation.new_leaves_allocated)

	def test_carry_forward_leaves_expiry_after_partially_used_leaves(self):
		from hrms.payroll.doctype.salary_slip.test_salary_slip import make_leave_application

		leave_type = create_leave_type(
			leave_type_name="_Test_CF_leave_expiry",
			is_carry_forward=1,
			expire_carry_forwarded_leaves_after_days=90,
		)

		# initial leave allocation = 5
		leave_allocation = create_leave_allocation(
			employee=self.employee.name,
			leave_type="_Test_CF_leave_expiry",
			from_date=add_months(nowdate(), -24),
			to_date=add_months(nowdate(), -12),
			new_leaves_allocated=5,
			carry_forward=0,
		)
		leave_allocation.submit()

		# carry-forward 5 leaves + 15 new leaves
		leave_allocation = create_leave_allocation(
			employee=self.employee.name,
			leave_type="_Test_CF_leave_expiry",
			from_date=add_days(nowdate(), -90),
			to_date=add_days(nowdate(), 100),
			carry_forward=1,
		)
		leave_allocation.submit()

		# leave application for 3 days
		make_leave_application(
			self.employee.name,
			leave_allocation.from_date,
			add_days(leave_allocation.from_date, 2),
			leave_type.name,
		)

		# only unused carry-forwarded leaves should expire
		process_expired_allocation()
		expired_leaves = frappe.db.get_value(
			"Leave Ledger Entry",
			dict(
				transaction_name=leave_allocation.name,
				is_expired=1,
				is_carry_forward=1,
			),
			"leaves",
		)
		self.assertEqual(expired_leaves, -2)

	def test_carry_forward_leaves_expiry_after_completely_used_leaves(self):
		from hrms.payroll.doctype.salary_slip.test_salary_slip import make_leave_application

		leave_type = create_leave_type(
			leave_type_name="_Test_CF_leave_expiry",
			is_carry_forward=1,
			expire_carry_forwarded_leaves_after_days=90,
		)

		# initial leave allocation = 5
		leave_allocation = create_leave_allocation(
			employee=self.employee.name,
			leave_type="_Test_CF_leave_expiry",
			from_date=add_months(nowdate(), -24),
			to_date=add_months(nowdate(), -12),
			new_leaves_allocated=5,
			carry_forward=0,
		)
		leave_allocation.submit()

		# carry-forward 5 leaves + 15 new leaves
		leave_allocation = create_leave_allocation(
			employee=self.employee.name,
			leave_type="_Test_CF_leave_expiry",
			from_date=add_days(nowdate(), -90),
			to_date=add_days(nowdate(), 100),
			carry_forward=1,
		)
		leave_allocation.submit()

		# leave application for 6 days, all cf leaves used
		make_leave_application(
			self.employee.name,
			leave_allocation.from_date,
			add_days(leave_allocation.from_date, 5),
			leave_type.name,
		)

		# 0 leaves should expire
		process_expired_allocation()
		expired_leaves = frappe.db.exists(
			"Leave Ledger Entry",
			dict(
				transaction_name=leave_allocation.name,
				is_expired=1,
				is_carry_forward=1,
			),
		)
		self.assertIsNone(expired_leaves)

	def test_creation_of_leave_ledger_entry_on_submit(self):
		leave_allocation = create_leave_allocation(
			employee=self.employee.name, employee_name=self.employee.employee_name
		)
		leave_allocation.submit()

		leave_ledger_entry = frappe.get_all(
			"Leave Ledger Entry", fields="*", filters=dict(transaction_name=leave_allocation.name)
		)

		self.assertEqual(len(leave_ledger_entry), 1)
		self.assertEqual(leave_ledger_entry[0].employee, leave_allocation.employee)
		self.assertEqual(leave_ledger_entry[0].leave_type, leave_allocation.leave_type)
		self.assertEqual(leave_ledger_entry[0].leaves, leave_allocation.new_leaves_allocated)

		# check if leave ledger entry is deleted on cancellation
		leave_allocation.cancel()
		self.assertFalse(frappe.db.exists("Leave Ledger Entry", {"transaction_name": leave_allocation.name}))

	def test_leave_addition_after_submit(self):
		leave_allocation = create_leave_allocation(
			employee=self.employee.name, employee_name=self.employee.employee_name
		)
		leave_allocation.submit()
		leave_allocation.reload()
		self.assertEqual(leave_allocation.total_leaves_allocated, 15)

		leave_allocation.new_leaves_allocated = 40
		leave_allocation.save()
		leave_allocation.reload()

		updated_entry = frappe.db.get_all(
			"Leave Ledger Entry",
			{"transaction_name": leave_allocation.name},
			pluck="leaves",
			order_by="creation desc",
			limit=1,
		)

		self.assertEqual(updated_entry[0], 25)
		self.assertEqual(leave_allocation.total_leaves_allocated, 40)

	def test_leave_addition_after_submit_with_carry_forward(self):
		from hrms.hr.doctype.leave_application.test_leave_application import (
			create_carry_forwarded_allocation,
		)

		leave_type = create_leave_type(
			leave_type_name="_Test_CF_leave_expiry",
			is_carry_forward=1,
			include_holiday=True,
		)

		leave_allocation = create_carry_forwarded_allocation(self.employee, leave_type)
		# 15 new leaves, 15 carry forwarded leaves
		self.assertEqual(leave_allocation.total_leaves_allocated, 30)

		leave_allocation.new_leaves_allocated = 32
		leave_allocation.save()
		leave_allocation.reload()

		updated_entry = frappe.db.get_all(
			"Leave Ledger Entry",
			{"transaction_name": leave_allocation.name},
			pluck="leaves",
			order_by="creation desc",
			limit=1,
		)
		self.assertEqual(updated_entry[0], 17)
		self.assertEqual(leave_allocation.total_leaves_allocated, 47)

	def test_leave_subtraction_after_submit(self):
		leave_allocation = create_leave_allocation(
			employee=self.employee.name, employee_name=self.employee.employee_name
		)
		leave_allocation.submit()
		leave_allocation.reload()
		self.assertEqual(leave_allocation.total_leaves_allocated, 15)

		leave_allocation.new_leaves_allocated = 10
		leave_allocation.submit()
		leave_allocation.reload()

		updated_entry = frappe.db.get_all(
			"Leave Ledger Entry",
			{"transaction_name": leave_allocation.name},
			pluck="leaves",
			order_by="creation desc",
			limit=1,
		)

		self.assertEqual(updated_entry[0], -5)
		self.assertEqual(leave_allocation.total_leaves_allocated, 10)

	def test_leave_subtraction_after_submit_with_carry_forward(self):
		from hrms.hr.doctype.leave_application.test_leave_application import (
			create_carry_forwarded_allocation,
		)

		leave_type = create_leave_type(
			leave_type_name="_Test_CF_leave_expiry",
			is_carry_forward=1,
			include_holiday=True,
		)

		leave_allocation = create_carry_forwarded_allocation(self.employee, leave_type)
		self.assertEqual(leave_allocation.total_leaves_allocated, 30)

		leave_allocation.new_leaves_allocated = 8
		leave_allocation.save()

		updated_entry = frappe.db.get_all(
			"Leave Ledger Entry",
			{"transaction_name": leave_allocation.name},
			pluck="leaves",
			order_by="creation desc",
			limit=1,
		)
		self.assertEqual(updated_entry[0], -7)
		self.assertEqual(leave_allocation.total_leaves_allocated, 23)

	def test_validation_against_leave_application_after_submit(self):
		from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list

		make_holiday_list()
		frappe.db.set_value(
			"Company", self.employee.company, "default_holiday_list", "Salary Slip Test Holiday List"
		)

		leave_allocation = create_leave_allocation(
			employee=self.employee.name, employee_name=self.employee.employee_name
		)
		leave_allocation.submit()
		self.assertTrue(leave_allocation.total_leaves_allocated, 15)

		leave_application = frappe.get_doc(
			{
				"doctype": "Leave Application",
				"employee": self.employee.name,
				"leave_type": "_Test Leave Type",
				"from_date": add_months(nowdate(), 2),
				"to_date": add_months(add_days(nowdate(), 10), 2),
				"company": self.employee.company,
				"docstatus": 1,
				"status": "Approved",
				"leave_approver": "test@example.com",
			}
		)
		leave_application.submit()
		leave_application.reload()

		# allocate less leaves than the ones which are already approved
		leave_allocation.new_leaves_allocated = leave_application.total_leave_days - 1
		leave_allocation.total_leaves_allocated = leave_application.total_leave_days - 1
		self.assertRaises(frappe.ValidationError, leave_allocation.submit)


def create_leave_allocation(**args):
	args = frappe._dict(args)

	emp_id = make_employee("test_emp_leave_allocation@salary.com")
	employee = frappe.get_doc("Employee", emp_id)

	return frappe.get_doc(
		{
			"doctype": "Leave Allocation",
			"__islocal": 1,
			"employee": args.employee or employee.name,
			"employee_name": args.employee_name or employee.employee_name,
			"leave_type": args.leave_type or "_Test Leave Type",
			"from_date": args.from_date or nowdate(),
			"new_leaves_allocated": args.new_leaves_allocated or 15,
			"carry_forward": args.carry_forward or 0,
			"to_date": args.to_date or add_months(nowdate(), 12),
		}
	)


test_dependencies = ["Employee", "Leave Type"]
