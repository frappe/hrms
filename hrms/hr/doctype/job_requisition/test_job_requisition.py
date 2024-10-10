# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.job_opening.test_job_opening import get_job_opening
from hrms.hr.doctype.job_requisition.job_requisition import make_job_opening


class TestJobRequisition(IntegrationTestCase):
	def setUp(self):
		self.employee = make_employee("test_employee_1@company.com", company="_Test Company")

	def test_make_job_opening(self):
		job_req = make_job_requisition(requested_by=self.employee)

		job_opening = make_job_opening(job_req.name)
		job_opening.status = "Closed"
		job_opening.save()

		job_req.reload()

		self.assertEqual(job_opening.job_requisition, job_req.name)
		self.assertEqual(job_req.status, "Filled")

	def test_associate_job_opening(self):
		job_req = make_job_requisition(requested_by=self.employee)
		job_opening = get_job_opening(company="_Test Company").insert()

		job_req.associate_job_opening(job_opening.name)
		job_opening.reload()

		self.assertEqual(job_opening.job_requisition, job_req.name)

	def test_time_to_fill(self):
		job_req = make_job_requisition(requested_by=self.employee)
		job_req.status = "Filled"
		job_req.completed_on = "2023-01-31"
		job_req.save()

		# 30 days from posting date to completion date = 2592000 seconds (duration field)
		self.assertEqual(job_req.time_to_fill, 2592000)


def make_job_requisition(**args):
	frappe.db.delete("Job Requisition")
	args = frappe._dict(args)

	return frappe.get_doc(
		{
			"doctype": "Job Requisition",
			"designation": args.designation or create_designation().name,
			"department": args.department or frappe.db.get_value("Employee", args.requested_by, "department"),
			"no_of_positions": args.no_of_positions or 1,
			"expected_compensation": args.expected_compensation or 500000,
			"company": "_Test Company",
			"status": args.status or "Open & Approved",
			"requested_by": args.requested_by or "_Test Employee",
			"posting_date": args.posting_date or "2023-01-01",
			"expected_by": args.expected_by or "2023-01-15",
			"description": "Test",
			"reason_for_requesting": "Test",
		}
	).insert()
