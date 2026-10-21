# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
from frappe.utils import add_days, get_first_day, get_last_day, getdate, nowdate

from erpnext.setup.doctype.designation.test_designation import create_designation
from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.staffing_plan.staffing_plan import (
	ParentCompanyError,
	SubsidiaryCompanyError,
	get_designation_counts,
)
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

	def test_job_requisitions_merged_per_designation(self):
		from hrms.hr.doctype.job_requisition.test_job_requisition import make_job_requisition

		employee = make_employee("test_sp@example.com", company="_Test Company", designation="Accountant")
		first = make_job_requisition(
			requested_by=employee, designation="Accountant", no_of_positions=4, expected_compensation=100
		)
		second = frappe.copy_doc(first)
		second.no_of_positions = 2
		second.expected_compensation = 400
		second.insert()

		staffing_plan = frappe.get_doc(
			{
				"doctype": "Staffing Plan",
				"__newname": "Test JR Merge",
				"company": "_Test Company",
				"from_date": get_first_day(getdate()),
				"to_date": get_last_day(getdate()),
			}
		)
		staffing_plan.set_job_requisitions([first.name, second.name])
		staffing_plan.save()

		self.assertEqual(len(staffing_plan.staffing_details), 1)
		self.assertEqual(staffing_plan.staffing_details[0].vacancies, 6)
		self.assertEqual(staffing_plan.total_estimated_budget, 1200)

	def test_nested_subsidiary_plans_not_double_counted(self):
		make_company_tree()
		designation = create_designation(designation_name="_Test SP Nested").name

		make_plan("_Test Company 3", designation, 10)
		make_plan("_Test Company 10", designation, 5)
		make_plan("_Test SP Company C", designation, 5)
		self.assertRaises(frappe.ValidationError, make_plan, "_Test SP Company D", designation, 6)
		plan = make_plan("_Test SP Company D", designation, 5)
		self.assertEqual(plan.docstatus, 1)

	def test_subsidiary_check_includes_grandchildren(self):
		make_company_tree()
		designation = create_designation(designation_name="_Test SP Grandchild").name

		make_plan("_Test SP Company C", designation, 8)
		self.assertRaises(SubsidiaryCompanyError, make_plan, "_Test Company 3", designation, 5)

	def test_duplicate_designation_rows(self):
		designation = create_designation(designation_name="_Test SP Duplicate").name
		plan = make_plan("_Test Company 10", designation, 2, submit=False, save=False)
		plan.append("staffing_details", {"designation": designation, "vacancies": 2})
		self.assertRaises(frappe.DuplicateEntryError, plan.insert)

	def test_parent_budget_checked_on_direct_submit(self):
		designation = create_designation(designation_name="_Test SP Budget").name
		make_plan("_Test Company 3", designation, 10, cost=100)

		plan = make_plan("_Test Company 10", designation, 5, cost=1000, submit=False, save=False)
		plan.docstatus = 1
		self.assertRaises(ParentCompanyError, plan.insert)

	def test_vacancies_not_lower_than_current_openings(self):
		designation = create_designation(designation_name="_Test SP Openings").name
		frappe.get_doc(
			{
				"doctype": "Job Opening",
				"job_title": "_Test SP Openings",
				"designation": designation,
				"company": "_Test Company 10",
				"status": "Open",
			}
		).insert()

		plan = make_plan("_Test Company 10", designation, 0, submit=False, save=False)
		self.assertRaises(frappe.ValidationError, plan.insert)

	def test_designation_counts_permission(self):
		from frappe.core.doctype.user_permission.test_user_permission import create_user

		create_user("test_sp_no_role@example.com", "Employee")
		frappe.set_user("test_sp_no_role@example.com")
		try:
			self.assertRaises(frappe.PermissionError, get_designation_counts, "Designer", "_Test Company")
		finally:
			frappe.set_user("Administrator")


def make_company_tree():
	frappe.db.set_value("Company", "_Test Company 3", "is_group", 1)
	frappe.db.set_value("Company", "_Test Company 10", "is_group", 1)
	make_company("_Test SP Company C", "_TSPC", parent_company="_Test Company 10")
	make_company("_Test SP Company D", "_TSPD", parent_company="_Test Company 3")


def make_plan(company, designation, vacancies, cost=100, submit=True, save=True):
	plan = frappe.get_doc(
		{
			"doctype": "Staffing Plan",
			"__newname": f"{company}-{designation}-{vacancies}",
			"company": company,
			"from_date": nowdate(),
			"to_date": add_days(nowdate(), 10),
			"staffing_details": [
				{"designation": designation, "vacancies": vacancies, "estimated_cost_per_position": cost}
			],
		}
	)
	if save:
		plan.insert()
		if submit:
			plan.submit()
	return plan


def make_company(name=None, abbr=None, parent_company=None):
	if not name:
		name = "_Test Company 10"

	if frappe.db.exists("Company", name):
		return

	company = frappe.new_doc("Company")
	company.company_name = name
	company.abbr = abbr or "_TC10"
	company.parent_company = parent_company or "_Test Company 3"
	company.default_currency = "INR"
	company.country = "Pakistan"
	company.insert()
