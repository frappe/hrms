# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from unittest.mock import patch

import frappe

from hrms.tests.utils import HRMSTestSuite


class TestFractionalPaymentDays(HRMSTestSuite):
	def make_slip(self, working_days, payment_days):
		return frappe.get_doc(
			{
				"doctype": "Salary Slip",
				"salary_structure": "Test Structure",
				"total_working_days": working_days,
				"payment_days": payment_days,
			}
		)

	def test_fractional_component_payment_days(self):
		for working_days, payment_days, expected in (
			(30.5, 30.5, 1100),
			(0.5, 0.5, 1100),
			(0.5, 0.25, 550),
			(0.5, 0, 0),
		):
			with self.subTest(working_days=working_days, payment_days=payment_days):
				slip = self.make_slip(working_days, payment_days)
				row = slip.append(
					"earnings",
					{
						"salary_component": "Basic",
						"amount": 1100,
						"default_amount": 1000,
						"additional_amount": 100,
						"depends_on_payment_days": 1,
					},
				)
				amount, additional = slip.get_amount_based_on_payment_days(row)
				self.assertEqual(amount, expected)
				self.assertEqual(additional, 100 * payment_days / working_days)

	def test_fractional_statistical_component_payment_days(self):
		for days in (30.5, 0.5, 0):
			with self.subTest(days=days):
				slip = self.make_slip(days, days)
				slip.data, slip.default_data = {}, {}
				row = frappe._dict(
					salary_component="Statistical",
					abbr="STAT",
					statistical_component=1,
					depends_on_payment_days=1,
					precision=2,
				)
				with patch.object(slip, "eval_condition_and_formula", return_value=1000):
					slip.add_structure_component(row, "earnings")
				self.assertEqual(slip.data["STAT"], 1000 if days else 0)

	def test_fractional_benefit_payment_days(self):
		for days in (30.5, 0.5, 0):
			with self.subTest(days=days):
				slip = self.make_slip(days, days)
				benefit = frappe._dict(
					salary_component="Benefit", yearly_amount=12000, depends_on_payment_days=1
				)
				with (
					patch(
						"hrms.payroll.doctype.salary_slip.salary_slip.get_period_factor",
						return_value=(12, 1),
					),
					patch.object(slip, "_get_benefit_ledger_entries", return_value={"Benefit": {}}),
				):
					slip.get_current_period_employee_benefit_amounts([benefit])
				self.assertEqual(benefit.amount, 1000 if days else 0)
