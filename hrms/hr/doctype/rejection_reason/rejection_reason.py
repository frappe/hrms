# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

DECLINED_OFFER = "Declined offer"
DEFAULT_REASONS = [
	"Not qualified",
	"Failed interview",
	"Withdrew",
	"Hired elsewhere",
	"Salary mismatch",
	"No response",
	"Position filled",
	DECLINED_OFFER,
]


class RejectionReason(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		reason: DF.Data
	# end: auto-generated types

	pass


def create_default_reasons():
	"""Adds the standard reasons that are missing; existing ones are left as they are."""
	for reason in DEFAULT_REASONS:
		if not frappe.db.exists("Rejection Reason", reason):
			frappe.get_doc({"doctype": "Rejection Reason", "reason": reason}).insert(ignore_permissions=True)
