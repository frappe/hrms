# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.page.organizational_chart.organizational_chart import get_children, get_people
from hrms.tests.test_utils import create_company
from hrms.tests.utils import HRMSTestSuite


class TestOrganizationalChart(HRMSTestSuite):
	def setUp(self):
		self.company = create_company("Test Org Chart").name
		frappe.db.delete("Employee", {"company": self.company})

	def test_get_children(self):
		create_company("Test Org Chart").name
		emp1 = make_employee("testemp1@mail.com", company=self.company)
		emp2 = make_employee("testemp2@mail.com", company=self.company, reports_to=emp1)
		emp3 = make_employee("testemp3@mail.com", company=self.company, reports_to=emp1)
		make_employee("testemp4@mail.com", company=self.company, reports_to=emp2)

		# root node
		children = get_children(company=self.company)
		self.assertEqual(len(children), 1)
		self.assertEqual(children[0].id, emp1)
		self.assertEqual(children[0].connections, 3)

		# root's children
		children = get_children(parent=emp1, company=self.company)
		self.assertEqual(len(children), 2)
		self.assertEqual(children[0].id, emp2)
		self.assertEqual(children[0].connections, 1)
		self.assertEqual(children[1].id, emp3)
		self.assertEqual(children[1].connections, 0)

	def approve_leave_today(self, employee):
		# an approved application covering today; the leave rules are not under test
		leave = frappe.get_doc(
			{
				"doctype": "Leave Application",
				"employee": employee,
				"company": self.company,
				"leave_type": frappe.get_all("Leave Type", pluck="name", limit=1)[0],
				"from_date": getdate(),
				"to_date": getdate(),
			}
		)
		leave.flags.ignore_validate = True
		leave.flags.ignore_mandatory = True
		leave.insert(ignore_permissions=True)
		frappe.db.set_value("Leave Application", leave.name, {"docstatus": 1, "status": "Approved"})

	def test_get_people(self):
		emp1 = make_employee("testemp1@mail.com", company=self.company)
		emp2 = make_employee("testemp2@mail.com", company=self.company, reports_to=emp1)
		emp3 = make_employee("testemp3@mail.com", company=self.company, reports_to=emp1)
		inactive = make_employee("testemp4@mail.com", company=self.company, reports_to=emp1)
		frappe.db.set_value("Employee", inactive, "status", "Left")

		self.approve_leave_today(emp3)

		people = {p.name: p for p in get_people() if p.company == self.company}

		self.assertEqual(set(people), {emp1, emp2, emp3})
		self.assertEqual(people[emp1].reports, 2)
		self.assertEqual(people[emp2].reports, 0)
		self.assertEqual(people[emp2].reports_to, emp1)
		self.assertFalse(people[emp1].on_leave_today)
		self.assertTrue(people[emp3].on_leave_today)
		self.assertEqual(people[emp3].leave_to_date, getdate())
