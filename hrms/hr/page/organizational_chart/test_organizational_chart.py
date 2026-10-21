# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.page.organizational_chart.organizational_chart import get_children
from hrms.tests.test_utils import create_company
from hrms.tests.utils import HRMSTestSuite
from hrms.utils.hierarchy_chart import get_all_nodes


class TestOrganizationalChart(HRMSTestSuite):
	def setUp(self):
		self.company = create_company("Test Org Chart").name
		self.company_2 = create_company("Test Org Chart 2", abbr="TOC2").name
		frappe.db.delete("Employee", {"company": ("in", [self.company, self.company_2])})

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

	def test_reports_of_inactive_manager_attach_to_nearest_active_ancestor(self):
		emp1 = make_employee("testemp1@mail.com", company=self.company)
		emp2 = make_employee("testemp2@mail.com", company=self.company, reports_to=emp1)
		emp3 = make_employee("testemp3@mail.com", company=self.company, reports_to=emp2)
		frappe.db.set_value("Employee", emp2, "status", "Suspended")

		roots = get_children(company=self.company)
		self.assertEqual([(r.id, r.connections) for r in roots], [(emp1, 1)])
		children = get_children(parent=emp1, company=self.company)
		self.assertEqual([c.id for c in children], [emp3])

	def test_manager_in_other_company(self):
		emp1 = make_employee("testemp1@mail.com", company=self.company)
		emp2 = make_employee("testemp2@mail.com", company=self.company_2, reports_to=emp1)

		self.assertEqual([(r.id, r.connections) for r in get_children(company=self.company)], [(emp1, 0)])
		self.assertEqual([r.id for r in get_children(company=self.company_2)], [emp2])

	def test_every_employee_sees_full_tree_with_limited_fields(self):
		emp1 = make_employee("testemp1@mail.com", company=self.company)
		emp2 = make_employee("testemp2@mail.com", company=self.company, reports_to=emp1)
		emp3 = make_employee("testemp3@mail.com", company=self.company, reports_to=emp1)
		emp4 = make_employee("testemp4@mail.com", company=self.company, reports_to=emp2)

		frappe.set_user("testemp2@mail.com")
		roots = get_children(company=self.company)
		self.assertEqual([(r.id, r.connections) for r in roots], [(emp1, 3)])
		children = get_children(parent=emp1, company=self.company)
		self.assertEqual([c.id for c in children], [emp2, emp3])
		self.assertEqual([c.id for c in get_children(parent=emp2, company=self.company)], [emp4])
		self.assertEqual(
			set(children[0]), {"name", "id", "image", "title", "department", "connections", "expandable"}
		)

		frappe.set_user("Guest")
		self.assertRaises(frappe.PermissionError, get_children, company=self.company)
		frappe.set_user("Administrator")

	def test_get_all_nodes_only_runs_chart_methods(self):
		emp1 = make_employee("testemp1@mail.com", company=self.company)
		emp2 = make_employee("testemp2@mail.com", company=self.company, reports_to=emp1)

		result = get_all_nodes(
			"hrms.hr.page.organizational_chart.organizational_chart.get_children", self.company
		)
		self.assertEqual([(r["parent"], [d.id for d in r["data"]]) for r in result], [(emp1, [emp2])])
		self.assertRaises(frappe.PermissionError, get_all_nodes, "frappe.client.get_count", self.company)
