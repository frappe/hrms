# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.employee_referral.employee_referral import (
	create_additional_salary,
	create_job_applicant,
)


class TestEmployeeReferral(IntegrationTestCase):
	def setUp(self):
		frappe.db.sql("DELETE FROM `tabJob Applicant`")
		frappe.db.sql("DELETE FROM `tabEmployee Referral`")

	def test_workflow_and_status_sync(self):
		emp_ref = create_employee_referral()

		# Check Initial status
		self.assertTrue(emp_ref.status, "Pending")

		job_applicant = create_job_applicant(emp_ref.name)

		# Check status sync
		emp_ref.reload()
		self.assertTrue(emp_ref.status, "In Process")

		job_applicant.reload()
		job_applicant.status = "Rejected"
		job_applicant.save()

		emp_ref.reload()
		self.assertTrue(emp_ref.status, "Rejected")

		job_applicant.reload()
		job_applicant.status = "Accepted"
		job_applicant.save()

		emp_ref.reload()
		self.assertTrue(emp_ref.status, "Accepted")

		# Check for Referral reference in additional salary

		add_sal = create_additional_salary(emp_ref)
		self.assertTrue(add_sal.ref_docname, emp_ref.name)

	def tearDown(self):
		frappe.db.sql("DELETE FROM `tabJob Applicant`")
		frappe.db.sql("DELETE FROM `tabEmployee Referral`")


def create_employee_referral():
	emp_ref = frappe.new_doc("Employee Referral")
	emp_ref.first_name = "Mahesh"
	emp_ref.last_name = "Singh"
	emp_ref.email = "a@b.c"
	emp_ref.date = today()
	emp_ref.for_designation = create_designation().name
	emp_ref.referrer = make_employee("testassetmovemp@example.com", company="_Test Company")
	emp_ref.is_applicable_for_employee_referral_compensation = 1
	emp_ref.save()
	emp_ref.submit()

	return emp_ref
