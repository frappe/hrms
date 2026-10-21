# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, nowdate, today

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.employee_referral.employee_referral import (
	create_additional_salary,
	create_job_applicant,
)
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeReferral(HRMSTestSuite):
	def test_workflow_and_status_sync(self):
		emp_ref = create_employee_referral()

		# Check Initial status
		self.assertEqual(emp_ref.status, "Pending")

		job_applicant = create_job_applicant(emp_ref.name)

		# Check status sync
		emp_ref.reload()
		self.assertEqual(emp_ref.status, "In Process")

		job_applicant.reload()
		job_applicant.status = "Rejected"
		job_applicant.save()

		emp_ref.reload()
		self.assertEqual(emp_ref.status, "Rejected")

		job_applicant.reload()
		job_applicant.status = "Accepted"
		job_applicant.save()

		emp_ref.reload()
		self.assertEqual(emp_ref.status, "Accepted")

		# Check for Referral reference in additional salary

		add_sal = create_additional_salary(emp_ref.name)
		self.assertEqual(add_sal.ref_docname, emp_ref.name)

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

	def test_create_job_applicant_state_checks(self):
		draft = create_employee_referral(email="test_ref_draft@example.com", do_not_submit=True)
		self.assertRaises(frappe.ValidationError, create_job_applicant, draft.name)

		emp_ref = create_employee_referral(email="test_ref_state@example.com")
		job_applicant = create_job_applicant(emp_ref.name)
		self.assertEqual(job_applicant.status, "Open")

		self.assertRaises(frappe.ValidationError, create_job_applicant, emp_ref.name)
		emp_ref.db_set("status", "Pending")
		self.assertRaises(frappe.DuplicateEntryError, create_job_applicant, emp_ref.name)

		rejected = create_employee_referral(email="test_ref_rejected@example.com")
		rejected.status = "Rejected"
		rejected.save()
		self.assertEqual(frappe.db.get_value("Employee Referral", rejected.name, "status"), "Rejected")
		self.assertRaises(frappe.ValidationError, create_job_applicant, rejected.name)

	def test_referral_bonus_paid_once(self):
		from hrms.payroll.doctype.salary_component.test_salary_component import create_salary_component
		from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure

		emp_ref = create_employee_referral(email="test_ref_bonus@example.com")
		emp_ref.db_set({"status": "Accepted", "is_applicable_for_referral_bonus": 1})
		make_salary_structure(
			"Test Salary Structure Referral Bonus",
			"Monthly",
			employee=emp_ref.referrer,
			from_date=add_days(nowdate(), -50),
			company="_Test Company",
		)
		create_salary_component("Referral Bonus")

		def make_bonus():
			additional_salary = create_additional_salary(emp_ref.name)
			additional_salary.salary_component = "Referral Bonus"
			additional_salary.amount = 5000
			additional_salary.payroll_date = nowdate()
			additional_salary.currency = "INR"
			return additional_salary.insert()

		first = make_bonus()
		self.assertRaises(frappe.DuplicateEntryError, create_additional_salary, emp_ref.name)

		second = frappe.copy_doc(first)
		first.submit()
		self.assertEqual(
			frappe.db.get_value("Employee Referral", emp_ref.name, "referral_payment_status"), "Paid"
		)
		self.assertRaises(frappe.ValidationError, second.insert)

		first.cancel()
		self.assertEqual(
			frappe.db.get_value("Employee Referral", emp_ref.name, "referral_payment_status"), "Unpaid"
		)
		self.assertTrue(make_bonus().name)


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
