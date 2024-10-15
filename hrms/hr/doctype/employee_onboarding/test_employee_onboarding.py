# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate

from hrms.hr.doctype.employee_onboarding.employee_onboarding import (
	IncompleteTaskError,
	make_employee,
)
from hrms.hr.doctype.job_offer.test_job_offer import create_job_offer
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.tests.test_utils import create_company


class TestEmployeeOnboarding(IntegrationTestCase):
	def setUp(self):
		create_company()
		if frappe.db.exists("Employee Onboarding", {"employee_name": "Test Researcher"}):
			frappe.db.sql("delete from `tabEmployee Onboarding` where employee_name=%s", "Test Researcher")

		project = "Employee Onboarding : test@researcher.com"
		frappe.db.sql("delete from tabProject where project_name=%s", project)
		frappe.db.sql("delete from tabTask where project=%s", project)

	def test_employee_onboarding_incomplete_task(self):
		onboarding = create_employee_onboarding()

		project_name = frappe.db.get_value("Project", onboarding.project, "project_name")
		self.assertEqual(project_name, "Employee Onboarding : test@researcher.com")

		# don't allow making employee if onboarding is not complete
		self.assertRaises(IncompleteTaskError, make_employee, onboarding.name)

		# boarding status
		self.assertEqual(onboarding.boarding_status, "Pending")

		# start and end dates
		start_date, end_date = get_task_dates(onboarding.activities[0].task)
		self.assertEqual(start_date, onboarding.boarding_begins_on)
		self.assertEqual(end_date, add_days(start_date, onboarding.activities[0].duration))

		start_date, end_date = get_task_dates(onboarding.activities[1].task)
		self.assertEqual(
			start_date, add_days(onboarding.boarding_begins_on, onboarding.activities[0].duration)
		)
		self.assertEqual(end_date, add_days(start_date, onboarding.activities[1].duration))

		# complete the task
		project = frappe.get_doc("Project", onboarding.project)
		for task in frappe.get_all("Task", dict(project=project.name)):
			task = frappe.get_doc("Task", task.name)
			task.status = "Completed"
			task.save()

		# boarding status
		onboarding.reload()
		self.assertEqual(onboarding.boarding_status, "Completed")

		# make employee
		onboarding.reload()
		employee = make_employee(onboarding.name)
		employee.first_name = employee.employee_name
		employee.date_of_joining = getdate()
		employee.date_of_birth = "1990-05-08"
		employee.gender = "Female"
		employee.insert()
		self.assertEqual(employee.employee_name, "Test Researcher")

	def test_mark_onboarding_as_completed(self):
		onboarding = create_employee_onboarding()

		# before marking as completed
		self.assertEqual(onboarding.boarding_status, "Pending")
		project = frappe.get_doc("Project", onboarding.project)
		self.assertEqual(project.status, "Open")
		for task_status in frappe.get_all("Task", dict(project=project.name), pluck="status"):
			self.assertEqual(task_status, "Open")

		onboarding.reload()
		onboarding.mark_onboarding_as_completed()

		# after marking as completed
		self.assertEqual(onboarding.boarding_status, "Completed")
		project.reload()
		self.assertEqual(project.status, "Completed")
		for task_status in frappe.get_all("Task", dict(project=project.name), pluck="status"):
			self.assertEqual(task_status, "Completed")

	def tearDown(self):
		frappe.db.rollback()


def get_job_applicant():
	if frappe.db.exists("Job Applicant", "test@researcher.com"):
		return frappe.get_doc("Job Applicant", "test@researcher.com")
	applicant = frappe.new_doc("Job Applicant")
	applicant.applicant_name = "Test Researcher"
	applicant.email_id = "test@researcher.com"
	applicant.designation = "Researcher"
	applicant.status = "Open"
	applicant.cover_letter = "I am a great Researcher."
	applicant.insert()
	return applicant


def get_job_offer(applicant_name):
	job_offer = frappe.db.exists("Job Offer", {"job_applicant": applicant_name})
	if job_offer:
		return frappe.get_doc("Job Offer", job_offer)

	job_offer = create_job_offer(job_applicant=applicant_name)
	job_offer.submit()
	return job_offer


def create_employee_onboarding():
	applicant = get_job_applicant()
	job_offer = get_job_offer(applicant.name)

	holiday_list = make_holiday_list("_Test Employee Boarding")
	holiday_list = frappe.get_doc("Holiday List", holiday_list)
	holiday_list.holidays = []
	holiday_list.save()

	onboarding = frappe.new_doc("Employee Onboarding")
	onboarding.job_applicant = applicant.name
	onboarding.job_offer = job_offer.name
	onboarding.date_of_joining = onboarding.boarding_begins_on = getdate()
	onboarding.company = "_Test Company"
	onboarding.holiday_list = holiday_list.name
	onboarding.designation = "Researcher"
	onboarding.append(
		"activities",
		{
			"activity_name": "Assign ID Card",
			"role": "HR User",
			"required_for_employee_creation": 1,
			"begin_on": 0,
			"duration": 1,
		},
	)
	onboarding.append(
		"activities",
		{"activity_name": "Assign a laptop", "role": "HR User", "begin_on": 1, "duration": 1},
	)
	onboarding.status = "Pending"
	onboarding.insert()
	onboarding.submit()

	return onboarding


def get_task_dates(task: str) -> tuple[str, str]:
	start_date, end_date = frappe.db.get_value("Task", task, ["exp_start_date", "exp_end_date"])
	return getdate(start_date), getdate(end_date)
