# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import os

import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification
from frappe.model import display_fieldtypes, table_fields
from frappe.model.document import Document
from frappe.permissions import add_permission
from frappe.utils import get_url, now_datetime

PREBOARDING_CANDIDATE_ROLE = "Preboarding Candidate"
PREBOARDING_INVITE_TEMPLATE = "Preboarding Invite"
PREBOARDING_ROUTE = "/preboarding"
REVIEWER_ROLES = ("HR Manager", "HR User", "System Manager")
CANDIDATE_LINK_DOCTYPES = ("Gender", "Salutation")
REVIEW_SKIPPED_TABS = ("documents_tab", "request_tab")
NOT_COPIED_FIELDS = ("employee_name",)


class EmployeeRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from erpnext.setup.doctype.employee_education.employee_education import EmployeeEducation
		from erpnext.setup.doctype.employee_external_work_history.employee_external_work_history import (
			EmployeeExternalWorkHistory,
		)

		from hrms.hr.doctype.employee_boarding_document.employee_boarding_document import (
			EmployeeBoardingDocument,
		)

		bank_ac_no: DF.Data | None
		bank_name: DF.Data | None
		bio: DF.TextEditor | None
		blood_group: DF.Literal["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
		cell_number: DF.Data | None
		current_accommodation_type: DF.Literal["", "Rented", "Owned"]
		current_address: DF.SmallText | None
		date_of_birth: DF.Date
		date_of_issue: DF.Date | None
		documents: DF.Table[EmployeeBoardingDocument]
		education: DF.Table[EmployeeEducation]
		emergency_phone_number: DF.Data | None
		employee_name: DF.Data | None
		employee_preboarding: DF.Link
		external_work_history: DF.Table[EmployeeExternalWorkHistory]
		family_background: DF.SmallText | None
		first_name: DF.Data
		gender: DF.Link
		health_details: DF.SmallText | None
		iban: DF.Data | None
		image: DF.AttachImage | None
		last_name: DF.Data | None
		marital_status: DF.Literal["", "Single", "Married", "Divorced", "Widowed"]
		middle_name: DF.Data | None
		passport_number: DF.Data | None
		permanent_accommodation_type: DF.Literal["", "Rented", "Owned"]
		permanent_address: DF.SmallText | None
		person_to_be_contacted: DF.Data | None
		personal_email: DF.Data | None
		place_of_issue: DF.Data | None
		relation: DF.Data | None
		salutation: DF.Link | None
		submitted_on: DF.Datetime | None
		user: DF.Data | None
		valid_upto: DF.Date | None
	# end: auto-generated types

	_DOCTYPE_NAME = "Employee Request"

	def validate(self):
		self.flags.ignore_mandatory = not self.flags.submitting_details
		self.validate_document_list()
		self.make_attachments_private()

	@frappe.whitelist(methods=["POST"])
	def submit_details(self) -> None:
		self.check_permission("write")
		self.validate_required_documents()
		self.flags.submitting_details = True
		self.save()
		self.db_set("submitted_on", now_datetime(), notify=True)
		self.notify_reviewer()

	def validate_required_documents(self):
		missing = [row.document_name for row in self.documents if row.required and not row.attachment]
		if missing:
			frappe.throw(
				_("Upload {0} before submitting").format(", ".join(frappe.bold(name) for name in missing)),
				title=_("Documents missing"),
			)

	def validate_document_list(self):
		if is_reviewer() or self.is_new():
			return

		before = self.get_doc_before_save()
		requested = [(row.name, row.document_name, row.required) for row in before.documents]
		if [(row.name, row.document_name, row.required) for row in self.documents] != requested:
			frappe.throw(_("Only HR can change the requested documents"), frappe.PermissionError)

	def make_attachments_private(self):
		if self.image:
			self.image = self.make_private(self.image)
		for row in self.documents:
			if row.attachment:
				row.attachment = self.make_private(row.attachment)

	def make_private(self, url: str) -> str:
		attached = {"attached_to_doctype": self.doctype, "attached_to_name": self.name}
		unattached = {
			"attached_to_doctype": ["is", "not set"],
			"attached_to_name": ["is", "not set"],
			"owner": frappe.session.user,
		}
		name = frappe.db.get_value("File", {"file_url": url, **attached}, "name") or frappe.db.get_value(
			"File", {"file_url": url, **unattached}, "name"
		)
		if not name:
			if frappe.db.exists("File", {"file_url": url}):
				frappe.throw(_("Upload {0} again to attach it to this request").format(frappe.bold(url)))
			return url
		file = frappe.get_doc("File", name)
		if not file.is_private:
			file.is_private = 1
			file.save(ignore_permissions=True)
		return file.file_url

	def get_employee_values(self) -> dict:
		employee_meta = frappe.get_meta("Employee")
		values = {}
		for df in self.meta.fields:
			if df.fieldtype in display_fieldtypes or df.fieldname in NOT_COPIED_FIELDS:
				continue
			if not employee_meta.has_field(df.fieldname):
				continue
			value = self.get(df.fieldname)
			if df.fieldtype in table_fields:
				value = [
					{
						key: cell
						for key, cell in row.as_dict(
							no_default_fields=True, no_child_table_fields=True
						).items()
						if not key.startswith("__")
					}
					for row in value
				]
			if value:
				values[df.fieldname] = value
		return values

	def get_review(self) -> dict:
		return {
			"name": self.name,
			"photo": self.image,
			"documents": [
				{"label": row.document_name, "url": row.attachment}
				for row in self.documents
				if row.attachment
			],
		}

	def apply_to(self, employee: str) -> None:
		filled = self.fill_blank_fields(frappe.get_doc("Employee", employee))
		moved = self.move_attachments(employee)
		if self.user:
			user = frappe.get_doc("User", self.user)
			user.flags.ignore_permissions = True
			user.remove_roles(PREBOARDING_CANDIDATE_ROLE)
		frappe.delete_doc(self.doctype, self.name, ignore_permissions=True)
		if summary := get_apply_summary(filled, moved):
			frappe.msgprint(
				_("{0} from {1}'s Employee Request").format(summary, self.employee_name),
				alert=True,
				indicator="green",
			)

	def fill_blank_fields(self, employee: Document) -> int:
		blanks = {key: value for key, value in self.get_employee_values().items() if not employee.get(key)}
		scalars = {key: value for key, value in blanks.items() if not isinstance(value, list)}
		if scalars:
			employee.db_set(scalars)
		for fieldname, rows in blanks.items():
			if isinstance(rows, list):
				for row in rows:
					employee.append(fieldname, row).db_insert()
		return len(blanks)

	def move_attachments(self, employee: str) -> int:
		document_names = {row.attachment: row.document_name for row in self.documents if row.attachment}
		in_use = [url for url in (self.image, *document_names) if url]
		files = frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": self.doctype,
				"attached_to_name": self.name,
				"file_url": ["in", in_use],
			},
			pluck="name",
		)
		for name in files:
			file = frappe.get_doc("File", name)
			file.update(
				{"attached_to_doctype": "Employee", "attached_to_name": employee, "attached_to_field": None}
			)
			if label := document_names.get(file.file_url):
				file.file_name = f"{label}{os.path.splitext(file.file_name)[1]}"
			file.save(ignore_permissions=True)
		return len(document_names)

	def notify_reviewer(self):
		reviewer = get_reviewer(self.employee_preboarding)
		enqueue_create_notification(
			frappe.db.get_value("User", reviewer, "email"),
			{
				"type": "Alert",
				"document_type": self.doctype,
				"document_name": self.name,
				"from_user": frappe.session.user,
				"subject": _("{0} submitted their details and documents").format(
					frappe.bold(self.employee_name)
				),
				"email_content": _("Review them while creating the employee: {0}").format(
					get_url(self.get_url())
				),
			},
		)


