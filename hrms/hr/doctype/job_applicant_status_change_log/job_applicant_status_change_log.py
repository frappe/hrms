# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class JobApplicantStatusChangeLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		changed_by: DF.Link | None
		changed_on: DF.Datetime | None
		new_status: DF.Link
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		previous_status: DF.Link | None
		time_in_previous_status: DF.Duration | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Job Applicant Status Change Log"
