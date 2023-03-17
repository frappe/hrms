# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase


class TestAppraisalTemplate(FrappeTestCase):
	def test_incorrect_weightage_allocation(self):
		create_kras()

		appraisal_template = frappe.new_doc("Appraisal Template")
		appraisal_template.template_title = "Engineering"
		appraisal_template.update(
			{
				"goals": [
					{
						"kra": "Quality",
						"per_weightage": 30,
					},
					{
						"kra": "Development",
						"per_weightage": 69.99,
					},
				]
			}
		)

		self.assertRaises(frappe.ValidationError, appraisal_template.insert)

		appraisal_template.goals[1].per_weightage = 70.00
		appraisal_template.insert()


def create_kras():
	for entry in ["Quality", "Development"]:
		if not frappe.db.exists("KRA", entry):
			kra = frappe.get_doc(
				{
					"doctype": "KRA",
					"title": entry,
				}
			).insert()
