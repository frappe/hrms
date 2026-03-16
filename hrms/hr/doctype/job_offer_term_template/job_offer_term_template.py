# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class JobOfferTermTemplate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.job_offer_term.job_offer_term import JobOfferTerm

		offer_terms: DF.Table[JobOfferTerm]
		title: DF.Data | None
	# end: auto-generated types

	pass
