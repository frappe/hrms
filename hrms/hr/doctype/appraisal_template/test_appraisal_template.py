# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestAppraisalTemplate(FrappeTestCase):
	def test_incorrect_weightage_allocation(self):
		template = create_appraisal_template()
		template.goals[1].per_weightage = 69.99

		self.assertRaises(frappe.ValidationError, template.save)

		template.reload()
		template.goals[1].per_weightage = 70.00
		template.save()


def create_kras(kras):
	for entry in kras:
		if not frappe.db.exists("KRA", entry):
			frappe.get_doc(
				{
					"doctype": "KRA",
					"title": entry,
				}
			).insert()


def create_criteria(criteria):
	for entry in criteria:
		if not frappe.db.exists("Employee Feedback Criteria", entry):
			frappe.get_doc(
				{
					"doctype": "Employee Feedback Criteria",
					"criteria": entry,
				}
			).insert()


def create_appraisal_template(title=None, kras=None, rating_criteria=None):
	name = title or "Engineering"

	if frappe.db.exists("Appraisal Template", name):
		return frappe.get_doc("Appraisal Template", name)

	if not kras:
		kras = [
			{
				"key_result_area": "Quality",
				"per_weightage": 30,
			},
			{
				"key_result_area": "Development",
				"per_weightage": 70,
			},
		]

	if not rating_criteria:
		rating_criteria = [
			{
				"criteria": "Problem Solving",
				"per_weightage": 70,
			},
			{
				"criteria": "Excellence",
				"per_weightage": 30,
			},
		]

	create_kras([entry["key_result_area"] for entry in kras])
	create_criteria([entry["criteria"] for entry in rating_criteria])

	appraisal_template = frappe.new_doc("Appraisal Template")
	appraisal_template.template_title = name
	appraisal_template.update({"goals": kras})
	appraisal_template.update({"rating_criteria": rating_criteria})
	appraisal_template.insert()

	return appraisal_template
