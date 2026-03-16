# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document


class AppointmentLetter(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.appointment_letter_content.appointment_letter_content import (
			AppointmentLettercontent,
		)

		applicant_name: DF.Data
		appointment_date: DF.Date
		appointment_letter_template: DF.Link
		closing_notes: DF.Text | None
		company: DF.Link
		introduction: DF.LongText
		job_applicant: DF.Link
		terms: DF.Table[AppointmentLettercontent]
	# end: auto-generated types

	pass


@frappe.whitelist()
def get_appointment_letter_details(template: str) -> list:
	body = []
	intro = frappe.get_list(
		"Appointment Letter Template",
		fields=["introduction", "closing_notes"],
		filters={"name": template},
	)[0]
	content = frappe.get_all(
		"Appointment Letter content",
		fields=["title", "description"],
		filters={"parent": template},
		order_by="idx",
	)
	body.append(intro)
	body.append({"description": content})
	return body
