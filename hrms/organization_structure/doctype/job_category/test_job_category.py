# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestJobCategory(IntegrationTestCase):
	def test_create_job_category(self):
		doc = create_job_category("Chief Officer")
		self.assertEqual(doc.job_category_name, "Chief Officer")


def create_job_category(job_category_name: str):
	if frappe.db.exists("Job Category", job_category_name):
		return frappe.get_doc("Job Category", job_category_name)

	return frappe.get_doc(
		{
			"doctype": "Job Category",
			"job_category_name": job_category_name,
		}
	).insert(ignore_permissions=True)
