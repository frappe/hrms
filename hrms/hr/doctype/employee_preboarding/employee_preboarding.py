# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import formatdate, get_link_to_form, get_url, now_datetime, validate_email_address

from hrms.hr.doctype.appointment_letter_template.appointment_letter_template import get_default_template
from hrms.hr.doctype.employee_preboarding.preboarding_activities import PreboardingActivities
from hrms.hr.doctype.employee_request.employee_request import (
	PREBOARDING_CANDIDATE_ROLE,
	PREBOARDING_INVITE_TEMPLATE,
	PREBOARDING_ROUTE,
	get_review_fields,
)

EMPLOYEE_SELF_SERVICE_ROLE = "Employee Self Service"
OFFER_EMPLOYEE_FIELDS = ("branch", "employment_type", "reports_to")
USER_EMAIL_FIELDS = {"Company Email": "company_email", "Personal Email": "personal_email"}


def split_full_name(full_name: str) -> tuple[str, str, str]:
	parts = (full_name or "").split()
	if not parts:
		return "", "", ""
	if len(parts) == 1:
		return parts[0], "", ""
	if len(parts) == 2:
		return parts[0], "", parts[1]
	return parts[0], parts[1], " ".join(parts[2:])


class EmployeePreboarding(PreboardingActivities, Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.employee_boarding_activity.employee_boarding_activity import (
			EmployeeBoardingActivity,
		)

		activities: DF.Table[EmployeeBoardingActivity]
		amended_from: DF.Link | None
		appointment_letter_sent_on: DF.Datetime | None
		boarding_begins_on: DF.Date
		boarding_status: DF.Literal["Pending", "In Process", "Completed"]
		company: DF.Link
		company_email: DF.Data | None
		date_of_joining: DF.Date
		department: DF.Link | None
		designation: DF.Link | None
		employee: DF.Link | None
		employee_boarding_template: DF.Link | None
		employee_grade: DF.Link | None
		employee_name: DF.Data
		job_applicant: DF.Link | None
		job_offer: DF.Link
		notify_users_by_email: DF.Check
		personal_email: DF.Data | None
		user: DF.Data | None
	# end: auto-generated types

	def onload(self):
		self.set_onload("offer_defaults", self.get_offer_defaults())
		self.set_onload("appointment_letter", self.get_appointment_letter())
		self.set_onload("draft_assignments", self.get_draft_assignments())
		self.set_onload("user_info", self.get_assignee_info())
		self.set_onload("needs_sync", self.docstatus == 1 and bool(self.reconcile_activities()))

	def before_insert(self):
		self.set_template()
		if self.amended_from:
			self.clear_todos()

	def validate(self):
		self.set_employee()
		self.validate_duplicate_employee_preboarding()
		self.set_activities()
		self.validate_unique_activities()
		self.reconcile_activities()
		self.set_boarding_status()

	def on_update(self):
		self.sync_todos()

	def on_cancel(self):
		self.close_todos()

	def set_employee(self):
		if not self.employee:
			self.employee = frappe.db.get_value("Employee", {"job_offer": self.job_offer}, "name")

	def validate_duplicate_employee_preboarding(self):
		emp_preboarding = frappe.db.exists(
			"Employee Preboarding", {"job_offer": self.job_offer, "docstatus": ("!=", 2)}
		)
		if emp_preboarding and emp_preboarding != self.name:
			frappe.throw(
				_("Employee Preboarding: {0} already exists for Job Offer: {1}").format(
					frappe.bold(emp_preboarding), frappe.bold(self.job_offer)
				)
			)

	@frappe.whitelist()
	def get_company_holiday_list(self) -> str | None:
		self.check_permission("read")

		assigned = frappe.db.get_value(
			"Holiday List Assignment",
			{"applicable_for": "Company", "assigned_to": self.company, "docstatus": 1},
			"holiday_list",
			order_by="from_date desc",
		)
		return assigned or frappe.db.get_value("Company", self.company, "default_holiday_list")

	@frappe.whitelist(methods=["POST"])
	def create_user(
		self,
		create_user_for: str = "Company Email",
		personal_email: str | None = None,
		company_email: str | None = None,
	) -> str:
		self.check_permission("write")
		self.validate_started()
		self.set_user_emails(personal_email=personal_email, company_email=company_email)

		if self.user:
			frappe.throw(_("User {0} is already linked").format(get_link_to_form("User", self.user)))

		fieldname = USER_EMAIL_FIELDS.get(create_user_for)
		email = fieldname and self.get(fieldname)
		if not email:
			frappe.throw(_("Set the {0} to create a user").format(frappe.bold(_(create_user_for))))

		user = email if frappe.db.exists("User", email) else self.insert_user(email)
		self.db_set("user", user)
		self.start_employee_request()
		self.save_activity_states()
		return user

	def insert_user(self, email: str) -> str:
		first_name, middle_name, last_name = split_full_name(self.employee_name)
		user = frappe.new_doc("User")
		user.update(
			{
				"email": email,
				"first_name": first_name,
				"middle_name": middle_name,
				"last_name": last_name,
				"enabled": 1,
			}
		)
		user.insert(ignore_permissions=True)
		return user.name

	def start_employee_request(self) -> None:
		user = frappe.get_doc("User", self.user)
		user.append_roles(PREBOARDING_CANDIDATE_ROLE)
		user.save(ignore_permissions=True)
		if request := frappe.db.get_value("Employee Request", {"employee_preboarding": self.name}):
			frappe.db.set_value("Employee Request", request, "user", self.user)
		else:
			self.make_employee_request().insert()
		self.send_preboarding_invite()

	def make_employee_request(self) -> Document:
		first_name, middle_name, last_name = split_full_name(self.employee_name)
		request = frappe.new_doc("Employee Request")
		request.update(
			{
				"employee_preboarding": self.name,
				"user": self.user,
				"first_name": first_name,
				"middle_name": middle_name,
				"last_name": last_name,
				"personal_email": self.personal_email,
			}
		)
		for row in get_required_documents(self.employee_boarding_template):
			request.append("documents", row)
		return request

	def send_preboarding_invite(self) -> None:
		template = frappe.get_doc("Email Template", PREBOARDING_INVITE_TEMPLATE)
		email = template.get_formatted_email(
			{
				"employee_name": self.employee_name,
				"company": self.company,
				"date_of_joining": formatdate(self.date_of_joining),
				"preboarding_url": get_url(PREBOARDING_ROUTE),
			}
		)
		frappe.sendmail(
			recipients=[self.user],
			subject=email["subject"],
			message=email["message"],
			reference_doctype=self.doctype,
			reference_name=self.name,
		)

	def set_user_emails(self, **emails) -> None:
		changed = {
			fieldname: email.strip()
			for fieldname, email in emails.items()
			if email and email.strip() != self.get(fieldname)
		}
		for email in changed.values():
			validate_email_address(email, throw=True)
		if changed:
			self.db_set(changed)

	def grant_employee_self_service(self) -> None:
		"""Add the self-service role once an Employee is mapped.

		erpnext's validate_employee_role strips this role from a User that no Employee
		points at, so it cannot be granted when the user is created.
		"""
		if not self.user:
			return

		user = frappe.get_doc("User", self.user)
		user.append_roles(EMPLOYEE_SELF_SERVICE_ROLE)
		user.save(ignore_permissions=True)

	def get_appointment_letter(self) -> str | None:
		return frappe.db.get_value("Appointment Letter", {"employee_preboarding": self.name}, "name")

	def attach_employee(self, employee: str) -> None:
		self.db_set("employee", employee)
		if letter := self.get_appointment_letter():
			frappe.db.set_value("Appointment Letter", letter, "employee", employee)
		self.grant_employee_self_service()
		if request := self.get_employee_request():
			request.apply_to(employee)
		self.save_activity_states()

	def get_employee_request(self) -> Document | None:
		name = frappe.db.get_value("Employee Request", {"employee_preboarding": self.name})
		return name and frappe.get_doc("Employee Request", name)


def get_required_documents(template: str | None) -> list[dict]:
	if not template:
		return []
	return frappe.get_all(
		"Employee Boarding Document",
		fields=["document_name", "required", "description"],
		filters={"parent": template, "parenttype": "Employee Boarding Template"},
		order_by="idx",
	)


@frappe.whitelist()
def make_employee(source_name: str, target_doc: str | Document | None = None) -> Document:
	frappe.get_doc("Employee Preboarding", source_name).validate_started()

	def set_missing_values(source, target):
		first_name, middle_name, last_name = split_full_name(source.employee_name)
		target.first_name = first_name
		target.middle_name = middle_name
		target.last_name = last_name
		target.personal_email = source.personal_email
		target.company_email = source.company_email
		target.user_id = source.user
		target.job_offer = source.job_offer
		target.status = "Active"
		if source.job_offer:
			target.update(
				frappe.db.get_value("Job Offer", source.job_offer, OFFER_EMPLOYEE_FIELDS, as_dict=True) or {}
			)
		request = source.get_employee_request()
		if request:
			target.update(request.get_employee_values())
		target.set_onload(
			"employee_details",
			{"fields": get_review_fields(), **(request.get_review() if request else {"documents": []})},
		)

	return get_mapped_doc(
		"Employee Preboarding",
		source_name,
		{
			"Employee Preboarding": {
				"doctype": "Employee",
				"field_map": {"employee_grade": "grade"},
				"field_no_map": ["employee_name", "amended_from", "naming_series"],
			}
		},
		target_doc,
		set_missing_values,
	)


@frappe.whitelist()
def make_appointment_letter(source_name: str, target_doc: str | Document | None = None) -> Document:
	def set_missing_values(source, target):
		target.appointment_date = source.date_of_joining
		target.applicant_email = source.company_email or source.personal_email
		target.letter_head = frappe.db.get_value("Job Offer", source.job_offer, "letter_head")
		if source.employee:
			target.address = frappe.db.get_value("Employee", source.employee, "current_address")
			target.set_shift_from_employee()
		target.appointment_letter_template = get_default_template()
		target.letter_body = target.get_template_body()

	return get_mapped_doc(
		"Employee Preboarding",
		source_name,
		{
			"Employee Preboarding": {
				"doctype": "Appointment Letter",
				"field_map": {"name": "employee_preboarding", "employee_name": "applicant_name"},
				"field_no_map": ["naming_series", "amended_from"],
			}
		},
		target_doc,
		set_missing_values,
	)


def unlink_deleted_user(user: Document, method: str | None = None) -> None:
	"""Clear a deleted user from its preboarding and open the Create User row again.

	The preboarding keeps the user as a plain value, not a Link, so deleting the user is not
	blocked by the preboarding.
	"""
	for name in frappe.get_all("Employee Preboarding", filters={"user": user.name}, pluck="name"):
		preboarding = frappe.get_doc("Employee Preboarding", name)
		preboarding.db_set("user", None)
		preboarding.save_activity_states()
	frappe.db.set_value("Employee Request", {"user": user.name}, "user", None)


def mark_appointment_letter_sent(preboarding: str) -> None:
	doc = frappe.get_doc("Employee Preboarding", preboarding)
	doc.db_set("appointment_letter_sent_on", now_datetime())
	doc.save_activity_states()


def reopen_appointment_letter(preboarding: str) -> None:
	"""Open the Send Appointment Letter row again once its letter is deleted."""
	doc = frappe.get_doc("Employee Preboarding", preboarding)
	doc.db_set("appointment_letter_sent_on", None)
	doc.save_activity_states()


def rename_preboarding_user(
	user: Document, method: str | None, old_name: str, new_name: str, merge: bool = False
) -> None:
	"""Keep the preboarding's user, a plain value, pointing at a renamed user."""
	frappe.db.set_value("Employee Preboarding", {"user": old_name}, "user", new_name, update_modified=False)
