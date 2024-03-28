# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import add_days, getdate


class LeavePolicyCorrection(Document):
	def validate(self):
		self.effective_from = getdate(self.effective_from)
		self.validate_effective_from()

	def validate_effective_from(self):
		existing_lpa = frappe.db.get_value(
			"Leave Policy Assignment",
			self.leave_policy_assignment,
			["effective_from", "effective_to"],
			as_dict=True,
		)

		if (
			getdate(existing_lpa.effective_from) > self.effective_from
			or getdate(existing_lpa.effective_to) < self.effective_from
		):
			frappe.throw(
				_("Effective from should be between {0} and {1}").format(
					getdate(existing_lpa.effective_from), getdate(existing_lpa.effective_to)
				)
			)

	def on_submit(self):
		self.revert_older_allocation()
		self.update_leave_policy_assignment()

	def update_leave_policy_assignment(self):
		new_lpa = get_mapped_doc(
			"Leave Policy Assignment",
			self.leave_policy_assignment,
			{
				"Leave Policy Assignment": {
					"doctype": "Leave Policy Assignment",
				}
			},
		)

		frappe.flags.in_lpa_correction = True
		frappe.db.set_value(
			"Leave Policy Assignment",
			self.leave_policy_assignment,
			"effective_to",
			add_days(self.effective_from, -1),
		)

		new_lpa.effective_from = self.effective_from
		new_lpa.submit()
		frappe.flags.in_lpa_correction = False

	def revert_older_allocation(self):
		leave_allocations = frappe.db.get_all(
			"Leave Allocation",
			filters={"leave_policy_assignment": self.leave_policy_assignment},
			pluck="name",
		)
		if not leave_allocations:
			return

		frappe.db.set_value(
			"Leave Allocation",
			{"name": ["in", leave_allocations]},
			"to_date",
			add_days(self.effective_from, -1),
		)

		ll_entries = frappe.db.get_all(
			"Leave Ledger Entry",
			filters={
				"transaction_type": "Leave Allocation",
				"transaction_name": ["in", leave_allocations],
				"from_date": [">=", self.effective_from],
			},
			pluck="name",
		)

		for leave_ledger_entry in ll_entries:
			new_ll = get_mapped_doc(
				"Leave Ledger Entry",
				leave_ledger_entry,
				{
					"Leave Ledger Entry": {
						"doctype": "Leave Ledger Entry",
					}
				},
			)

			new_ll.leaves = -(new_ll.leaves)
			new_ll.submit()
