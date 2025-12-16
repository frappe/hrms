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
		for d in ["Job Applicant", "Employee Referral"]:
			frappe.db.delete(d)

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

	def test_status_on_discard(self):
		refarral = create_employee_referral(do_not_submit=True)
		refarral.discard()
		refarral.reload()
		self.assertEqual(refarral.status, "Cancelled")

	def test_unique_referral(self):
		referral_1 = create_employee_referral(email="test_ref@example.com")
		self.assertRaises(frappe.DuplicateEntryError, create_employee_referral, email="test_ref@example.com")
		referral_1.cancel()
		referral_2 = create_employee_referral(email="test_ref@example.com")
		self.assertTrue(referral_2)


def create_employee_referral(email=None, do_not_submit=False):
	emp_ref = frappe.new_doc("Employee Referral")
	emp_ref.first_name = "Mahesh"
	emp_ref.last_name = "Singh"
	emp_ref.email = email or "a@b.c"
	emp_ref.date = today()
	emp_ref.for_designation = create_designation().name
	emp_ref.referrer = make_employee("testassetmovemp@example.com", company="_Test Company")
	emp_ref.is_applicable_for_employee_referral_compensation = 1
	emp_ref.save()
	if do_not_submit:
		return emp_ref
	emp_ref.submit()

	return emp_ref
