# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.desk.form.linked_with import get_linked_docs_to_delete
from frappe.utils import add_days, getdate

from hrms.hr.doctype.employee_onboarding.employee_onboarding import make_employee, split_full_name
from hrms.hr.doctype.employee_onboarding.onboarding_activities import (
	STANDARD_ACTIVITIES,
	get_template_activities,
)
from hrms.hr.doctype.employee_onboarding_template.employee_onboarding_template import (
	get_standard_activities,
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

	def test_template_rows_become_the_checklist(self):
		onboarding = create_employee_onboarding(submit=False)

		names = [row.activity_name for row in onboarding.activities]
		standard = [activity["activity_name"] for activity in STANDARD_ACTIVITIES]
		self.assertEqual(names, [*standard, "Assign ID Card", "Assign a laptop"])
		self.assertFalse([row for row in onboarding.activities if row.completed or row.skipped or row.status])
		self.assertEqual(get_row(onboarding, "Assign Leave Policy").action, "Assign")
		self.assertEqual(
			get_row(onboarding, "Assign Leave Policy").reference_doctype, "Leave Policy Assignment"
		)
		self.assertEqual(get_row(onboarding, "Assign Leave Policy").depends_on_action, "Create Employee")
		self.assertEqual(get_row(onboarding, "Assign ID Card").action, "Manual")

	def test_resaving_keeps_the_rows_without_duplicates(self):
		onboarding = create_employee_onboarding(submit=False)
		onboarding.save()

		names = [row.activity_name for row in onboarding.activities]
		self.assertEqual(len(names), len(set(names)))

	def test_due_date_defaults_to_the_offset_from_onboarding_start(self):
		onboarding = create_employee_onboarding(submit=False)

		self.assertEqual(getdate(get_row(onboarding, "Create User").due_date), getdate())
		self.assertEqual(getdate(get_row(onboarding, "Assign a laptop").due_date), add_days(getdate(), 1))

	def test_new_template_starts_with_the_standard_activities_once(self):
		template = make_template("_Test Fresh Template", [{"activity_name": "Order a desk"}])

		standard = [activity["activity_name"] for activity in STANDARD_ACTIVITIES]
		self.assertEqual([row.activity_name for row in template.activities], [*standard, "Order a desk"])

		template.activities = [row for row in template.activities if row.action != "Appointment Letter"]
		template.save()
		self.assertNotIn("Appointment Letter", [row.activity_name for row in template.activities])

	def test_template_prefilled_by_the_form_keeps_one_of_each_standard_activity(self):
		template = make_template("_Test Prefilled Template", get_standard_activities())

		standard = [activity["activity_name"] for activity in STANDARD_ACTIVITIES]
		self.assertEqual([row.activity_name for row in template.activities], standard)

	def test_an_onboarding_without_a_template_gets_no_activities(self):
		self.assertEqual(get_template_activities(None), [])

	def test_template_rejects_a_duplicate_action(self):
		template = make_template("_Test Duplicate Template")
		template.append(
			"activities",
			{
				"activity_name": "Assign Leave Policy again",
				"action": "Assign",
				"reference_doctype": "Leave Policy Assignment",
			},
		)

		with self.assertRaises(frappe.ValidationError):
			template.save()

	def test_new_onboarding_uses_the_newest_matching_template(self):
		make_template("_Test Older Engineer Template", designation="Engineer")
		newest = make_template(
			"_Test Newer Engineer Template", [{"activity_name": "Book a desk"}], designation="Engineer"
		)
		make_template(
			"_Test Other Designation Template", designation=make_designation("_Test Designation Elsewhere")
		)

		onboarding = create_employee_onboarding(submit=False, with_activities=False)

		self.assertEqual(onboarding.employee_onboarding_template, newest.name)
		self.assertIn("Book a desk", [row.activity_name for row in onboarding.activities])

	def test_a_blank_template_applies_to_every_onboarding(self):
		blank = make_template("_Test Blank Template")

		onboarding = create_employee_onboarding(submit=False, with_activities=False)

		self.assertEqual(onboarding.employee_onboarding_template, blank.name)

	def test_a_template_set_for_another_value_is_never_picked(self):
		make_template("_Test Blank Fallback Template")
		other = make_template("_Test Other Grade Template", employee_grade=make_grade("_Test Other Grade"))

		onboarding = create_employee_onboarding(submit=False, with_activities=False)

		self.assertNotEqual(onboarding.employee_onboarding_template, other.name)

	def test_hint_shows_until_the_template_has_own_tasks(self):
		template = make_template("_Test Hint Template")
		onboarding = create_employee_onboarding(submit=False, with_activities=False)
		self.assertEqual(onboarding.get_template_hint(), template.name)

		template.append("activities", {"activity_name": "Welcome lunch"})
		template.save()
		self.assertIsNone(onboarding.get_template_hint())

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
		self.assertTrue(get_row(onboarding, "Create User").completed)

	def test_deleting_the_user_keeps_the_onboarding_and_reopens_create_user(self):
		onboarding = create_employee_onboarding(submit=False)
		onboarding.db_set("company_email", "asha.unlink@example.com")
		onboarding.reload()
		user = onboarding.create_user()
		onboarding.reload()
		self.assertTrue(get_row(onboarding, "Create User").completed)
		blockers = get_linked_docs_to_delete("User", user)["docs"]
		self.assertNotIn("Employee Onboarding", [doc["doctype"] for doc in blockers])

		frappe.delete_doc("User", user)

		onboarding.reload()
		self.assertFalse(frappe.db.exists("User", user))
		self.assertIsNone(onboarding.user)
		self.assertFalse(get_row(onboarding, "Create User").completed)

	def test_renaming_the_user_keeps_the_onboarding_on_it(self):
		onboarding = create_employee_onboarding(submit=False)
		onboarding.db_set("company_email", "asha.rename@example.com")
		onboarding.reload()
		user = onboarding.create_user()

		frappe.rename_doc("User", user, "asha.renamed@example.com", force=True)

		onboarding.reload()
		self.assertEqual(onboarding.user, "asha.renamed@example.com")
		self.assertTrue(get_row(onboarding, "Create User").completed)

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
		self.assertTrue(get_row(onboarding, "Assign ID Card").completed)
		self.assertTrue(get_row(onboarding, "Create Employee").skipped)

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
		self.assertTrue(get_row(onboarding, "Create Employee").completed)
		self.assertFalse(get_row(onboarding, "Assign Holiday List").completed)

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
		self.assertTrue(row.completed)
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

		self.assertTrue(get_row(onboarding, "Assign Shift Type").skipped)

	def test_progress_status_is_set_by_hand_and_survives_a_resave(self):
		onboarding = create_employee_onboarding(submit=False)
		row = get_row(onboarding, "Create Employee")

		onboarding.set_activity_progress(row.name, "Stuck")
		onboarding.reload()
		self.assertEqual(get_row(onboarding, "Create Employee").status, "Stuck")
		self.assertEqual(onboarding.boarding_status, "In Process")

		onboarding.save()
		self.assertEqual(get_row(onboarding, "Create Employee").status, "Stuck")

	def test_progress_status_clears_by_hand_and_when_the_activity_finishes(self):
		onboarding = create_employee_onboarding(submit=False)
		stuck, manual = get_row(onboarding, "Create Employee"), get_row(onboarding, "Assign ID Card")

		onboarding.set_activity_progress(stuck.name, "Stuck")
		onboarding.set_activity_progress(stuck.name, None)
		onboarding.set_activity_progress(manual.name, "In Progress")
		onboarding.complete_activity(manual.name)
		onboarding.reload()

		self.assertFalse(get_row(onboarding, "Create Employee").status)
		self.assertFalse(get_row(onboarding, "Assign ID Card").status)
		self.assertTrue(get_row(onboarding, "Assign ID Card").completed)

	def test_progress_status_cannot_finish_or_reopen_an_activity(self):
		onboarding = create_employee_onboarding(submit=False)
		row = get_row(onboarding, "Assign Shift Type")

		with self.assertRaises(frappe.ValidationError):
			onboarding.set_activity_progress(row.name, "Completed")

		onboarding.skip_activity(row.name)
		onboarding.reload()
		with self.assertRaises(frappe.ValidationError):
			onboarding.set_activity_progress(row.name, "In Progress")

	def test_undoing_a_skip_reopens_the_activity(self):
		onboarding = create_employee_onboarding(submit=False)
		row = get_row(onboarding, "Assign Shift Type")

		onboarding.skip_activity(row.name)
		onboarding.unskip_activity(row.name)
		onboarding.reload()

		self.assertFalse(get_row(onboarding, "Assign Shift Type").skipped)
		self.assertFalse(get_row(onboarding, "Assign Shift Type").completed)

	def test_only_manual_activities_are_completed_by_hand(self):
		onboarding = create_employee_onboarding(submit=False)

		onboarding.complete_activity(get_row(onboarding, "Assign ID Card").name)
		onboarding.reload()
		self.assertTrue(get_row(onboarding, "Assign ID Card").completed)

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

	def test_mark_onboarding_as_completed(self):
		onboarding = create_employee_onboarding(submit=False)
		self.assertEqual(onboarding.boarding_status, "Pending")

		onboarding.mark_onboarding_as_completed()

		self.assertEqual(onboarding.boarding_status, "Completed")
		self.assertTrue(all(row.completed or row.skipped for row in onboarding.activities))


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
		onboarding.employee_onboarding_template = get_test_template().name
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


def get_test_template():
	name = frappe.db.get_value("Employee Onboarding Template", {"title": "_Test Engineering Onboarding"})
	if name:
		return frappe.get_doc("Employee Onboarding Template", name)
	return make_template(
		"_Test Engineering Onboarding",
		[
			{"activity_name": "Assign ID Card", "role": "HR User", "begin_on": 0, "duration": 1},
			{"activity_name": "Assign a laptop", "role": "HR User", "begin_on": 1, "duration": 1},
		],
	)


def make_template(title, activities=None, **fields):
	template = frappe.new_doc("Employee Onboarding Template")
	template.title = title
	template.update(fields)
	for activity in activities or []:
		template.append("activities", activity)
	return template.insert()


def make_designation(name):
	if not frappe.db.exists("Designation", name):
		frappe.get_doc({"doctype": "Designation", "designation_name": name}).insert()
	return name


def make_grade(name):
	if not frappe.db.exists("Employee Grade", name):
		frappe.get_doc({"doctype": "Employee Grade", "__newname": name}).insert()
	return name
