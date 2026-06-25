# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


def create_job_grade(grade_level: str):
	if frappe.db.exists("Job Grade", grade_level):
		return frappe.get_doc("Job Grade", grade_level)

	return frappe.get_doc(
		{
			"doctype": "Job Grade",
			"grade_level": grade_level,
		}
	).insert(ignore_permissions=True)


class TestJobGrade(FrappeTestCase):
	def test_create(self):
		grade = create_job_grade("XI")
		self.assertEqual(grade.name, "XI")
