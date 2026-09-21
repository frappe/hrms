# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate

from hrms.hr.doctype.employee_onboarding.employee_onboarding import (
	ASSIGNMENT_MASTERS,
	make_employee,
	split_full_name,
)
from hrms.hr.doctype.job_offer.job_offer import make_employee_onboarding
from hrms.hr.doctype.job_offer.test_job_offer import create_job_offer
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeOnboarding(HRMSTestSuite):
	def test_split_full_name(self):
		self.assertEqual(split_full_name("Asha"), ("Asha", "", ""))
		self.assertEqual(split_full_name("Asha Rao"), ("Asha", "", "Rao"))
		self.assertEqual(split_full_name("Asha Bhanu Rao"), ("Asha", "Bhanu", "Rao"))
		self.assertEqual(split_full_name("Asha Bhanu Devi Rao"), ("Asha", "Bhanu", "Devi Rao"))
		self.assertEqual(split_full_name(""), ("", "", ""))

	def test_offer_maps_onto_onboarding(self):
		job_offer = get_job_offer(get_job_applicant().name)
		onboarding = make_employee_onboarding(job_offer.name)

		self.assertEqual(onboarding.job_offer, job_offer.name)
		self.assertEqual(onboarding.employee_name, job_offer.applicant_name)
		self.assertEqual(onboarding.company, job_offer.company)
		self.assertEqual(onboarding.date_of_joining, job_offer.date_of_joining)
		self.assertEqual(onboarding.boarding_begins_on, job_offer.date_of_joining)

	def test_no_project_or_task_is_created(self):
		onboarding = create_employee_onboarding(submit=False)

		self.assertFalse(onboarding.project)
		self.assertFalse(frappe.db.exists("Project", {"project_name": ("like", "%Employee Onboarding%")}))
		self.assertFalse([row.task for row in onboarding.activities if row.task])

	def test_assignments_are_seeded_from_the_offer(self):
		onboarding = create_employee_onboarding(submit=False)

		self.assertEqual(
			[row.master for row in onboarding.assignments],
			[master["master"] for master in ASSIGNMENT_MASTERS],
		)
		self.assertTrue(all(row.status == "Pending" for row in onboarding.assignments))

		holiday_row = next(row for row in onboarding.assignments if row.master == "Holiday List")
		offer_holiday_list = frappe.db.get_value("Job Offer", onboarding.job_offer, "holiday_list")
		self.assertEqual(holiday_row.offer_value, offer_holiday_list)

		shift_row = next(row for row in onboarding.assignments if row.master == "Shift Type")
		self.assertIsNone(shift_row.offer_value)

	def test_boarding_status_tracks_progress(self):
		onboarding = create_employee_onboarding(with_activities=False)
		self.assertEqual(onboarding.boarding_status, "Pending")

		onboarding.db_set("documents_requested_on", frappe.utils.now_datetime())
		onboarding.reload()
		onboarding.save()
		self.assertEqual(onboarding.boarding_status, "In Process")

	def test_create_user_uses_the_selected_email(self):
		onboarding = create_employee_onboarding(submit=False)
		onboarding.db_set("company_email", "asha.company@example.com")
		onboarding.db_set("personal_email", "asha.personal@example.com")
		onboarding.db_set("create_user_for", "Personal Email")
		onboarding.reload()

		user = onboarding.create_user()

		self.assertEqual(user, "asha.personal@example.com")
		self.assertEqual(onboarding.user, user)
		self.assertEqual(frappe.db.get_value("User", user, "first_name"), "Test")

	def test_self_service_role_is_granted_with_the_employee(self):
		onboarding = create_employee_onboarding(submit=False)
		onboarding.db_set("company_email", "asha.ess@example.com")
		onboarding.db_set("create_user_for", "Company Email")
		onboarding.db_set("gender", "Female")
		onboarding.db_set("date_of_birth", "1990-05-08")
		onboarding.reload()

		user = onboarding.create_user()
		self.assertNotIn("Employee Self Service", frappe.get_roles(user))

		onboarding.reload()
		onboarding.create_employee()

		frappe.clear_cache(user=user)
		self.assertIn("Employee Self Service", frappe.get_roles(user))

	def test_submitting_completes_the_remaining_steps(self):
		onboarding = create_employee_onboarding(submit=False)
		self.assertEqual(onboarding.boarding_status, "Pending")

		onboarding.submit()

		self.assertEqual(onboarding.boarding_status, "Completed")
		self.assertTrue(all(row.completed for row in onboarding.activities))
		self.assertTrue(all(row.status == "Skipped" for row in onboarding.assignments))

	def test_employee_is_created_from_the_onboarding(self):
		onboarding = create_employee_onboarding(submit=False)
		onboarding.db_set("gender", "Female")
		onboarding.db_set("date_of_birth", "1990-05-08")
		onboarding.reload()

		employee = make_employee(onboarding.name)
		employee.insert()

		self.assertEqual(employee.employee_name, "Test Engineer")
		self.assertEqual(employee.first_name, "Test")
		self.assertEqual(employee.last_name, "Engineer")
		self.assertEqual(employee.job_offer, onboarding.job_offer)

	def test_assignment_row_ticks_from_the_real_assignment(self):
		onboarding = create_employee_onboarding(submit=False)
		onboarding.db_set("gender", "Female")
		onboarding.db_set("date_of_birth", "1990-05-08")
		onboarding.reload()
		employee = onboarding.create_employee()

		row = next(row for row in onboarding.assignments if row.master == "Holiday List")
		self.assertEqual(row.status, "Pending")

		assignment = frappe.get_doc(
			{
				"doctype": "Holiday List Assignment",
				"applicable_for": "Employee",
				"assigned_to": employee,
				"employee_company": onboarding.company,
				"holiday_list": get_boarding_holiday_list(),
				"from_date": getdate(),
			}
		).insert()
		assignment.submit()

		onboarding.reload()
		onboarding.sync_assignments()
		onboarding.reload()

		row = next(row for row in onboarding.assignments if row.master == "Holiday List")
		self.assertEqual(row.status, "Assigned")
		self.assertEqual(row.reference_name, assignment.name)

	def test_company_holiday_list_prefers_the_company_assignment(self):
		onboarding = create_employee_onboarding(submit=False)

		company_list = frappe.copy_doc(frappe.get_doc("Holiday List", get_boarding_holiday_list()))
		company_list.holiday_list_name = "_Test Company Wide Holidays"
		company_list.insert()

		assignment = frappe.get_doc(
			{
				"doctype": "Holiday List Assignment",
				"applicable_for": "Company",
				"assigned_to": onboarding.company,
				"holiday_list": company_list.name,
				"from_date": add_days(getdate(), 1),
			}
		).insert()
		assignment.submit()

		self.assertEqual(onboarding.get_company_holiday_list(), company_list.name)

	def test_skipping_an_assignment_marks_it_skipped(self):
		onboarding = create_employee_onboarding(submit=False)

		onboarding.set_assignment("Shift Type", None)

		row = next(row for row in onboarding.assignments if row.master == "Shift Type")
		self.assertEqual(row.status, "Skipped")

	def test_mark_onboarding_as_completed(self):
		onboarding = create_employee_onboarding(submit=False)
		self.assertEqual(onboarding.boarding_status, "Pending")

		onboarding.mark_onboarding_as_completed()

		self.assertEqual(onboarding.boarding_status, "Completed")
		self.assertTrue(all(row.completed for row in onboarding.activities))
		self.assertTrue(all(row.status == "Skipped" for row in onboarding.assignments))


