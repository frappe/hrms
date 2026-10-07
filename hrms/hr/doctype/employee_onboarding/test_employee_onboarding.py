# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, getdate

from hrms.hr.doctype.employee_onboarding.employee_onboarding import make_employee, split_full_name
from hrms.hr.doctype.employee_onboarding_activity.employee_onboarding_activity import (
	STANDARD_ACTIVITIES,
	create_standard_activities,
)
from hrms.hr.doctype.job_offer.job_offer import make_employee_onboarding
from hrms.hr.doctype.job_offer.test_job_offer import create_job_offer
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeOnboarding(HRMSTestSuite):
	def setUp(self):
		create_standard_activities()

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

	def test_standard_activities_come_first_then_the_onboardings_own(self):
		onboarding = create_employee_onboarding(submit=False)

		names = [row.activity_name for row in onboarding.activities]
		standard = [activity["title"] for activity in STANDARD_ACTIVITIES]
		self.assertEqual(names, [*standard, "Assign ID Card", "Assign a laptop"])
		self.assertTrue(all(row.status == "Pending" for row in onboarding.activities))
		self.assertEqual(get_row(onboarding, "Assign Leave Policy").action, "Assign")
		self.assertEqual(
			get_row(onboarding, "Assign Leave Policy").reference_doctype, "Leave Policy Assignment"
		)
		self.assertEqual(get_row(onboarding, "Assign ID Card").action, "Manual")

	def test_standard_activities_survive_a_resave_without_duplicates(self):
		onboarding = create_employee_onboarding(submit=False)
		onboarding.activities = [row for row in onboarding.activities if row.action == "Manual"]
		onboarding.save()

		names = [row.activity_name for row in onboarding.activities]
		self.assertEqual(len(names), len(set(names)))
		self.assertIn("Create Employee", names)

	def test_due_date_defaults_to_the_offset_from_onboarding_start(self):
		onboarding = create_employee_onboarding(submit=False)

		self.assertEqual(getdate(get_row(onboarding, "Create User").due_date), getdate())
		self.assertEqual(getdate(get_row(onboarding, "Assign a laptop").due_date), add_days(getdate(), 1))

	def test_disabled_standard_activity_is_not_added(self):
		frappe.db.set_value("Employee Onboarding Activity", "Assign Shift Schedule", "enabled", 0)
		self.addCleanup(
			frappe.db.set_value, "Employee Onboarding Activity", "Assign Shift Schedule", "enabled", 1
		)
		onboarding = create_employee_onboarding(submit=False)

		self.assertNotIn("Assign Shift Schedule", [row.activity_name for row in onboarding.activities])

	def test_offer_defaults_come_from_the_job_offer(self):
		onboarding = create_employee_onboarding(submit=False)
		offer_holiday_list = frappe.db.get_value("Job Offer", onboarding.job_offer, "holiday_list")

		defaults = onboarding.get_offer_defaults()
		self.assertEqual(
			defaults["Holiday List Assignment"], {"fieldname": "holiday_list", "value": offer_holiday_list}
		)
		self.assertNotIn("Shift Assignment", defaults)

	def test_boarding_status_tracks_progress(self):
		onboarding = create_employee_onboarding(with_activities=False)
		self.assertEqual(onboarding.boarding_status, "Pending")

		onboarding.db_set("company_email", "asha.status@example.com")
		onboarding.reload()
		onboarding.create_user()
		onboarding.reload()
		self.assertEqual(onboarding.boarding_status, "In Process")
		self.assertEqual(get_row(onboarding, "Create User").status, "Completed")

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
		self.assertEqual(get_row(onboarding, "Assign ID Card").status, "Completed")
		self.assertEqual(get_row(onboarding, "Create Employee").status, "Skipped")

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

		onboarding.reload()
		self.assertEqual(get_row(onboarding, "Create Employee").status, "Completed")
		self.assertEqual(get_row(onboarding, "Assign Holiday List").status, "Pending")

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
		onboarding.sync_activities()
		onboarding.reload()

		row = get_row(onboarding, "Assign Holiday List")
		self.assertEqual(row.status, "Completed")
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

	def test_skipping_an_activity_marks_it_skipped(self):
		onboarding = create_employee_onboarding(submit=False)

		onboarding.skip_activity(get_row(onboarding, "Assign Shift Type").name)
		onboarding.reload()

		self.assertEqual(get_row(onboarding, "Assign Shift Type").status, "Skipped")

	def test_only_manual_activities_are_completed_by_hand(self):
		onboarding = create_employee_onboarding(submit=False)

		onboarding.complete_activity(get_row(onboarding, "Assign ID Card").name)
		onboarding.reload()
		self.assertEqual(get_row(onboarding, "Assign ID Card").status, "Completed")

		with self.assertRaises(frappe.ValidationError):
			onboarding.complete_activity(get_row(onboarding, "Create Employee").name)

	def test_assigning_an_activity_gives_the_user_a_todo_of_their_own(self):
		onboarding = create_employee_onboarding(submit=False)
		first, second = (
			get_test_user("onboarding_first@example.com"),
			get_test_user("onboarding_second@example.com"),
		)
		row = get_row(onboarding, "Create Employee")

		onboarding.assign_activity(row.name, first)
		onboarding.reload()
		first_todo = get_row(onboarding, "Create Employee").todo
		self.assertEqual(frappe.db.get_value("ToDo", first_todo, ["allocated_to", "status"]), (first, "Open"))

		onboarding.assign_activity(row.name, second)
		onboarding.reload()
		second_todo = get_row(onboarding, "Create Employee").todo
		self.assertNotEqual(first_todo, second_todo)
		self.assertEqual(frappe.db.get_value("ToDo", first_todo, "status"), "Cancelled")
		self.assertEqual(frappe.db.get_value("ToDo", second_todo, "allocated_to"), second)

	def test_due_date_change_reaches_the_todo(self):
		onboarding = create_employee_onboarding(submit=False)
		row = get_row(onboarding, "Create User")
		onboarding.assign_activity(row.name, get_test_user("onboarding_due@example.com"))

		due_date = add_days(getdate(), 5)
		onboarding.set_activity_due_date(row.name, str(due_date))
		onboarding.reload()

		row = get_row(onboarding, "Create User")
		self.assertEqual(getdate(row.due_date), due_date)
		self.assertEqual(getdate(frappe.db.get_value("ToDo", row.todo, "date")), due_date)

	def test_finishing_an_activity_closes_its_todo(self):
		onboarding = create_employee_onboarding(submit=False)
		row = get_row(onboarding, "Assign ID Card")
		onboarding.assign_activity(row.name, get_test_user("onboarding_close@example.com"))
		onboarding.reload()
		todo = get_row(onboarding, "Assign ID Card").todo

		onboarding.complete_activity(row.name)

		self.assertEqual(frappe.db.get_value("ToDo", todo, "status"), "Closed")

	def test_template_cannot_list_a_standard_activity(self):
		template = frappe.new_doc("Employee Onboarding Template")
		template.title = "_Test Template With Standard Row"
		template.append("activities", {"activity_name": "Create User", "activity": "Create User"})

		with self.assertRaises(frappe.ValidationError):
			template.insert()

	def test_mark_onboarding_as_completed(self):
		onboarding = create_employee_onboarding(submit=False)
		self.assertEqual(onboarding.boarding_status, "Pending")

		onboarding.mark_onboarding_as_completed()

		self.assertEqual(onboarding.boarding_status, "Completed")
		self.assertTrue(all(row.status in ("Completed", "Skipped") for row in onboarding.activities))


class TestEmployeeOnboardingActivity(HRMSTestSuite):
	def setUp(self):
		create_standard_activities()

	def test_standard_activity_cannot_be_deleted(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Employee Onboarding Activity", "Create User")

	def test_standard_activity_keeps_its_action(self):
		activity = frappe.get_doc("Employee Onboarding Activity", "Create Employee")
		activity.action = "Manual"

		with self.assertRaises(frappe.ValidationError):
			activity.save()

	def test_an_action_is_done_by_one_activity_only(self):
		activity = frappe.new_doc("Employee Onboarding Activity")
		activity.title = "_Test Second Leave Policy"
		activity.action = "Assign"
		activity.reference_doctype = "Leave Policy Assignment"

		with self.assertRaises(frappe.ValidationError):
			activity.insert()


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


def get_row(onboarding, activity_name):
	return next(row for row in onboarding.activities if row.activity_name == activity_name)


def get_test_user(email):
	if not frappe.db.exists("User", email):
		frappe.get_doc({"doctype": "User", "email": email, "first_name": email.split("@")[0]}).insert(
			ignore_permissions=True
		)
	return email
