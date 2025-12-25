# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, get_first_day, get_last_day, getdate, nowdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.staffing_plan.staffing_plan import ParentCompanyError, SubsidiaryCompanyError

test_dependencies = ["Designation"]


class TestStaffingPlan(IntegrationTestCase):
	def setUp(self):
		for doctype in ["Staffing Plan", "Staffing Plan Detail"]:
			frappe.db.delete(doctype)
		make_company()

	def test_staffing_plan(self):
		frappe.db.set_value("Company", "_Test Company 3", "is_group", 1)
		if frappe.db.exists("Staffing Plan", "Test"):
			return
		staffing_plan = frappe.new_doc("Staffing Plan")
		staffing_plan.company = "_Test Company 10"
		staffing_plan.name = "Test"
		staffing_plan.from_date = nowdate()
		staffing_plan.to_date = add_days(nowdate(), 10)
		staffing_plan.append(
			"staffing_details",
			{"designation": "Designer", "vacancies": 6, "estimated_cost_per_position": 50000},
		)
		staffing_plan.insert()
		staffing_plan.submit()
		self.assertEqual(staffing_plan.total_estimated_budget, 300000.00)

	def test_staffing_plan_subsidiary_company(self):
		self.test_staffing_plan()
		if frappe.db.exists("Staffing Plan", "Test 1"):
			return
		staffing_plan = frappe.new_doc("Staffing Plan")
		staffing_plan.company = "_Test Company 3"
		staffing_plan.name = "Test 1"
		staffing_plan.from_date = nowdate()
		staffing_plan.to_date = add_days(nowdate(), 10)
		staffing_plan.append(
			"staffing_details",
			{"designation": "Designer", "vacancies": 3, "estimated_cost_per_position": 45000},
		)
		self.assertRaises(SubsidiaryCompanyError, staffing_plan.insert)

	def test_staffing_plan_parent_company(self):
		if frappe.db.exists("Staffing Plan", "Test"):
			return
		staffing_plan = frappe.new_doc("Staffing Plan")
		staffing_plan.company = "_Test Company 3"
		staffing_plan.name = "Test"
		staffing_plan.from_date = nowdate()
		staffing_plan.to_date = add_days(nowdate(), 10)
		staffing_plan.append(
			"staffing_details",
			{"designation": "Designer", "vacancies": 7, "estimated_cost_per_position": 50000},
		)
		staffing_plan.insert()
		staffing_plan.submit()
		self.assertEqual(staffing_plan.total_estimated_budget, 350000.00)
		if frappe.db.exists("Staffing Plan", "Test 1"):
			return
		staffing_plan = frappe.new_doc("Staffing Plan")
		staffing_plan.company = "_Test Company 10"
		staffing_plan.name = "Test 1"
		staffing_plan.from_date = nowdate()
		staffing_plan.to_date = add_days(nowdate(), 10)
		staffing_plan.append(
			"staffing_details",
			{"designation": "Designer", "vacancies": 7, "estimated_cost_per_position": 60000},
		)
		staffing_plan.insert()
		self.assertRaises(ParentCompanyError, staffing_plan.submit)

	def test_staffing_details_from_job_requisition(self):
		from hrms.hr.doctype.job_requisition.test_job_requisition import make_job_requisition

		employee = make_employee("test_sp@example.com", company="_Test Company", designation="Accountant")
		requisition = make_job_requisition(requested_by=employee, designation="Accountant", no_of_positions=4)
		staffing_plan = frappe.get_doc(
			{
				"doctype": "Staffing Plan",
				"__newname": "Test JR",
				"company": "_Test Company",
				"from_date": get_first_day(getdate()),
				"to_date": get_last_day(getdate()),
			}
		)
		staffing_plan.set_job_requisitions([requisition.name])
		staffing_plan.save()
		staffing_plan_detail = frappe.db.get_values(
			"Staffing Plan Detail",
			{"parent": staffing_plan.name},
			["designation", "vacancies", "current_count", "number_of_positions"],
			as_dict=True,
		)[0]
		self.assertEqual(staffing_plan_detail.designation, "Accountant")
		self.assertEqual(staffing_plan_detail.vacancies, 4)
		self.assertEqual(staffing_plan_detail.current_count, 1)
		self.assertEqual(staffing_plan_detail.number_of_positions, 5)


def make_company(name=None, abbr=None):
	if not name:
		name = "_Test Company 10"

	if frappe.db.exists("Company", name):
		return

	company = frappe.new_doc("Company")
	company.company_name = name
	company.abbr = abbr or "_TC10"
	company.parent_company = "_Test Company 3"
	company.default_currency = "INR"
	company.country = "Pakistan"
	company.insert()
