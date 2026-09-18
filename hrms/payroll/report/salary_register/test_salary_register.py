# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import add_months, get_first_day, get_last_day, getdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from hrms.payroll.doctype.salary_structure.test_salary_structure import (
	create_salary_structure_assignment,
	make_salary_structure,
)
from hrms.payroll.report.salary_register.salary_register import execute
from hrms.tests.utils import HRMSTestSuite

EMPLOYER_PF = "_Test Register Employer PF"
SHARED_PF = "_Test Register Shared PF"


class TestSalaryRegister(HRMSTestSuite):
	def setUp(self):
		self.employee = make_employee("test_salary_register@example.com", company="_Test Company")
		self.start_date = get_first_day(add_months(getdate(), -1))
		self.end_date = get_last_day(self.start_date)

	def create_component(self, component, abbr, component_type):
		if frappe.db.exists("Salary Component", component):
			frappe.delete_doc("Salary Component", component, force=True)

		frappe.get_doc(
			{
				"doctype": "Salary Component",
				"salary_component": component,
				"salary_component_abbr": abbr,
				"type": component_type,
			}
		).insert()

	def create_salary_slip(self, salary_structure, posting_date):
		salary_slip = make_salary_slip(salary_structure, employee=self.employee, posting_date=posting_date)
		salary_slip.insert()
		salary_slip.submit()

		return salary_slip

	def get_report(self, **filters):
		return execute(
			frappe._dict(
				{
					"company": "_Test Company",
					"employee": self.employee,
					"docstatus": "Submitted",
					**filters,
				}
			)
		)

	def create_structure_with_employer_contribution(self):
		self.create_component(EMPLOYER_PF, "TREPF", "Employer Contribution")

		return make_salary_structure(
			"_Test Salary Register Structure",
			"Monthly",
			employee=self.employee,
			company="_Test Company",
			currency="INR",
			from_date=self.start_date,
			other_details={
				"employer_contributions": [{"salary_component": EMPLOYER_PF, "abbr": "TREPF", "amount": 1800}]
			},
		)

	def test_employer_contributions_hidden_by_default(self):
		salary_structure = self.create_structure_with_employer_contribution()
		self.create_salary_slip(salary_structure.name, self.end_date)

		columns, data = self.get_report()

		fieldnames = [column["fieldname"] for column in columns]
		self.assertNotIn(frappe.scrub(EMPLOYER_PF), fieldnames)
		self.assertNotIn("total_employer_contribution", fieldnames)
		self.assertEqual(len(data), 1)

	def test_employer_contributions_shown_with_filter(self):
		salary_structure = self.create_structure_with_employer_contribution()
		salary_slip = self.create_salary_slip(salary_structure.name, self.end_date)

		columns, data = self.get_report(show_employer_contributions=1)

		fieldnames = [column["fieldname"] for column in columns]
		self.assertIn(frappe.scrub(EMPLOYER_PF), fieldnames)
		self.assertIn("total_employer_contribution", fieldnames)

		self.assertEqual(data[0][frappe.scrub(EMPLOYER_PF)], 1800)
		self.assertEqual(data[0]["total_employer_contribution"], 1800)
		self.assertEqual(data[0]["net_pay"], salary_slip.net_pay)

	def test_component_shared_across_parentfields(self):
		self.create_component(SHARED_PF, "TRSPF", "Deduction")

		deduction_structure = make_salary_structure(
			"_Test Salary Register Deduction Structure",
			"Monthly",
			employee=self.employee,
			company="_Test Company",
			currency="INR",
			from_date=self.start_date,
			deductions=[{"salary_component": SHARED_PF, "abbr": "TRSPF", "amount": 1800}],
		)
		deduction_slip = self.create_salary_slip(deduction_structure.name, self.end_date)

		frappe.db.set_value("Salary Component", SHARED_PF, "type", "Employer Contribution")

		next_start_date = add_months(self.start_date, 1)
		contribution_structure = make_salary_structure(
			"_Test Salary Register Contribution Structure",
			"Monthly",
			company="_Test Company",
			currency="INR",
			other_details={
				"employer_contributions": [{"salary_component": SHARED_PF, "abbr": "TRSPF", "amount": 2400}]
			},
		)
		create_salary_structure_assignment(
			self.employee,
			contribution_structure.name,
			from_date=next_start_date,
			currency="INR",
			allow_duplicate=True,
		)
		contribution_slip = self.create_salary_slip(
			contribution_structure.name, get_last_day(next_start_date)
		)

		columns, data = self.get_report(show_employer_contributions=1)

		fieldname = frappe.scrub(SHARED_PF)
		self.assertEqual([column["fieldname"] for column in columns].count(fieldname), 1)

		amounts = {row["salary_slip_id"]: row.get(fieldname) for row in data}
		self.assertEqual(amounts[deduction_slip.name], 1800)
		self.assertEqual(amounts[contribution_slip.name], 2400)
