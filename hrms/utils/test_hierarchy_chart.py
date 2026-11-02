import frappe

from hrms.tests.test_utils import create_company
from hrms.tests.utils import HRMSTestSuite
from hrms.utils.hierarchy_chart import get_all_nodes


class TestHierarchyChart(HRMSTestSuite):
	def test_get_all_nodes_rejects_other_methods(self):
		company = create_company("Test Org Chart").name
		for method in ("frappe.client.get_count", "hrms.utils.missing_module.foo"):
			self.assertRaises(frappe.PermissionError, get_all_nodes, method, company)
