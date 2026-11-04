# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import os

import frappe
from frappe.model.document import Document
from frappe.utils.jinja import validate_template


class AppointmentLetterTemplate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		letter_body: DF.TextEditor
		template_name: DF.Data
	# end: auto-generated types

	def validate(self):
		validate_template(self.letter_body)


@frappe.whitelist()
def get_default_letter_body() -> str:
	path = os.path.join(os.path.dirname(__file__), "default_letter_body.html")
	with open(path) as f:
		body = "".join(line.strip() for line in f)
	return f'<div class="ql-editor read-mode">{body}</div>'
