# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from unittest.mock import patch

import frappe
from frappe.utils import getdate

from hrms.tests.utils import HRMSTestSuite


class TestFormulaPeriods(HRMSTestSuite):
	def test_future_formula_dates(self):
		cases = (
			("Daily", "2026-02-28", "2026-02-28", 1, "2026-03-01", "2026-03-01"),
			("Weekly", "2026-02-23", "2026-03-01", 2, "2026-03-09", "2026-03-15"),
			("Fortnightly", "2026-02-16", "2026-03-01", 2, "2026-03-16", "2026-03-29"),
			("Bimonthly", "2026-02-01", "2026-02-15", 1, "2026-02-16", "2026-02-28"),
			("Bimonthly", "2026-02-16", "2026-02-28", 2, "2026-03-16", "2026-03-31"),
			("Bimonthly", "2024-02-16", "2024-02-29", 1, "2024-03-01", "2024-03-15"),
			("Bimonthly", "2026-12-16", "2026-12-31", 1, "2027-01-01", "2027-01-15"),
			("Monthly", "2026-02-01", "2026-02-28", 1, "2026-03-01", "2026-03-31"),
			("Monthly", "2024-02-01", "2024-02-29", 1, "2024-03-01", "2024-03-31"),
			("Monthly", "2026-02-10", "2026-02-20", 1, "2026-03-10", "2026-03-20"),
		)
		for frequency, start, end, offset, expected_start, expected_end in cases:
			with self.subTest(frequency=frequency, start=start, offset=offset):
				slip = frappe.get_doc(
					{
						"doctype": "Salary Slip",
						"payroll_frequency": frequency,
						"start_date": start,
						"end_date": end,
						"posting_date": start,
					}
				)
				slip.data = {"start_date": start, "end_date": end, "posting_date": start, "base": 1000}
				original_data = slip.data.copy()
				with patch.object(slip, "eval_condition_and_formula", return_value=1000) as evaluate:
					self.assertEqual(slip.get_amount_from_formula(frappe._dict(), offset), 1000)
				context = evaluate.call_args.args[1]
				self.assertEqual(getdate(context["start_date"]), getdate(expected_start))
				self.assertEqual(getdate(context["end_date"]), getdate(expected_end))
				self.assertEqual(getdate(context["posting_date"]), getdate(expected_start))
				self.assertEqual(slip.data, original_data)
