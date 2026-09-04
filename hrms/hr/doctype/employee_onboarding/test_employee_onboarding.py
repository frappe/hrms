# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date

import frappe
from frappe.utils import add_days, getdate

from hrms.hr.doctype.employee_onboarding.employee_onboarding import (
	IncompleteTaskError,
	make_employee,
)
from hrms.hr.doctype.job_offer.test_job_offer import create_job_offer
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.tests.test_utils import create_company
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeOnboarding(HRMSTestSuite):
	def test_employee_onboarding_incomplete_task(self):
		onboarding = create_employee_onboarding()

		project_name = frappe.db.get_value("Project", onboarding.project, "project_name")
		self.assertEqual(project_name, "Employee Onboarding : test@engineer.com")

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
		self.assertEqual(employee.employee_name, "Test Engineer")

	def test_task_dates_skip_holidays(self):
		boarding_begins_on = getdate()
		onboarding = create_employee_onboarding(
			boarding_begins_on=boarding_begins_on,
			holidays=[
				{"holiday_date": add_days(boarding_begins_on, 1), "description": "Test Holiday"},
				{"holiday_date": add_days(boarding_begins_on, 2), "description": "Test Holiday"},
				# half days are working days, so dates should not be pushed past them
				{
					"holiday_date": add_days(boarding_begins_on, 3),
					"description": "Test Half Day Holiday",
					"is_half_day": 1,
				},
			],
		)

		# first activity begins on day 0 and ends on day 1, which falls in the holiday block
		start_date, end_date = get_task_dates(onboarding.activities[0].task)
		self.assertEqual(start_date, boarding_begins_on)
		self.assertEqual(end_date, add_days(boarding_begins_on, 3))

		# second activity begins on day 1 and ends on day 2, both in the holiday block
		start_date, end_date = get_task_dates(onboarding.activities[1].task)
		self.assertEqual(start_date, add_days(boarding_begins_on, 3))
		self.assertEqual(end_date, add_days(boarding_begins_on, 3))

	def test_holidays_are_fetched_in_a_single_query(self):
		boarding_begins_on = getdate()
		onboarding = create_employee_onboarding(
			boarding_begins_on=boarding_begins_on,
			holidays=[
				{"holiday_date": add_days(boarding_begins_on, day), "description": "Test Holiday"}
				for day in range(1, 8)
			],
		)
		holiday_list = onboarding.get_holiday_list()

		# dates walk over a week of holidays, but the holidays are read only once
		with count_queries() as queries:
			holidays = onboarding.get_upcoming_holidays(holiday_list)
			for activity in onboarding.activities:
				onboarding.get_task_dates(activity, holidays)

		holiday_queries = [query for query in queries if "`tabHoliday`" in query]
		self.assertEqual(len(holiday_queries), 1, msg="\n\n".join(holiday_queries))

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


@contextmanager
def count_queries() -> Iterator[list[str]]:
	"""Collect the queries fired inside the block, so N+1s can be asserted against."""
	queries = []
	original_sql = frappe.db.__class__.sql

	def counting_sql(self, query, *args, **kwargs):
		queries.append(str(query))
		return original_sql(self, query, *args, **kwargs)

	frappe.db.__class__.sql = counting_sql
	try:
		yield queries
	finally:
		frappe.db.__class__.sql = original_sql


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
	job_offer.submit()
	return job_offer


def create_employee_onboarding(holidays: list | None = None, boarding_begins_on: date | str | None = None):
	applicant = get_job_applicant()
	job_offer = get_job_offer(applicant.name)

	boarding_begins_on = getdate(boarding_begins_on)
	holiday_list = make_holiday_list(
		"_Test Employee Boarding", from_date=boarding_begins_on, to_date=add_days(boarding_begins_on, 30)
	)
	holiday_list = frappe.get_doc("Holiday List", holiday_list)
	holiday_list.holidays = []
	for holiday in holidays or []:
		holiday_list.append("holidays", holiday)
	holiday_list.save()

	onboarding = frappe.new_doc("Employee Onboarding")
	onboarding.job_applicant = applicant.name
	onboarding.job_offer = job_offer.name
	onboarding.date_of_joining = onboarding.boarding_begins_on = boarding_begins_on
	onboarding.company = "_Test Company"
	onboarding.holiday_list = holiday_list.name
	onboarding.designation = "Engineer"
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