def get_preboarding_boot() -> dict:
	if frappe.session.user == "Guest":
		return {}
	request = frappe.db.get_value("Employee Request", {"user": frappe.session.user})
	if not request:
		return {"request": None}

	meta = frappe.get_meta("Employee Request")
	return {
		"request": request,
		"fields": get_translated_fields(meta.name),
		"child_metas": {df.options: get_translated_fields(df.options) for df in meta.get_table_fields()},
	}


def get_translated_fields(doctype: str) -> list[dict]:
	return [
		{**df.as_dict(no_default_fields=True), "label": _(df.label) if df.label else df.label}
		for df in frappe.get_meta(doctype).fields
	]


def get_review_fields() -> list[str]:
	employee_meta = frappe.get_meta("Employee")
	tab = None
	fields = []
	for df in frappe.get_meta("Employee Request").fields:
		if df.fieldtype == "Tab Break":
			tab = df.fieldname
		elif tab not in REVIEW_SKIPPED_TABS and df.fieldtype not in display_fieldtypes:
			if employee_meta.has_field(df.fieldname):
				fields.append(df.fieldname)
	return fields


def get_apply_summary(filled: int, moved: int) -> str:
	parts = []
	if filled:
		parts.append(
			_("Filled 1 empty field") if filled == 1 else _("Filled {0} empty fields").format(filled)
		)
	if moved:
		parts.append(_("attached 1 document") if moved == 1 else _("attached {0} documents").format(moved))
	return _(" and ").join(parts).capitalize() if parts else ""


