# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import os

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.jinja import validate_template


class AppointmentLetterTemplate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		is_default: DF.Check
		letter_body: DF.TextEditor
		template_name: DF.Data
	# end: auto-generated types

	def validate(self):
		validate_template(self.letter_body)

	def on_update(self):
		if self.is_default:
			frappe.db.set_value(
				"Appointment Letter Template",
				{"name": ("!=", self.name), "is_default": 1},
				"is_default",
				0,
				update_modified=False,
			)


@frappe.whitelist()
def get_default_letter_body() -> str:
	path = os.path.join(os.path.dirname(__file__), "default_letter_body.html")
	with open(path) as f:
		body = "".join(line.strip() for line in f)
	return f'<div class="ql-editor read-mode">{body}</div>'


def get_default_template() -> str | None:
	return frappe.db.get_value("Appointment Letter Template", {"is_default": 1})


def create_default_template() -> None:
	if get_default_template():
		return

	template_name = _("Standard Appointment Letter")
	if frappe.db.exists("Appointment Letter Template", template_name):
		frappe.db.set_value("Appointment Letter Template", template_name, "is_default", 1)
		return

	frappe.get_doc(
		{
			"doctype": "Appointment Letter Template",
			"template_name": template_name,
			"is_default": 1,
			"letter_body": get_default_letter_body(),
		}
	).insert(ignore_permissions=True)
