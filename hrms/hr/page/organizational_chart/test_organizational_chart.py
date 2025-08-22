# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.page.organizational_chart.organizational_chart import get_children
from hrms.tests.test_utils import create_company


class TestOrganizationalChart(IntegrationTestCase):
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