def get_reviewer(preboarding: str) -> str:
	assignee = frappe.db.get_value(
		"Employee Boarding Activity",
		{"parent": preboarding, "parenttype": "Employee Preboarding", "action": "Create Employee"},
		"user",
	)
	return assignee or frappe.db.get_value("Employee Preboarding", preboarding, "owner")


def is_reviewer(user: str | None = None) -> bool:
	return bool(set(frappe.get_roles(user)) & set(REVIEWER_ROLES))


def get_permission_query_conditions(user: str | None = None) -> str:
	user = user or frappe.session.user
	if is_reviewer(user):
		return ""
	return f"`tabEmployee Request`.`user` = {frappe.db.escape(user)}"


def has_permission(doc, ptype: str | None = None, user: str | None = None) -> bool:
	user = user or frappe.session.user
	return is_reviewer(user) or doc.user == user


def setup_preboarding_candidate() -> None:
	if not frappe.db.exists("Role", PREBOARDING_CANDIDATE_ROLE):
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": PREBOARDING_CANDIDATE_ROLE,
				"desk_access": 0,
				"home_page": PREBOARDING_ROUTE,
			}
		).insert(ignore_permissions=True)

	for doctype in CANDIDATE_LINK_DOCTYPES:
		add_permission(doctype, PREBOARDING_CANDIDATE_ROLE)

	if not frappe.db.exists("Email Template", PREBOARDING_INVITE_TEMPLATE):
		frappe.get_doc(
			{
				"doctype": "Email Template",
				"name": PREBOARDING_INVITE_TEMPLATE,
				"subject": "Welcome to {{ company }}, {{ employee_name }}",
				"use_html": 1,
				"response_html": PREBOARDING_INVITE_MESSAGE,
			}
		).insert(ignore_permissions=True)


PREBOARDING_INVITE_MESSAGE = """<p>Hi {{ employee_name }},</p>
<p>We are glad you are joining {{ company }} on {{ date_of_joining }}.</p>
<p>Before your first day, please share your personal details and documents here:</p>
<p><a href="{{ preboarding_url }}">{{ preboarding_url }}</a></p>
<p>Set your password from the welcome email we sent you, then log in with this email address.
If that link has expired, use <b>Forgot password</b> on the login page.</p>
"""
