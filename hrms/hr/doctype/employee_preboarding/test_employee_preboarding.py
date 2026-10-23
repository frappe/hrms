# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.desk.form.linked_with import get_linked_docs_to_delete
from frappe.utils import add_days, getdate

from hrms.hr.doctype.employee_boarding_template.employee_boarding_template import (
	get_standard_activities,
)
from hrms.hr.doctype.employee_preboarding.employee_preboarding import make_employee, split_full_name
from hrms.hr.doctype.employee_preboarding.preboarding_activities import (
	STANDARD_ACTIVITIES,
	get_template_activities,
)
from hrms.hr.doctype.job_offer.job_offer import make_employee_preboarding
from hrms.hr.doctype.job_offer.test_job_offer import create_job_offer
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
from hrms.tests.utils import HRMSTestSuite


class TestEmployeePreboarding(HRMSTestSuite):
	def test_split_full_name(self):
		self.assertEqual(split_full_name("Asha"), ("Asha", "", ""))
		self.assertEqual(split_full_name("Asha Rao"), ("Asha", "", "Rao"))
		self.assertEqual(split_full_name("Asha Bhanu Rao"), ("Asha", "Bhanu", "Rao"))
		self.assertEqual(split_full_name("Asha Bhanu Devi Rao"), ("Asha", "Bhanu", "Devi Rao"))
		self.assertEqual(split_full_name(""), ("", "", ""))

	def test_offer_maps_onto_preboarding(self):
		job_offer = get_job_offer(get_job_applicant().name)
		preboarding = make_employee_preboarding(job_offer.name)

		self.assertEqual(preboarding.job_offer, job_offer.name)
		self.assertEqual(preboarding.employee_name, job_offer.applicant_name)
		self.assertEqual(preboarding.company, job_offer.company)
		self.assertEqual(preboarding.date_of_joining, job_offer.date_of_joining)
		self.assertEqual(preboarding.boarding_begins_on, job_offer.date_of_joining)

	def test_no_project_or_task_is_created(self):
		preboarding = create_employee_preboarding(submit=False)

		self.assertFalse(preboarding.project)
		self.assertFalse(frappe.db.exists("Project", {"project_name": ("like", "%Employee Preboarding%")}))
		self.assertFalse([row.task for row in preboarding.activities if row.task])

	def test_template_rows_become_the_checklist(self):
		preboarding = create_employee_preboarding(submit=False)

		names = [row.activity_name for row in preboarding.activities]
		standard = [activity["activity_name"] for activity in STANDARD_ACTIVITIES]
		self.assertEqual(names, [*standard, "Assign ID Card", "Assign a laptop"])
		self.assertFalse(
			[row for row in preboarding.activities if row.completed or row.skipped or row.status]
		)
		self.assertEqual(get_row(preboarding, "Assign Leave Policy").action, "Assign")
		self.assertEqual(
			get_row(preboarding, "Assign Leave Policy").reference_doctype, "Leave Policy Assignment"
		)
		self.assertEqual(get_row(preboarding, "Assign Leave Policy").depends_on_action, "Create Employee")
		self.assertEqual(get_row(preboarding, "Assign ID Card").action, "Manual")

	def test_resaving_keeps_the_rows_without_duplicates(self):
		preboarding = create_employee_preboarding(submit=False)
		preboarding.save()

		names = [row.activity_name for row in preboarding.activities]
		self.assertEqual(len(names), len(set(names)))

	def test_due_date_defaults_to_the_offset_from_preboarding_start(self):
		preboarding = create_employee_preboarding(submit=False)

		self.assertEqual(getdate(get_row(preboarding, "Create Portal Login").due_date), getdate())
		self.assertEqual(getdate(get_row(preboarding, "Assign a laptop").due_date), add_days(getdate(), 1))

	def test_new_template_starts_with_the_standard_activities_once(self):
		template = make_template("_Test Fresh Template", [{"activity_name": "Order a desk"}])

		standard = [activity["activity_name"] for activity in STANDARD_ACTIVITIES]
		self.assertEqual(
			[row.activity_name for row in template.preboarding_activities], [*standard, "Order a desk"]
		)

		template.preboarding_activities = [
			row for row in template.preboarding_activities if row.action != "Appointment Letter"
		]
		template.save()
		self.assertNotIn(
			"Send Appointment Letter", [row.activity_name for row in template.preboarding_activities]
		)

	def test_template_prefilled_by_the_form_keeps_one_of_each_standard_activity(self):
		template = make_template("_Test Prefilled Template", get_standard_activities())

		standard = [activity["activity_name"] for activity in STANDARD_ACTIVITIES]
		self.assertEqual([row.activity_name for row in template.preboarding_activities], standard)

	def test_a_preboarding_without_a_template_gets_no_activities(self):
		self.assertEqual(get_template_activities(None), [])

	def test_template_rejects_a_duplicate_action(self):
		template = make_template("_Test Duplicate Template")
		template.append(
			"preboarding_activities",
			{
				"activity_name": "Assign Leave Policy again",
				"action": "Assign",
				"reference_doctype": "Leave Policy Assignment",
			},
		)

		with self.assertRaises(frappe.ValidationError):
			template.save()

	def test_new_preboarding_uses_the_newest_matching_template(self):
		make_template("_Test Older Engineer Template", designation="Engineer")
		newest = make_template(
			"_Test Newer Engineer Template", [{"activity_name": "Book a desk"}], designation="Engineer"
		)
		make_template(
			"_Test Other Designation Template", designation=make_designation("_Test Designation Elsewhere")
		)

		preboarding = create_employee_preboarding(submit=False, with_activities=False)

		self.assertEqual(preboarding.employee_boarding_template, newest.name)
		self.assertIn("Book a desk", [row.activity_name for row in preboarding.activities])

	def test_a_blank_template_applies_to_every_preboarding(self):
		blank = make_template("_Test Blank Template")

		preboarding = create_employee_preboarding(submit=False, with_activities=False)

		self.assertEqual(preboarding.employee_boarding_template, blank.name)

	def test_a_template_set_for_another_value_is_never_picked(self):
		make_template("_Test Blank Fallback Template")
		other = make_template("_Test Other Grade Template", employee_grade=make_grade("_Test Other Grade"))

		preboarding = create_employee_preboarding(submit=False, with_activities=False)

		self.assertNotEqual(preboarding.employee_boarding_template, other.name)

	def test_a_template_without_preboarding_activities_is_never_picked(self):
		blank = make_template("_Test Blank Preboarding Template")
		offboarding_only = frappe.new_doc("Employee Boarding Template")
		offboarding_only.title = "_Test Offboarding Only Template"
		offboarding_only.append("offboarding_activities", {"activity_name": "Collect the laptop"})
		offboarding_only.flags.skip_standard_activities = True
		offboarding_only.insert()

		preboarding = create_employee_preboarding(submit=False, with_activities=False)

		self.assertEqual(preboarding.employee_boarding_template, blank.name)

	def test_onboarding_and_offboarding_activities_are_manual(self):
		template = make_template("_Test Phase Template")
		template.append("onboarding_activities", {"activity_name": "Team lunch", "action": "Create User"})
		template.append(
			"offboarding_activities",
			{"activity_name": "Revoke access", "action": "Assign", "reference_doctype": "Shift Assignment"},
		)
		template.save()

		for row in template.onboarding_activities + template.offboarding_activities:
			self.assertEqual((row.action, row.reference_doctype), ("Manual", None))

	def test_hint_shows_until_the_template_has_own_tasks(self):
		template = make_template("_Test Hint Template")
		preboarding = create_employee_preboarding(submit=False, with_activities=False)
		self.assertEqual(preboarding.get_template_hint(), template.name)

		template.append("preboarding_activities", {"activity_name": "Welcome lunch"})
		template.save()
		self.assertIsNone(preboarding.get_template_hint())

	def test_offer_defaults_come_from_the_job_offer(self):
		preboarding = create_employee_preboarding(submit=False)
		offer_holiday_list = frappe.db.get_value("Job Offer", preboarding.job_offer, "holiday_list")

		defaults = preboarding.get_offer_defaults()
		self.assertEqual(
			defaults["Holiday List Assignment"], {"fieldname": "holiday_list", "value": offer_holiday_list}
		)
		self.assertNotIn("Shift Assignment", defaults)

	def test_boarding_status_tracks_progress(self):
		preboarding = create_employee_preboarding(with_activities=False)
		self.assertEqual(preboarding.boarding_status, "Pending")

		preboarding.db_set("company_email", "asha.status@example.com")
		preboarding.reload()
		preboarding.create_user()
		preboarding.reload()
		self.assertEqual(preboarding.boarding_status, "In Process")
		self.assertTrue(next(row for row in preboarding.activities if row.action == "Create User").completed)

	def test_deleting_the_user_keeps_the_preboarding_and_reopens_create_user(self):
		preboarding = create_employee_preboarding(submit=False)
		preboarding.db_set("company_email", "asha.unlink@example.com")
		preboarding.reload()
		user = preboarding.create_user()
		preboarding.reload()
		self.assertTrue(get_row(preboarding, "Create Portal Login").completed)
		blockers = get_linked_docs_to_delete("User", user)["docs"]
		self.assertNotIn("Employee Preboarding", [doc["doctype"] for doc in blockers])

		frappe.delete_doc("User", user)

		preboarding.reload()
		self.assertFalse(frappe.db.exists("User", user))
		self.assertIsNone(preboarding.user)
		self.assertFalse(get_row(preboarding, "Create Portal Login").completed)

	def test_renaming_the_user_keeps_the_preboarding_on_it(self):
		preboarding = create_employee_preboarding(submit=False)
		preboarding.db_set("company_email", "asha.rename@example.com")
		preboarding.reload()
		user = preboarding.create_user()

		frappe.rename_doc("User", user, "asha.renamed@example.com", force=True)

		preboarding.reload()
		self.assertEqual(preboarding.user, "asha.renamed@example.com")
		self.assertTrue(get_row(preboarding, "Create Portal Login").completed)

	def test_create_user_uses_the_selected_email(self):
		preboarding = create_employee_preboarding(submit=False)
		preboarding.db_set("company_email", "asha.company@example.com")
		preboarding.db_set("personal_email", "asha.personal@example.com")
		preboarding.db_set("create_user_for", "Personal Email")
		preboarding.reload()

		user = preboarding.create_user()

		self.assertEqual(user, "asha.personal@example.com")
		self.assertEqual(preboarding.user, user)
		self.assertEqual(frappe.db.get_value("User", user, "first_name"), "Test")

	def test_self_service_role_is_granted_with_the_employee(self):
		preboarding = create_employee_preboarding(submit=False)
		preboarding.db_set("company_email", "asha.ess@example.com")
		preboarding.db_set("create_user_for", "Company Email")
		preboarding.db_set("gender", "Female")
		preboarding.db_set("date_of_birth", "1990-05-08")
		preboarding.reload()

		user = preboarding.create_user()
		self.assertNotIn("Employee Self Service", frappe.get_roles(user))

		preboarding.reload()
		create_preboarding_employee(preboarding)

		frappe.clear_cache(user=user)
		self.assertIn("Employee Self Service", frappe.get_roles(user))

	def test_submitting_completes_the_remaining_steps(self):
		preboarding = create_employee_preboarding(submit=False)
		self.assertEqual(preboarding.boarding_status, "Pending")

		preboarding.submit()

		self.assertEqual(preboarding.boarding_status, "Completed")
		self.assertTrue(get_row(preboarding, "Assign ID Card").completed)
		self.assertTrue(get_row(preboarding, "Create Employee").skipped)

	def test_employee_is_created_from_the_preboarding(self):
		preboarding = create_employee_preboarding(submit=False)
		preboarding.db_set("gender", "Female")
		preboarding.db_set("date_of_birth", "1990-05-08")
		preboarding.reload()

		employee = make_employee(preboarding.name)
		employee.insert()

		self.assertEqual(employee.employee_name, "Test Engineer")
		self.assertEqual(employee.first_name, "Test")
		self.assertEqual(employee.last_name, "Engineer")
		self.assertEqual(employee.job_offer, preboarding.job_offer)

	def test_linking_an_employee_from_another_job_offer_is_blocked(self):
		preboarding = create_employee_preboarding(submit=False)
		preboarding.db_set("gender", "Female")
		preboarding.db_set("date_of_birth", "1990-05-08")
		preboarding.reload()
		employee = make_employee(preboarding.name)
		employee.job_offer = None
		employee.insert()

		self.assertRaises(frappe.ValidationError, preboarding.link_employee, employee.name)
		self.assertIsNone(frappe.db.get_value("Employee Preboarding", preboarding.name, "employee"))

	def test_activity_added_on_the_preboarding_is_a_flagged_manual_row(self):
		preboarding = create_employee_preboarding(submit=False)
		preboarding.add_activity("Order a desk")

		preboarding.reload()
		row = get_row(preboarding, "Order a desk")
		self.assertEqual((row.action, row.added_on_preboarding), ("Manual", 1))
		self.assertEqual(getdate(row.due_date), getdate(preboarding.boarding_begins_on))

	def test_only_activities_added_on_the_preboarding_can_be_removed(self):
		preboarding = create_employee_preboarding(submit=False)
		preboarding.add_activity("Order a desk")
		preboarding.reload()

		preboarding.remove_activity(get_row(preboarding, "Order a desk").name)
		preboarding.reload()
		self.assertNotIn("Order a desk", [row.activity_name for row in preboarding.activities])
		self.assertEqual(
			[row.idx for row in preboarding.activities], list(range(1, len(preboarding.activities) + 1))
		)

		template_row = get_row(preboarding, "Assign ID Card")
		self.assertRaises(frappe.ValidationError, preboarding.remove_activity, template_row.name)

	def test_activities_cannot_be_added_to_a_submitted_preboarding(self):
		preboarding = create_employee_preboarding(submit=True)

		self.assertRaises(frappe.ValidationError, preboarding.add_activity, "Order a desk")

	def test_assignment_row_ticks_from_the_real_assignment(self):
		preboarding = create_employee_preboarding(submit=False)
		preboarding.db_set("gender", "Female")
		preboarding.db_set("date_of_birth", "1990-05-08")
		preboarding.reload()
		employee = create_preboarding_employee(preboarding)

		preboarding.reload()
		self.assertTrue(get_row(preboarding, "Create Employee").completed)
		self.assertFalse(get_row(preboarding, "Assign Holiday List").completed)

		assignment = frappe.get_doc(
			{
				"doctype": "Holiday List Assignment",
				"applicable_for": "Employee",
				"assigned_to": employee,
				"employee_company": preboarding.company,
				"holiday_list": get_boarding_holiday_list(),
				"from_date": getdate(),
			}
		).insert()
		assignment.submit()

		preboarding.reload()
		preboarding.sync_activities()
		preboarding.reload()

		row = get_row(preboarding, "Assign Holiday List")
		self.assertTrue(row.completed)
		self.assertEqual(row.reference_name, assignment.name)

	def test_company_holiday_list_prefers_the_company_assignment(self):
		preboarding = create_employee_preboarding(submit=False)

		company_list = frappe.copy_doc(frappe.get_doc("Holiday List", get_boarding_holiday_list()))
		company_list.holiday_list_name = "_Test Company Wide Holidays"
		company_list.insert()

		assignment = frappe.get_doc(
			{
				"doctype": "Holiday List Assignment",
				"applicable_for": "Company",
				"assigned_to": preboarding.company,
				"holiday_list": company_list.name,
				"from_date": add_days(getdate(), 1),
			}
		).insert()
		assignment.submit()

		self.assertEqual(preboarding.get_company_holiday_list(), company_list.name)

	def test_skipping_an_activity_marks_it_skipped(self):
		preboarding = create_employee_preboarding(submit=False)

		preboarding.skip_activity(get_row(preboarding, "Assign Shift Type").name)
		preboarding.reload()

		self.assertTrue(get_row(preboarding, "Assign Shift Type").skipped)

	def test_progress_status_is_set_by_hand_and_survives_a_resave(self):
		preboarding = create_employee_preboarding(submit=False)
		row = get_row(preboarding, "Create Employee")

		preboarding.set_activity_progress(row.name, "Stuck")
		preboarding.reload()
		self.assertEqual(get_row(preboarding, "Create Employee").status, "Stuck")
		self.assertEqual(preboarding.boarding_status, "In Process")

		preboarding.save()
		self.assertEqual(get_row(preboarding, "Create Employee").status, "Stuck")

	def test_progress_status_clears_by_hand_and_when_the_activity_finishes(self):
		preboarding = create_employee_preboarding(submit=False)
		stuck, manual = get_row(preboarding, "Create Employee"), get_row(preboarding, "Assign ID Card")

		preboarding.set_activity_progress(stuck.name, "Stuck")
		preboarding.set_activity_progress(stuck.name, None)
		preboarding.set_activity_progress(manual.name, "In Progress")
		preboarding.complete_activity(manual.name)
		preboarding.reload()

		self.assertFalse(get_row(preboarding, "Create Employee").status)
		self.assertFalse(get_row(preboarding, "Assign ID Card").status)
		self.assertTrue(get_row(preboarding, "Assign ID Card").completed)

	def test_progress_status_cannot_finish_or_reopen_an_activity(self):
		preboarding = create_employee_preboarding(submit=False)
		row = get_row(preboarding, "Assign Shift Type")

		with self.assertRaises(frappe.ValidationError):
			preboarding.set_activity_progress(row.name, "Completed")

		preboarding.skip_activity(row.name)
		preboarding.reload()
		with self.assertRaises(frappe.ValidationError):
			preboarding.set_activity_progress(row.name, "In Progress")

	def test_undoing_a_skip_reopens_the_activity(self):
		preboarding = create_employee_preboarding(submit=False)
		row = get_row(preboarding, "Assign Shift Type")

		preboarding.skip_activity(row.name)
		preboarding.unskip_activity(row.name)
		preboarding.reload()

		self.assertFalse(get_row(preboarding, "Assign Shift Type").skipped)
		self.assertFalse(get_row(preboarding, "Assign Shift Type").completed)

	def test_only_manual_activities_are_completed_by_hand(self):
		preboarding = create_employee_preboarding(submit=False)

		preboarding.complete_activity(get_row(preboarding, "Assign ID Card").name)
		preboarding.reload()
		self.assertTrue(get_row(preboarding, "Assign ID Card").completed)

		with self.assertRaises(frappe.ValidationError):
			preboarding.complete_activity(get_row(preboarding, "Create Employee").name)

	def test_assigning_an_activity_gives_the_user_a_todo_of_their_own(self):
		preboarding = create_employee_preboarding(submit=False)
		first, second = (
			get_test_user("preboarding_first@example.com"),
			get_test_user("preboarding_second@example.com"),
		)
		row = get_row(preboarding, "Create Employee")

		preboarding.assign_activity(row.name, first)
		preboarding.reload()
		first_todo = get_row(preboarding, "Create Employee").todo
		self.assertEqual(frappe.db.get_value("ToDo", first_todo, ["allocated_to", "status"]), (first, "Open"))

		preboarding.assign_activity(row.name, second)
		preboarding.reload()
		second_todo = get_row(preboarding, "Create Employee").todo
		self.assertNotEqual(first_todo, second_todo)
		self.assertEqual(frappe.db.get_value("ToDo", first_todo, "status"), "Cancelled")
		self.assertEqual(frappe.db.get_value("ToDo", second_todo, "allocated_to"), second)

	def test_due_date_change_reaches_the_todo(self):
		preboarding = create_employee_preboarding(submit=False)
		row = get_row(preboarding, "Create Portal Login")
		preboarding.assign_activity(row.name, get_test_user("preboarding_due@example.com"))

		due_date = add_days(getdate(), 5)
		preboarding.set_activity_due_date(row.name, str(due_date))
		preboarding.reload()

		row = get_row(preboarding, "Create Portal Login")
		self.assertEqual(getdate(row.due_date), due_date)
		self.assertEqual(getdate(frappe.db.get_value("ToDo", row.todo, "date")), due_date)

	def test_finishing_an_activity_closes_its_todo(self):
		preboarding = create_employee_preboarding(submit=False)
		row = get_row(preboarding, "Assign ID Card")
		preboarding.assign_activity(row.name, get_test_user("preboarding_close@example.com"))
		preboarding.reload()
		todo = get_row(preboarding, "Assign ID Card").todo

		preboarding.complete_activity(row.name)

		self.assertEqual(frappe.db.get_value("ToDo", todo, "status"), "Closed")

	def test_mark_preboarding_as_completed(self):
		preboarding = create_employee_preboarding(submit=False)
		self.assertEqual(preboarding.boarding_status, "Pending")

		preboarding.mark_preboarding_as_completed()

		self.assertEqual(preboarding.boarding_status, "Completed")
		self.assertTrue(all(row.completed or row.skipped for row in preboarding.activities))


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


