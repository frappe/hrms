# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils import add_days, getdate

from hrms.tests.utils import HRMSTestSuite


class TestWithholdingCycles(HRMSTestSuite):
	def test_bimonthly_cycle_boundaries(self):
		cases = (
			("2026-01-01", ("2026-01-15", "2026-01-31", "2026-02-15")),
			("2026-02-16", ("2026-02-28", "2026-03-15")),
			("2024-02-16", ("2024-02-29", "2024-03-15")),
			("2026-12-16", ("2026-12-31", "2027-01-15")),
			("2026-01-10", ("2026-01-15",)),
		)
		for start, ends in cases:
			with self.subTest(start=start):
				self.check_cycles("Bimonthly", start, ends)

	def test_other_frequency_cycles(self):
		for frequency, ends in (
			("Daily", ("2026-01-01",)),
			("Daily", ("2026-01-01", "2026-01-02")),
			("Weekly", ("2026-01-07", "2026-01-14")),
			("Fortnightly", ("2026-01-14", "2026-01-28")),
			("Monthly", ("2026-01-31", "2026-02-28")),
		):
			with self.subTest(frequency=frequency, count=len(ends)):
				self.check_cycles(frequency, "2026-01-01", ends)

	def test_negative_cycle_count(self):
		withholding = frappe.get_doc(
			{"doctype": "Salary Withholding", "from_date": "2026-01-01", "number_of_withholding_cycles": -1}
		)
		self.assertRaises(frappe.ValidationError, withholding.set_withholding_cycles_and_to_date)

	def check_cycles(self, frequency, start, ends):
		withholding = frappe.get_doc(
			{
				"doctype": "Salary Withholding",
				"payroll_frequency": frequency,
				"from_date": start,
				"number_of_withholding_cycles": len(ends),
			}
		)
		withholding.set_withholding_cycles_and_to_date()
		self.assertEqual(len(withholding.cycles), len(ends))
		self.assertEqual(withholding.to_date, getdate(ends[-1]))
		for cycle, end in zip(withholding.cycles, ends, strict=True):
			self.assertEqual(cycle.from_date, getdate(start))
			self.assertEqual(cycle.to_date, getdate(end))
			start = add_days(end, 1)
