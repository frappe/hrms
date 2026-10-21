# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.job_opening.job_opening import close_expired_job_openings
from hrms.hr.doctype.job_opening.test_job_opening import get_job_opening
from hrms.hr.doctype.job_requisition.job_requisition import make_job_opening
from hrms.tests.utils import HRMSTestSuite


class TestJobRequisition(HRMSTestSuite):
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
		job_req = make_job_requisition(requested_by=self.employee, no_of_positions=2)
		job_opening = get_job_opening(
			job_title="Associate Opening",
			company="_Test Company",
			designation=job_req.designation,
			department=job_req.department,
		).insert()

		job_req.associate_job_opening(job_opening.name)
		job_opening.reload()

		self.assertEqual(job_opening.job_requisition, job_req.name)
		self.assertEqual(job_opening.vacancies, 2)

	def test_associate_job_opening_validates_requisition_and_opening(self):
		job_req = make_job_requisition(requested_by=self.employee)
		other_opening = get_job_opening(
			job_title="Other Designation Opening", company="_Test Company"
		).insert()
		self.assertRaises(frappe.ValidationError, job_req.associate_job_opening, other_opening.name)
		self.assertFalse(frappe.db.get_value("Job Opening", other_opening.name, "job_requisition"))

		job_req.db_set("status", "Pending")
		opening = get_job_opening(
			job_title="Pending Requisition Opening",
			company="_Test Company",
			designation=job_req.designation,
			department=job_req.department,
		).insert()
		self.assertRaises(frappe.ValidationError, job_req.associate_job_opening, opening.name)

	def test_completed_on_kept_on_later_save_of_closed_opening(self):
		job_req = make_job_requisition(requested_by=self.employee)
		job_opening = make_job_opening(job_req.name)
		job_opening.posted_on = "2023-01-01"
		job_opening.insert()
		job_opening.status = "Closed"
		job_opening.closed_on = "2023-01-31"
		job_opening.save()
		self.assertEqual(
			str(frappe.db.get_value("Job Requisition", job_req.name, "completed_on")), "2023-01-31"
		)

		job_opening.description = "Edited later"
		job_opening.save()

		job_req.reload()
		self.assertEqual(str(job_req.completed_on), "2023-01-31")
		self.assertEqual(job_req.time_to_fill, 2592000)

	def test_requisition_unchanged_when_scheduler_closes_expired_opening(self):
		job_req = make_job_requisition(requested_by=self.employee)
		job_opening = make_job_opening(job_req.name)
		job_opening.posted_on = add_days(getdate(), -10)
		job_opening.closes_on = add_days(getdate(), -1)
		job_opening.insert()

		close_expired_job_openings()

		self.assertEqual(frappe.db.get_value("Job Opening", job_opening.name, "status"), "Closed")
		job_req.reload()
		self.assertEqual(job_req.status, "Open & Approved")
		self.assertFalse(job_req.completed_on)

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