def create_employee_preboarding(submit=False, with_activities=True):
	applicant = get_job_applicant()
	job_offer = get_job_offer(applicant.name)

	preboarding = frappe.new_doc("Employee Preboarding")
	preboarding.job_applicant = applicant.name
	preboarding.job_offer = job_offer.name
	preboarding.date_of_joining = preboarding.boarding_begins_on = getdate()
	preboarding.company = "_Test Company"
	preboarding.holiday_list = get_boarding_holiday_list()
	preboarding.designation = "Engineer"
	preboarding.employee_name = applicant.applicant_name
	if with_activities:
		preboarding.employee_boarding_template = get_test_template().name
	preboarding.insert()
	if submit:
		preboarding.submit()

	return preboarding


def create_preboarding_employee(preboarding):
	employee = make_employee(preboarding.name).insert()
	preboarding.link_employee(employee.name)
	return employee.name


def get_row(preboarding, activity_name):
	return next(row for row in preboarding.activities if row.activity_name == activity_name)


def get_test_user(email):
	if not frappe.db.exists("User", email):
		frappe.get_doc({"doctype": "User", "email": email, "first_name": email.split("@")[0]}).insert(
			ignore_permissions=True
		)
	return email


def get_test_template():
	name = frappe.db.get_value("Employee Boarding Template", {"title": "_Test Engineering Preboarding"})
	if name:
		return frappe.get_doc("Employee Boarding Template", name)
	return make_template(
		"_Test Engineering Preboarding",
		[
			{"activity_name": "Assign ID Card", "role": "HR User", "begin_on": 0, "duration": 1},
			{"activity_name": "Assign a laptop", "role": "HR User", "begin_on": 1, "duration": 1},
		],
	)


def make_template(title, activities=None, **fields):
	template = frappe.new_doc("Employee Boarding Template")
	template.title = title
	template.update(fields)
	for activity in activities or []:
		template.append("preboarding_activities", activity)
	return template.insert()


def make_designation(name):
	if not frappe.db.exists("Designation", name):
		frappe.get_doc({"doctype": "Designation", "designation_name": name}).insert()
	return name


def make_grade(name):
	if not frappe.db.exists("Employee Grade", name):
		frappe.get_doc({"doctype": "Employee Grade", "__newname": name}).insert()
	return name
