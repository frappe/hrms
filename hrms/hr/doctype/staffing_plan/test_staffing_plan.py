# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, get_first_day, get_last_day, getdate, nowdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.staffing_plan.staffing_plan import ParentCompanyError, SubsidiaryCompanyError
from hrms.tests.utils import HRMSTestSuite


class TestStaffingPlan(HRMSTestSuite):
	def setUp(self):
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

	def test_number_of_positions_updates_when_vacancies_decrease(self):
		# Covers the server-side invariant only: StaffingPlan.set_number_of_positions()
		# (staffing_plan.py) must always recompute number_of_positions as
		# vacancies + current_count, even when vacancies is reduced.
		#
		# NOTE: this does NOT cover the client-side bug it was written for, where
		# staffing_plan.js's `set_number_of_positions` skipped the update on the
		# desk form when the newly computed total was lower than the current
		# value (so decreasing Vacancies did not decrease Number of Positions
		# on screen until save). This repo has no JS/UI test harness for desk
		# form scripts, so that fix has to be verified manually in the browser
		# whenever hrms/hr/doctype/staffing_plan/staffing_plan.js is touched.
		frappe.get_doc({"doctype": "Designation", "designation_name": "_Test SP Designation"}).insert(
			ignore_if_duplicate=True
		)

		if frappe.db.exists("Staffing Plan", "Test Vacancy Decrease"):
			frappe.delete_doc("Staffing Plan", "Test Vacancy Decrease", force=True)

		staffing_plan = frappe.new_doc("Staffing Plan")
		staffing_plan.company = "_Test Company 10"
		staffing_plan.name = "Test Vacancy Decrease"
		staffing_plan.from_date = nowdate()
		staffing_plan.to_date = add_days(nowdate(), 10)
		staffing_plan.append(
			"staffing_details",
			{"designation": "_Test SP Designation", "vacancies": 2, "estimated_cost_per_position": 50000},
		)
		staffing_plan.insert()
		self.assertEqual(staffing_plan.staffing_details[0].number_of_positions, 2)

		# decreasing vacancies should decrease number_of_positions
		staffing_plan.staffing_details[0].vacancies = 1
		staffing_plan.save()
		self.assertEqual(staffing_plan.staffing_details[0].number_of_positions, 1)

		# increasing vacancies again should still work
		staffing_plan.staffing_details[0].vacancies = 3
		staffing_plan.save()
		self.assertEqual(staffing_plan.staffing_details[0].number_of_positions, 3)


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
