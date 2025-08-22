# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.appraisal_template.test_appraisal_template import create_appraisal_template
from hrms.tests.test_utils import create_company


class TestAppraisalCycle(IntegrationTestCase):
	def setUp(self):
		company = create_company("_Test Appraisal").name
		self.template = create_appraisal_template()

		engineer = create_designation(designation_name="Engineer")
		engineer.appraisal_template = self.template.name
		engineer.save()

		create_designation(designation_name="Consultant")

		self.employee1 = make_employee("employee1@example.com", company=company, designation="Engineer")
		self.employee2 = make_employee("employee2@example.com", company=company, designation="Consultant")

	def test_set_employees(self):
		cycle = create_appraisal_cycle(designation="Engineer")

		self.assertEqual(len(cycle.appraisees), 1)
		self.assertEqual(cycle.appraisees[0].employee, self.employee1)

	def test_create_appraisals(self):
		cycle = create_appraisal_cycle(designation="Engineer")
		cycle.create_appraisals()

		appraisals = frappe.db.get_all("Appraisal", filters={"appraisal_cycle": cycle.name})
		self.assertEqual(len(appraisals), 1)

		appraisal = frappe.get_doc("Appraisal", appraisals[0].name)

		for i in range(2):
			# check if KRAs are set
			self.assertEqual(appraisal.appraisal_kra[i].kra, self.template.goals[i].key_result_area)
			self.assertEqual(appraisal.appraisal_kra[i].per_weightage, self.template.goals[i].per_weightage)

			# check if rating criteria is set
			self.assertEqual(appraisal.self_ratings[i].criteria, self.template.rating_criteria[i].criteria)
			self.assertEqual(
				appraisal.self_ratings[i].per_weightage, self.template.rating_criteria[i].per_weightage
			)


def create_appraisal_cycle(**args):
	args = frappe._dict(args)

	name = args.name or "Q1"
	if frappe.db.exists("Appraisal Cycle", name):
		frappe.delete_doc("Appraisal Cycle", name, force=True)

	appraisal_cycle = frappe.get_doc(
		{
			"doctype": "Appraisal Cycle",
			"cycle_name": name,
			"company": args.company or "_Test Appraisal",
			"start_date": args.start_date or "2022-01-01",
			"end_date": args.end_date or "2022-03-31",
		}
	)

	if args.kra_evaluation_method:
		appraisal_cycle.kra_evaluation_method = args.kra_evaluation_method

	filters = {}
	for filter_by in ["department", "designation", "branch"]:
		if args.get(filter_by):
			filters[filter_by] = args.get(filter_by)

	appraisal_cycle.update(filters)
	appraisal_cycle.set_employees()
	appraisal_cycle.insert()

	return appraisal_cycle
