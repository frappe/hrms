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

	def test_get_children_all_companies(self):
		"""Test that 'All Companies' returns employees from all companies"""
		company2 = create_company("Test Org Chart 2").name
		frappe.db.delete("Employee", {"company": company2})

		# Create employees in first company
		emp1 = make_employee("testallcomp1@mail.com", company=self.company)
		make_employee("testallcomp2@mail.com", company=self.company, reports_to=emp1)

		# Create employees in second company
		emp3 = make_employee("testallcomp3@mail.com", company=company2)
		make_employee("testallcomp4@mail.com", company=company2, reports_to=emp3)

		# Test "All Companies" - should return root employees from both companies
		children = get_children(company="All Companies")
		employee_ids = [child.id for child in children]
		self.assertIn(emp1, employee_ids)
		self.assertIn(emp3, employee_ids)

	def test_get_children_all_companies_hierarchy(self):
		"""Test drilling down into hierarchy with 'All Companies'"""
		# Create hierarchy
		emp1 = make_employee("testhier1@mail.com", company=self.company)
		emp2 = make_employee("testhier2@mail.com", company=self.company, reports_to=emp1)

		# Get children of emp1 with "All Companies"
		children = get_children(parent=emp1, company="All Companies")
		self.assertEqual(len(children), 1)
		self.assertEqual(children[0].id, emp2)

	def test_get_children_single_company_filter(self):
		"""Test that single company filter excludes other companies"""
		company2 = create_company("Test Org Chart 3").name
		frappe.db.delete("Employee", {"company": company2})

		emp1 = make_employee("testsingle1@mail.com", company=self.company)
		emp2 = make_employee("testsingle2@mail.com", company=company2)

		# Filter by first company - should not include emp2
		children = get_children(company=self.company)
		employee_ids = [child.id for child in children]
		self.assertIn(emp1, employee_ids)
		self.assertNotIn(emp2, employee_ids)

		# Filter by second company - should not include emp1
		children = get_children(company=company2)
		employee_ids = [child.id for child in children]
		self.assertIn(emp2, employee_ids)
		self.assertNotIn(emp1, employee_ids)
