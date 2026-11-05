# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe

from hrms.payroll.doctype.salary_structure.test_salary_structure import make_salary_structure
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeGrade(HRMSTestSuite):
	def test_default_salary_structure_must_be_submitted_and_active(self):
		structure = make_salary_structure(
			"Salary Structure Grade Draft", "Monthly", company="_Test Company", dont_submit=True
		)
		grade = frappe.get_doc(
			{
				"doctype": "Employee Grade",
				"__newname": "_Test Grade Draft Structure",
				"default_salary_structure": structure.name,
			}
		)
		self.assertRaises(frappe.ValidationError, grade.insert)

		structure.submit()
		grade.insert()

		structure.db_set("is_active", "No")
		grade.default_base_pay = 1000
		self.assertRaises(frappe.ValidationError, grade.save)
