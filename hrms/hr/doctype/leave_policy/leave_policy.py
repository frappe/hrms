# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document


class LeavePolicy(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.leave_policy_detail.leave_policy_detail import LeavePolicyDetail

		amended_from: DF.Link | None
		leave_policy_details: DF.Table[LeavePolicyDetail]
		title: DF.Data
	# end: auto-generated types

	def validate(self):
		if self.leave_policy_details:
			for lp_detail in self.leave_policy_details:
				max_leaves_allowed = frappe.db.get_value(
					"Leave Type", lp_detail.leave_type, "max_leaves_allowed"
				)
				if max_leaves_allowed > 0 and lp_detail.annual_allocation > max_leaves_allowed:
					frappe.throw(
						_("Maximum leave allowed in the leave type {0} is {1}").format(
							lp_detail.leave_type, max_leaves_allowed
						)
					)
