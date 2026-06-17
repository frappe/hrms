# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class JobApplicantStatus(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		color: DF.Color | None
		is_closed_status: DF.Check
		sequence: DF.Int
		status_name: DF.Data

	# end: auto-generated types

	_DOCTYPE_NAME = "Job Applicant Status"
