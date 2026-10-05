from unittest.mock import patch

import frappe
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.api.portal import check_in, get_context, get_home
from hrms.tests.utils import HRMSTestSuite


class TestPortalAPI(HRMSTestSuite):
	def setUp(self):
		for doctype in (
			"Leave Application",
			"Attendance",
			"Employee Checkin",
			"Employee Onboarding",
			"Employee Boarding Activity",
			"Appraisal",
			"Appraisal Cycle",
			"Task",
		):
			frappe.db.delete(doctype)

		self.manager = make_employee("portal_manager@example.com", company="_Test Company")
		self.report = make_employee(
			"portal_report@example.com",
			company="_Test Company",
			reports_to=self.manager,
			resignation_letter_date=None,
			final_confirmation_date=None,
		)
		self.peer = make_employee(
			"portal_peer@example.com", company="_Test Company", reports_to=self.manager, date_of_birth="1990-05-08"
		)
		frappe.get_doc("User", "portal_report@example.com").remove_roles("HR User")

	def tearDown(self):
		frappe.set_user("Administrator")

	# sidebar

	def test_nav_without_employee(self):
		context = get_context()
		self.assertIsNone(context["employee"])
		self.assertEqual(context["nav"]["todo_count"], 0)

	def test_manage_group_for_managers_and_hr(self):
		frappe.set_user("portal_manager@example.com")
		self.assertTrue(get_context()["nav"]["manages"])

		frappe.set_user("portal_report@example.com")
		nav = get_context()["nav"]
		self.assertFalse(nav["manages"])
		self.assertFalse(nav["is_hr"])

		frappe.set_user("Administrator")
		frappe.get_doc("User", "portal_report@example.com").add_roles("HR User")
		frappe.set_user("portal_report@example.com")
		self.assertTrue(get_context()["nav"]["is_hr"])

	def test_first_month_row_only_while_onboarding(self):
		onboarding = make_onboarding(self.report)

		frappe.set_user("portal_report@example.com")
		self.assertEqual(get_context()["nav"]["onboarding"], onboarding)

		frappe.set_user("Administrator")
		frappe.db.set_value("Employee Onboarding", onboarding, "boarding_status", "Completed")
		frappe.set_user("portal_report@example.com")
		self.assertIsNone(get_context()["nav"]["onboarding"])

	def test_offboarding_row_only_after_resigning(self):
		frappe.set_user("portal_report@example.com")
		self.assertFalse(get_context()["nav"]["resigned"])

		frappe.set_user("Administrator")
		frappe.db.set_value("Employee", self.report, "resignation_letter_date", getdate())
		frappe.set_user("portal_report@example.com")
		self.assertTrue(get_context()["nav"]["resigned"])

	# home: cards

	@HRMSTestSuite.change_settings("HR Settings", {"allow_employee_checkin_from_mobile_app": 0})
	def test_check_in_blocked_when_setting_is_off(self):
		frappe.set_user("portal_report@example.com")
		self.assertRaises(frappe.PermissionError, check_in, "IN")

	@HRMSTestSuite.change_settings("HR Settings", {"allow_employee_checkin_from_mobile_app": 1})
	def test_check_in_updates_shift_card(self):
		frappe.set_user("portal_report@example.com")
		self.assertIsNone(get_home()["shift"]["last_log_type"])

		check_in("IN")
		self.assertEqual(get_home()["shift"]["last_log_type"], "IN")

	def test_absent_count_this_month(self):
		insert_attendance(self.report, "Absent")
		insert_attendance(self.report, "Present")

		frappe.set_user("portal_report@example.com")
		self.assertEqual(get_home()["absent_count"], 1)

	def test_first_month_card_counts_from_onboarding_start(self):
		make_onboarding(self.report, begins_on=add_days(getdate(), -2))

		frappe.set_user("portal_report@example.com")
		# no activity has a duration, so the plan falls back to 30 days
		self.assertEqual(get_home()["first_month"], {"day": 3, "of": 30})

	# home: to do

	def test_each_request_to_approve_is_its_own_todo(self):
		insert_leave(self.report, status="Open", docstatus=0, approver="portal_manager@example.com")
		insert_leave(self.peer, status="Open", docstatus=0, approver="portal_manager@example.com")

		frappe.set_user("portal_manager@example.com")
		self.assertEqual(get_context()["nav"]["todo_count"], 2)

		todos = get_home()["todos"]
		self.assertEqual([todo["kind"] for todo in todos], ["leave_approval", "leave_approval"])
		self.assertEqual(
			{todo["person"]["name"] for todo in todos},
			{frappe.db.get_value("Employee", name, "employee_name") for name in (self.report, self.peer)},
		)

	def test_self_appraisal_todo_only_while_cycle_in_progress(self):
		cycle = make_appraisal_cycle()
		insert_appraisal(self.report, cycle)

		frappe.set_user("portal_report@example.com")
		self.assertEqual([todo["kind"] for todo in get_home()["todos"]], ["self_appraisal"])

		frappe.set_user("Administrator")
		frappe.db.set_value("Appraisal Cycle", cycle, "status", "Completed")
		frappe.set_user("portal_report@example.com")
		self.assertEqual(get_home()["todos"], [])

	def test_onboarding_tasks_are_todos_for_their_assignee(self):
		make_onboarding(self.report, activity_user="portal_report@example.com")

		frappe.set_user("portal_report@example.com")
		todos = get_home()["todos"]
		self.assertEqual([todo["kind"] for todo in todos], ["onboarding"])
		self.assertEqual(todos[0]["title"], "Read the leave policy")

	# home: upcoming and around the company

	def test_upcoming_shows_open_leave_and_probation_end(self):
		insert_leave(self.report, status="Open", docstatus=0)
		frappe.db.set_value("Employee", self.report, "final_confirmation_date", add_days(getdate(), 1))

		frappe.set_user("portal_report@example.com")
		upcoming = get_home()["upcoming"]

		leave = next(row for row in upcoming if row["kind"] == "leave")
		self.assertFalse(leave["approved"])
		self.assertIn("probation", [row["kind"] for row in upcoming])

	def test_out_today_shows_department_only_when_hr_settings_allow(self):
		insert_leave(self.peer, status="Approved", docstatus=1)
		peer_name = frappe.db.get_value("Employee", self.peer, "employee_name")

		frappe.set_user("portal_report@example.com")
		with self.change_settings("HR Settings", {"show_leaves_of_all_department_members_in_calendar": 0}):
			# the employee can't read a colleague's leave application
			self.assertEqual(get_home()["out_today"], [])

		with self.change_settings("HR Settings", {"show_leaves_of_all_department_members_in_calendar": 1}):
			out_today = get_home()["out_today"]
			self.assertEqual([row["employee_name"] for row in out_today], [peer_name])
			self.assertEqual(set(out_today[0]), {"employee_name", "image", "back_on"})

	# every test employee is born on 8 May, so don't let the limit hide the one we check
	@patch("hrms.api.portal.EVENTS_LIMIT", 1000)
	def test_birthdays_show_only_when_reminders_are_on(self):
		# 1992 is a leap year, so this also works on 29 February
		frappe.db.set_value("Employee", self.peer, "date_of_birth", getdate().replace(year=1992))
		peer_name = frappe.db.get_value("Employee", self.peer, "employee_name")
		frappe.set_user("portal_report@example.com")

		with self.change_settings("HR Settings", {"send_birthday_reminders": 0}):
			self.assertNotIn(peer_name, [event["employee_name"] for event in get_home()["events"]])

		with self.change_settings("HR Settings", {"send_birthday_reminders": 1}):
			event = next(event for event in get_home()["events"] if event["employee_name"] == peer_name)
			self.assertEqual(event, {"employee_name": peer_name, "image": None, "kind": "birthday"})


