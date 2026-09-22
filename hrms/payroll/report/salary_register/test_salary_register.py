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
PREFIXED_PF = "_Test Register PF"
CLASHING_PF = "Employer Contribution _Test Register PF"


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
		self.assertNotIn(f"employer_contribution_{frappe.scrub(EMPLOYER_PF)}", fieldnames)
		self.assertNotIn("total_employer_contribution", fieldnames)
		self.assertEqual(len(data), 1)

	def test_employer_contributions_shown_with_filter(self):
		salary_structure = self.create_structure_with_employer_contribution()
		salary_slip = self.create_salary_slip(salary_structure.name, self.end_date)

		columns, data = self.get_report(show_employer_contributions=1)

		fieldname = f"employer_contribution_{frappe.scrub(EMPLOYER_PF)}"
		fieldnames = [column["fieldname"] for column in columns]
		self.assertIn(fieldname, fieldnames)
		self.assertIn("total_employer_contribution", fieldnames)

		self.assertEqual(data[0][fieldname], 1800)
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

		deduction_fieldname = frappe.scrub(SHARED_PF)
		contribution_fieldname = f"employer_contribution_{frappe.scrub(SHARED_PF)}"
		fieldnames = [column["fieldname"] for column in columns]

		self.assertEqual(fieldnames.count(deduction_fieldname), 1)
		self.assertEqual(fieldnames.count(contribution_fieldname), 1)
		self.assertIn("total_employer_contribution", fieldnames)

		rows = {row["salary_slip_id"]: row for row in data}
		self.assertEqual(rows[deduction_slip.name][deduction_fieldname], 1800)
		self.assertEqual(rows[contribution_slip.name][contribution_fieldname], 2400)
		self.assertEqual(rows[contribution_slip.name]["total_employer_contribution"], 2400)

	def test_scrubbed_names_do_not_clash_across_parentfields(self):
		self.create_component(PREFIXED_PF, "TRPF", "Employer Contribution")
		self.create_component(CLASHING_PF, "ECTRPF", "Deduction")

		salary_structure = make_salary_structure(
			"_Test Salary Register Clash Structure",
			"Monthly",
			employee=self.employee,
			company="_Test Company",
			currency="INR",
			from_date=self.start_date,
			deductions=[{"salary_component": CLASHING_PF, "abbr": "ECTRPF", "amount": 500}],
			other_details={
				"employer_contributions": [{"salary_component": PREFIXED_PF, "abbr": "TRPF", "amount": 1800}]
			},
		)
		self.create_salary_slip(salary_structure.name, self.end_date)

		columns, data = self.get_report(show_employer_contributions=1)

		deduction_column = next(column for column in columns if column["label"] == CLASHING_PF)
		contribution_column = next(column for column in columns if column["label"] == PREFIXED_PF)

		self.assertNotEqual(deduction_column["fieldname"], contribution_column["fieldname"])
		self.assertEqual(data[0][deduction_column["fieldname"]], 500)
		self.assertEqual(data[0][contribution_column["fieldname"]], 1800)
		self.assertEqual(data[0]["total_employer_contribution"], 1800)
