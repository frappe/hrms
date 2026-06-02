# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.page.organizational_chart.organizational_chart import get_children
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

	def test_get_children_for_all_companies(self):
		other_company = create_company("Test Org Chart Other").name
		frappe.db.delete("Employee", {"company": other_company})

		emp1 = make_employee("testemp5@mail.com", company=self.company)
		emp2 = make_employee("testemp6@mail.com", company=other_company, reports_to=emp1)
		emp3 = make_employee("testemp7@mail.com", company=self.company, reports_to=emp2)

		children = get_children(company="All Companies")
		root = next(child for child in children if child.id == emp1)
		self.assertEqual(root.connections, 2)

		children = get_children(parent=emp1, company="All Companies")
		self.assertEqual(len(children), 1)
		self.assertEqual(children[0].id, emp2)
		self.assertEqual(children[0].connections, 1)

		children = get_children(parent=emp2, company="All Companies")
		self.assertEqual(len(children), 1)
		self.assertEqual(children[0].id, emp3)

	def test_get_children_filters_connections_by_company(self):
		other_company = create_company("Test Org Chart Other").name
		frappe.db.delete("Employee", {"company": other_company})

		emp1 = make_employee("testemp8@mail.com", company=self.company)
		make_employee("testemp9@mail.com", company=other_company, reports_to=emp1)

		children = get_children(company=self.company)
		self.assertEqual(len(children), 1)
		self.assertEqual(children[0].id, emp1)
		self.assertEqual(children[0].connections, 0)
