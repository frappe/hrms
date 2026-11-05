# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import json
import os

import frappe
from frappe.utils import get_last_day, nowdate

from hrms.payroll.doctype.employee_benefit_claim.test_employee_benefit_claim import (
	make_benefit_ledger_entries,
	setup_employee_with_benefits,
)
from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip
from hrms.tests.utils import HRMSTestSuite


class TestEmployeeBenefitLedger(HRMSTestSuite):
	def test_accrued_benefits_paid_in_leavers_final_slip(self):
		employee, salary_structure, payroll_period = setup_employee_with_benefits(
			"test_benefit_ledger_leaver@ledger.com", relieving_date=get_last_day(nowdate())
		)
		make_benefit_ledger_entries(employee, "Internet Reimbursement", payroll_period, 1000, months=3)
		make_benefit_ledger_entries(employee, "Mediclaim Allowance", payroll_period, 2000, months=3)

		salary_slip = make_salary_slip(salary_structure.name, employee=employee, posting_date=nowdate())
		earnings = {row.salary_component: row.amount for row in salary_slip.earnings}
		accrued = [row.salary_component for row in salary_slip.accrued_benefits]

		self.assertGreater(earnings.get("Internet Reimbursement", 0), 3000)
		self.assertGreater(earnings.get("Mediclaim Allowance", 0), 6000)
		self.assertNotIn("Internet Reimbursement", accrued)
		self.assertNotIn("Mediclaim Allowance", accrued)

	def test_company_is_a_link_for_user_permissions(self):
		with open(os.path.join(os.path.dirname(__file__), "employee_benefit_ledger.json")) as f:
			field = next(df for df in json.load(f)["fields"] if df["fieldname"] == "company")
		self.assertEqual((field["fieldtype"], field.get("options")), ("Link", "Company"))
