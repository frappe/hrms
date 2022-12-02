# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from hrms.hr.doctype.auto_leave_allocation.auto_leave_allocation import OverlapError

test_records = frappe.get_test_records("Auto Leave Allocation")
test_dependencies = ["Employee", "Leave Type"]


class TestAutoLeaveAllocation(FrappeTestCase):
	def setUp(self):
		for dt in ["Auto Leave Allocation", "Leave Allocation"]:
			frappe.db.delete(dt)

		frappe.db.set_value("Leave Type", "Casual Leave", "max_leaves_allowed", 0)
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.db.rollback()
		frappe.set_user("Administrator")

	def test_leave_allocation(self):
		ala_doc = frappe.copy_doc(test_records[1])
		ala_doc.submit()

		alloc_count = frappe.db.get_all(
			"Leave Allocation",
			filters={
				"from_date": ["between", [ala_doc.start_date, ala_doc.end_date]],
				"leave_type": ala_doc.leave_type,
			},
			fields=["count(name) as count"],
			group_by="employee",
		)

		for alloc in alloc_count:
			self.assertEqual(alloc["count"], 14)

	def test_overlap_error(self):
		frappe.copy_doc(test_records[0]).insert()
		ala_doc = frappe.copy_doc(test_records[0])

		ala_doc.start_date = "2022-11-25"
		ala_doc.end_date = "2022-12-05"
		self.assertRaises(OverlapError, ala_doc.save)

		ala_doc.start_date = "2022-12-05"
		ala_doc.end_date = "2022-12-15"
		self.assertRaises(OverlapError, ala_doc.save)

		ala_doc.start_date = "2022-12-25"
		ala_doc.end_date = "2023-01-15"
		self.assertRaises(OverlapError, ala_doc.save)

		ala_doc.start_date = "2023-01-05"
		ala_doc.end_date = "2023-01-15"
		ala_doc.save()

	def test_start_end_dates(self):
		ala_doc = frappe.copy_doc(test_records[0])

		ala_doc.start_date = "2022-11-25"
		ala_doc.end_date = "2021-12-05"
		self.assertRaises(frappe.ValidationError, ala_doc.save)