def get_job_applicant():
	if frappe.db.exists("Job Applicant", "test@engineer.com"):
		return frappe.get_doc("Job Applicant", "test@engineer.com")
	applicant = frappe.new_doc("Job Applicant")
	applicant.applicant_name = "Test Engineer"
	applicant.email_id = "test@engineer.com"
	applicant.designation = "Engineer"
	applicant.status = "Open"
	applicant.cover_letter = "I am a great Engineer."
	applicant.insert()
	return applicant


def get_job_offer(applicant_name):
	job_offer = frappe.db.exists("Job Offer", {"job_applicant": applicant_name})
	if job_offer:
		return frappe.get_doc("Job Offer", job_offer)

	job_offer = create_job_offer(job_applicant=applicant_name, company="_Test Company")
	job_offer.holiday_list = get_boarding_holiday_list()
	job_offer.save()
	job_offer.submit()
	return job_offer


def get_boarding_holiday_list():
	holiday_list = frappe.get_doc("Holiday List", make_holiday_list("_Test Employee Boarding"))
	holiday_list.holidays = []
	holiday_list.save()
	return holiday_list.name


def create_employee_onboarding(submit=False, with_activities=True):
	applicant = get_job_applicant()
	job_offer = get_job_offer(applicant.name)

	onboarding = frappe.new_doc("Employee Onboarding")
	onboarding.job_applicant = applicant.name
	onboarding.job_offer = job_offer.name
	onboarding.date_of_joining = onboarding.boarding_begins_on = getdate()
	onboarding.company = "_Test Company"
	onboarding.holiday_list = get_boarding_holiday_list()
	onboarding.designation = "Engineer"
	onboarding.employee_name = applicant.applicant_name
	if with_activities:
		onboarding.append(
			"activities",
			{"activity_name": "Assign ID Card", "role": "HR User", "begin_on": 0, "duration": 1},
		)
		onboarding.append(
			"activities",
			{"activity_name": "Assign a laptop", "role": "HR User", "begin_on": 1, "duration": 1},
		)
	onboarding.insert()
	if submit:
		onboarding.submit()

	return onboarding