def make_onboarding(employee, begins_on=None, activity_user=None):
	activities = []
	if activity_user:
		activities.append({"activity_name": "Read the leave policy", "user": activity_user})

	onboarding = frappe.get_doc(
		{
			"doctype": "Employee Onboarding",
			"employee": employee,
			"employee_name": frappe.db.get_value("Employee", employee, "employee_name"),
			"company": "_Test Company",
			"date_of_joining": getdate(),
			"boarding_begins_on": begins_on or getdate(),
			"boarding_status": "Pending",
			"activities": activities,
		}
	)
	# a real onboarding starts from a Job Offer, which these tests don't need
	onboarding.flags.ignore_mandatory = True
	onboarding.insert(ignore_permissions=True)

	for row in onboarding.activities:
		task = frappe.get_doc({"doctype": "Task", "subject": row.activity_name}).insert()
		row.db_set("task", task.name)
	return onboarding.name


def make_appraisal_cycle():
	cycle = frappe.get_doc(
		{
			"doctype": "Appraisal Cycle",
			"cycle_name": "_Test Portal Cycle",
			"company": "_Test Company",
			"start_date": add_days(getdate(), -30),
			"end_date": add_days(getdate(), 30),
		}
	).insert()
	cycle.db_set("status", "In Progress")
	return cycle.name


def insert_appraisal(employee, cycle):
	"""Inserts without template validation, for tests that only read appraisals."""
	appraisal = frappe.get_doc(
		{
			"doctype": "Appraisal",
			"employee": employee,
			"employee_name": frappe.db.get_value("Employee", employee, "employee_name"),
			"company": "_Test Company",
			"appraisal_cycle": cycle,
			"docstatus": 0,
		}
	)
	appraisal.set_new_name()
	appraisal.db_insert()


def insert_attendance(employee, status):
	attendance = frappe.get_doc(
		{
			"doctype": "Attendance",
			"employee": employee,
			"company": "_Test Company",
			"attendance_date": getdate(),
			"status": status,
			"docstatus": 1,
		}
	)
	attendance.set_new_name()
	attendance.db_insert()


def insert_leave(employee, status, docstatus, approver=None):
	"""Inserts without allocation checks, for tests that only read leave."""
	leave = frappe.get_doc(
		{
			"doctype": "Leave Application",
			"employee": employee,
			"employee_name": frappe.db.get_value("Employee", employee, "employee_name"),
			"department": frappe.db.get_value("Employee", employee, "department"),
			"company": "_Test Company",
			"leave_type": "_Test Leave Type",
			"from_date": getdate(),
			"to_date": add_days(getdate(), 1),
			"posting_date": getdate(),
			"status": status,
			"docstatus": docstatus,
			"leave_approver": approver,
		}
	)
	leave.set_new_name()
	leave.db_insert()
	if approver:
		# as Leave Application does on save
		frappe.share.add_docshare(
			"Leave Application", leave.name, approver, submit=1, flags={"ignore_share_permission": True}
		)
	return leave.name
