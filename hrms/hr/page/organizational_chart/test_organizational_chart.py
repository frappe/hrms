# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from unittest.mock import patch

import frappe
from frappe.core.doctype.user_permission.test_user_permission import create_user
from frappe.tests.classes.context_managers import freeze_time
from frappe.utils import add_days, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee
from erpnext.setup.doctype.holiday_list.test_holiday_list import make_holiday_list

from hrms.hr.doctype.holiday_list_assignment.test_holiday_list_assignment import (
	create_holiday_list_assignment,
)
from hrms.hr.page.organizational_chart.organizational_chart import (
	get_all_nodes,
	get_chart_context,
	get_children,
	get_directory,
	get_path,
	search_employees,
)
from hrms.payroll.doctype.salary_slip.test_salary_slip import make_leave_application
from hrms.tests.test_utils import create_company
from hrms.tests.utils import HRMSTestSuite


class TestOrganizationalChart(HRMSTestSuite):
	def setUp(self):
		self.company = create_company("Test Org Chart").name
		frappe.db.delete("Employee", {"company": self.company})

	def test_get_children(self):
		emp1 = make_employee("testemp1@mail.com", company=self.company)
		emp2 = make_employee("testemp2@mail.com", company=self.company, reports_to=emp1)
		emp3 = make_employee("testemp3@mail.com", company=self.company, reports_to=emp1)
		make_employee("testemp4@mail.com", company=self.company, reports_to=emp2)

		# root node, with its direct reports counted but not their reports
		children = get_children(self.company)
		self.assertEqual([child.id for child in children], [emp1])
		self.assertEqual(children[0].reports, 2)
		self.assertEqual({member["id"] for member in children[0].team}, {emp2, emp3})

		# root's children, each with their manager's details for the hover card
		children = get_children(self.company, parent=emp1)
		self.assertEqual({child.id: child.reports for child in children}, {emp2: 1, emp3: 0})
		self.assertEqual(children[0].manager.email, "testemp1@mail.com")

	@HRMSTestSuite.change_settings("HR Settings", {"show_org_chart_to_all_employees": 1})
	def test_employee_sees_whole_company(self):
		manager = make_employee("orgchart_view_manager@mail.com", company=self.company)
		employee = make_employee("orgchart_view_report@mail.com", company=self.company, reports_to=manager)
		# the user permission that limits the employee to their own Employee record
		self.assertTrue(
			frappe.db.exists(
				"User Permission",
				{"user": "orgchart_view_report@mail.com", "allow": "Employee", "for_value": employee},
			)
		)

		frappe.set_user("orgchart_view_report@mail.com")
		try:
			roots = get_children(self.company)
			team = get_children(self.company, parent=manager)
		finally:
			frappe.set_user("Administrator")

		# the chart is the company directory, so their manager is there too
		self.assertEqual([root.id for root in roots], [manager])
		self.assertEqual([member.id for member in team], [employee])
		# but only their own profile opens for them, and desk's composer sends only there
		self.assertEqual((roots[0].can_open, roots[0].can_email), (False, False))
		self.assertEqual((team[0].can_open, team[0].can_email), (True, True))

	@HRMSTestSuite.change_settings("HR Settings", {"show_org_chart_to_all_employees": 1})
	def test_manager_in_unseen_company_shows_only_who(self):
		other_company = create_company("Test Org Chart Other").name
		manager = make_employee("orgchart_unseen_manager@mail.com", company=other_company)
		employee = make_employee("orgchart_unseen_report@mail.com", company=self.company, reports_to=manager)

		# the employee's user permission gives them their own company only
		frappe.set_user("orgchart_unseen_report@mail.com")
		try:
			roots = {root.id: root for root in get_children(self.company)}
		finally:
			frappe.set_user("Administrator")

		self.assertEqual(set(roots[employee].manager), {"id", "name", "image", "company"})
		self.assertEqual(roots[employee].manager.company, other_company)

	@HRMSTestSuite.change_settings("HR Settings", {"show_org_chart_to_all_employees": 1})
	def test_chart_access(self):
		other_company = create_company("Test Org Chart Other").name
		make_employee("orgchart_access@mail.com", company=self.company)
		# limited to their own record, without the Company user permission employees usually get
		limited = make_employee(
			"orgchart_no_company_permission@mail.com", company=self.company, create_user_permission=0
		)
		frappe.permissions.add_user_permission("Employee", limited, "orgchart_no_company_permission@mail.com")
		create_user("orgchart_outsider@mail.com", "Website Manager")

		# an employee sees only their company, and a user without the page's roles none
		for user, company in (
			("orgchart_access@mail.com", other_company),
			("orgchart_no_company_permission@mail.com", other_company),
			("orgchart_outsider@mail.com", self.company),
		):
			frappe.set_user(user)
			try:
				self.assertRaises(frappe.PermissionError, get_children, company)
			finally:
				frappe.set_user("Administrator")

	@HRMSTestSuite.change_settings("HR Settings", {"show_org_chart_to_all_employees": 0})
	def test_chart_hidden_from_employees(self):
		employee = make_employee("orgchart_hidden@mail.com", company=self.company)
		create_user("orgchart_hidden_hr@mail.com", "HR User")

		# an employee gets no company, and the page says why
		frappe.set_user("orgchart_hidden@mail.com")
		try:
			context = get_chart_context()
			self.assertRaises(frappe.PermissionError, get_children, self.company)
		finally:
			frappe.set_user("Administrator")
		self.assertEqual(context["companies"], [])
		self.assertTrue(context["hidden_from_employees"])

		# HR, who may read every Employee, still sees the chart
		frappe.set_user("orgchart_hidden_hr@mail.com")
		try:
			self.assertIn(self.company, get_chart_context()["companies"])
			self.assertEqual([node.id for node in get_children(self.company)], [employee])
		finally:
			frappe.set_user("Administrator")

	def test_portal_user_has_no_access(self):
		portal_user = frappe.get_doc(
			{"doctype": "User", "email": "orgchart_portal@mail.com", "first_name": "Portal"}
		).insert()
		self.assertEqual(portal_user.user_type, "Website User")

		# even with the page's roles cleared and a company they may see
		frappe.set_user(portal_user.name)
		try:
			with (
				patch("frappe.core.doctype.page.page.Page.is_permitted", return_value=True),
				patch(
					"hrms.hr.page.organizational_chart.organizational_chart.get_allowed_companies",
					return_value=[self.company],
				),
			):
				self.assertRaises(frappe.PermissionError, get_children, self.company)
		finally:
			frappe.set_user("Administrator")

	def test_access_error_escapes_company(self):
		with self.assertRaises(frappe.PermissionError) as error:
			get_children("<b>Not a company</b>")
		self.assertNotIn("<b>Not a company</b>", str(error.exception))

	def test_expand_all_limit(self):
		make_employee("orgchart_limit1@mail.com", company=self.company)
		make_employee("orgchart_limit2@mail.com", company=self.company)
		self.assertEqual(len(get_all_nodes(self.company)), 2)

		with patch("hrms.hr.page.organizational_chart.organizational_chart.EXPAND_ALL_LIMIT", 1):
			self.assertRaises(frappe.ValidationError, get_all_nodes, self.company)

	@HRMSTestSuite.change_settings("HR Settings", {"show_org_chart_to_all_employees": 1})
	def test_get_chart_context(self):
		employee = make_employee("orgchart_context@mail.com", company=self.company)

		frappe.set_user("orgchart_context@mail.com")
		try:
			context = get_chart_context()
		finally:
			frappe.set_user("Administrator")

		# the chart opens at the user's own company, with their card to find
		self.assertEqual(context["company"], self.company)
		self.assertEqual(context["employee"], employee)

	def test_employee_with_manager_outside_chart_is_a_root(self):
		other_company = create_company("Test Org Chart Other").name
		other_company_manager = make_employee("orgchart_other_manager@mail.com", company=other_company)
		left_manager = make_employee("orgchart_left_manager@mail.com", company=self.company)
		frappe.db.set_value("Employee", left_manager, "status", "Left")

		reports_to_other_company = make_employee(
			"orgchart_other_report@mail.com", company=self.company, reports_to=other_company_manager
		)
		reports_to_left_manager = make_employee(
			"orgchart_left_report@mail.com", company=self.company, reports_to=left_manager
		)

		roots = {root.id: root for root in get_children(self.company)}
		self.assertEqual(set(roots), {reports_to_other_company, reports_to_left_manager})
		self.assertEqual(roots[reports_to_other_company].manager["company"], other_company)
		# a manager who has left shows who they were, not their email or department
		self.assertEqual(set(roots[reports_to_left_manager].manager), {"id", "name", "image", "company"})
		# each chart shows one company, so the manager's chart does not show the report
		self.assertEqual(get_children(other_company, parent=other_company_manager), [])

	@HRMSTestSuite.change_settings("HR Settings", {"show_org_chart_to_all_employees": 1})
	def test_get_directory(self):
		other_company = create_company("Test Org Chart Other").name
		make_employee("orgchart_directory_other@mail.com", company=other_company)
		with freeze_time(f"{getdate().year}-06-10"):
			today = getdate()
			manager = make_employee(
				"orgchart_directory_manager@mail.com",
				company=self.company,
				date_of_joining=add_days(today, -400),
			)
			joiner = make_employee(
				"orgchart_directory_joiner@mail.com",
				company=self.company,
				reports_to=manager,
				date_of_joining=add_days(today, -5),
			)

			frappe.set_user("orgchart_directory_joiner@mail.com")
			try:
				people = {person.id: person for person in get_directory(self.company)}
				self.assertRaises(frappe.PermissionError, get_directory, other_company)
			finally:
				frappe.set_user("Administrator")

		# the whole company, with who reports to whom and who joined recently, but not the joining date
		self.assertEqual(list(people), [manager, joiner])
		self.assertEqual(people[joiner].manager, manager)
		self.assertEqual(
			{name: person.new_joiner for name, person in people.items()}, {manager: False, joiner: True}
		)
		self.assertNotIn("date_of_joining", people[joiner])
		self.assertEqual((people[manager].can_open, people[joiner].can_open), (False, True))

	@HRMSTestSuite.change_settings(
		"HR Settings",
		{
			"show_org_chart_to_all_employees": 1,
			"send_birthday_reminders": 1,
			"send_work_anniversary_reminders": 0,
		},
	)
	def test_directory_celebrations(self):
		with freeze_time(f"{getdate().year}-06-10"):
			today = getdate()
			birthday = make_employee(
				"orgchart_birthday@mail.com", company=self.company, date_of_birth=f"{today.year - 30}-06-10"
			)
			anniversary = make_employee(
				"orgchart_anniversary@mail.com",
				company=self.company,
				date_of_joining=f"{today.year - 5}-06-10",
			)
			people = {person.id: person for person in get_directory(self.company)}
			frappe.db.set_single_value(
				"HR Settings", {"send_birthday_reminders": 0, "send_work_anniversary_reminders": 1}
			)
			later = {person.id: person.celebrating for person in get_directory(self.company)}

		# each shows only while HR Settings announces it to the company anyway, and never its date
		self.assertEqual(
			{name: person.celebrating for name, person in people.items()},
			{birthday: {"birthday": True}, anniversary: None},
		)
		self.assertEqual(later, {birthday: None, anniversary: {"years": 5}})
		self.assertNotIn("date_of_birth", people[birthday])

	def test_get_path(self):
		emp1 = make_employee("orgchart_path1@mail.com", company=self.company)
		emp2 = make_employee("orgchart_path2@mail.com", company=self.company, reports_to=emp1)
		emp3 = make_employee("orgchart_path3@mail.com", company=self.company, reports_to=emp2)

		self.assertEqual(get_path(self.company, emp3), [emp1, emp2, emp3])

	def test_search_employees(self):
		other_company = create_company("Test Org Chart Other").name
		employee = make_employee("orgchart_search@mail.com", company=self.company)
		make_employee("orgchart_search_other@mail.com", company=other_company)
		left = make_employee("orgchart_search_left@mail.com", company=self.company)
		frappe.db.set_value("Employee", left, "status", "Left")

		# only active people of the chart's company
		results = search_employees(self.company, "orgchart_search")
		self.assertEqual([result.name for result in results], [employee])

		# with nothing typed, a manager comes before their report, whose name sorts first
		report = make_employee("orgchart_a_report@mail.com", company=self.company, reports_to=employee)
		results = search_employees(self.company)
		self.assertEqual([result.name for result in results], [employee, report])

	def test_leave_status(self):
		# mid-year, so the leaves and holidays below stay in one year
		with freeze_time(f"{getdate().year}-06-10"):
			today = getdate()
			holiday_list = make_holiday_list(
				"Test Org Chart Holidays",
				from_date=add_days(today, -10),
				to_date=add_days(today, 10),
				holiday_dates=[{"holiday_date": add_days(today, 1), "description": "Test Holiday"}],
			).name
			on_leave = make_employee("orgchart_on_leave@mail.com", company=self.company)
			on_half_day = make_employee("orgchart_half_day@mail.com", company=self.company)
			for employee in (on_leave, on_half_day):
				create_holiday_list_assignment("Employee", employee, holiday_list, company=self.company)

			# back after today's leave, tomorrow's holiday and the leave on the day after
			make_leave_application(on_leave, today, today, "_Test Leave Type LWP", company=self.company)
			make_leave_application(
				on_leave, add_days(today, 2), add_days(today, 2), "_Test Leave Type LWP", company=self.company
			)
			make_leave_application(
				on_half_day,
				today,
				today,
				"_Test Leave Type LWP",
				company=self.company,
				half_day=1,
				half_day_date=today,
			)

			leave_status = {node.id: node.leave for node in get_children(self.company)}
			self.assertEqual(leave_status[on_leave], {"half_day": False, "back_on": add_days(today, 3)})
			self.assertEqual(leave_status[on_half_day], {"half_day": True, "back_on": None})
