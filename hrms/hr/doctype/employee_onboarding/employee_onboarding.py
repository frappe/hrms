# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import get_link_to_form, now_datetime

from hrms.hr.doctype.employee_onboarding.onboarding_activities import OnboardingActivities

EMPLOYEE_SELF_SERVICE_ROLE = "Employee Self Service"
ONBOARDING_CANDIDATE_ROLE = "Employee Onboarding Candidate"
PORTAL_ROUTE = "/employee-documents"


def split_full_name(full_name: str) -> tuple[str, str, str]:
	parts = (full_name or "").split()
	if not parts:
		return "", "", ""
	if len(parts) == 1:
		return parts[0], "", ""
	if len(parts) == 2:
		return parts[0], "", parts[1]
	return parts[0], parts[1], " ".join(parts[2:])


class EmployeeOnboarding(OnboardingActivities, Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from hrms.hr.doctype.employee_boarding_activity.employee_boarding_activity import (
			EmployeeBoardingActivity,
		)
		from hrms.hr.doctype.employee_onboarding_document.employee_onboarding_document import (
			EmployeeOnboardingDocument,
		)

		activities: DF.Table[EmployeeBoardingActivity]
		amended_from: DF.Link | None
		appointment_letter: DF.Link | None
		appointment_letter_sent_on: DF.Datetime | None
		boarding_begins_on: DF.Date
		boarding_status: DF.Literal["Pending", "In Process", "Completed"]
		branch: DF.Link | None
		company: DF.Link
		company_email: DF.Data | None
		create_user_for: DF.Literal["Company Email", "Personal Email"]
		date_of_birth: DF.Date | None
		date_of_joining: DF.Date
		department: DF.Link | None
		designation: DF.Link | None
		details_submitted_on: DF.Datetime | None
		documents: DF.Table[EmployeeOnboardingDocument]
		documents_requested_on: DF.Datetime | None
		employee: DF.Link | None
		employee_grade: DF.Link | None
		employee_name: DF.Data
		employee_onboarding_template: DF.Link | None
		employment_type: DF.Link | None
		gender: DF.Link | None
		holiday_list: DF.Link | None
		job_applicant: DF.Link | None
		job_offer: DF.Link
		notify_users_by_email: DF.Check
		onboarding_stage: DF.Literal[
			"Create User",
			"Upload Documents",
			"Appointment Letter",
			"Create Employee",
			"Assign Masters",
			"Activities",
		]
		personal_email: DF.Data | None
		project: DF.Link | None
		reports_to: DF.Link | None
		submitted_details: DF.Code | None
		user: DF.Link | None
	# end: auto-generated types

	def onload(self):
		self.set_onload("offer_defaults", self.get_offer_defaults())

	def validate(self):
		self.set_employee()
		self.validate_duplicate_employee_onboarding()
		self.set_activities()
		self.validate_unique_activities()
		self.reconcile_activities()
		self.set_boarding_status()

	def on_update(self):
		self.sync_todos()

	def before_submit(self):
		self.complete_remaining_activities()

	def set_employee(self):
		if not self.employee:
			self.employee = frappe.db.get_value("Employee", {"job_offer": self.job_offer}, "name")

	def validate_duplicate_employee_onboarding(self):
		emp_onboarding = frappe.db.exists(
			"Employee Onboarding", {"job_offer": self.job_offer, "docstatus": ("!=", 2)}
		)
		if emp_onboarding and emp_onboarding != self.name:
			frappe.throw(
				_("Employee Onboarding: {0} already exists for Job Offer: {1}").format(
					frappe.bold(emp_onboarding), frappe.bold(self.job_offer)
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

	def get_employee_email(self) -> str | None:
		return self.company_email or self.personal_email

	@frappe.whitelist(methods=["POST"])
	def create_user(self) -> str:
		self.check_permission("write")

		if self.user:
			frappe.throw(_("User {0} is already linked").format(get_link_to_form("User", self.user)))

		email = self.company_email if self.create_user_for == "Company Email" else self.personal_email
		if not email:
			frappe.throw(_("Set the {0} to create a user").format(frappe.bold(_(self.create_user_for))))

		if frappe.db.exists("User", email):
			self.db_set("user", email)
			self.grant_onboarding_candidate_role()
			self.save_activity_states()
			return email

		first_name, middle_name, last_name = split_full_name(self.employee_name)
		user = frappe.new_doc("User")
		user.update(
			{
				"email": email,
				"first_name": first_name,
				"middle_name": middle_name,
				"last_name": last_name,
				"gender": self.gender,
				"birth_date": self.date_of_birth,
				"enabled": 1,
			}
		)
		user.append_roles(ONBOARDING_CANDIDATE_ROLE)
		user.insert(ignore_permissions=True)

		self.db_set("user", user.name)
		self.save_activity_states()
		return user.name

	def grant_onboarding_candidate_role(self) -> None:
		"""Let the linked user open the document upload portal.

		The role carries no DocType permissions - the portal's whitelisted methods are
		the gate. erpnext's validate_employee_role strips "Employee" and "Employee Self
		Service" from a user no Employee points at, so neither name can be used here.
		"""
		if not self.user:
			return

		user = frappe.get_doc("User", self.user)
		if ONBOARDING_CANDIDATE_ROLE in {row.role for row in user.roles}:
			return

		user.append_roles(ONBOARDING_CANDIDATE_ROLE)
		user.save(ignore_permissions=True)

	def grant_employee_self_service(self) -> None:
		"""Add the self-service role once an Employee is mapped.

		erpnext's validate_employee_role strips this role from a User that no Employee
		points at, so it cannot be granted while creating the user in step 1.
		"""
		if not self.user:
			return

		user = frappe.get_doc("User", self.user)
		user.append_roles(EMPLOYEE_SELF_SERVICE_ROLE)
		user.save(ignore_permissions=True)

	@frappe.whitelist(methods=["POST"])
	def send_documents_link(self) -> None:
		self.check_permission("write")

		recipient = self.get_employee_email()
		if not recipient:
			frappe.throw(_("Set a Company Email or Personal Email to send the request"))

		if not self.documents:
			frappe.throw(_("Add the documents you need from the employee"))

		if not self.user:
			frappe.throw(_("Create the user account before sending the request"))

		rows = "".join(f"<li>{frappe.utils.escape_html(row.document_name)}</li>" for row in self.documents)
		portal_url = frappe.utils.get_url(PORTAL_ROUTE)
		frappe.sendmail(
			recipients=[recipient],
			subject=_("Share your details and documents"),
			message=_("Hello {0}, please fill in your details and upload the following documents:").format(
				frappe.utils.escape_html(self.employee_name)
			)
			+ f"<ul>{rows}</ul>"
			+ f'<p><a href="{portal_url}">{_("Open the form")}</a></p>'
			+ f"<p>{_('Sign in as {0}.').format(frappe.utils.escape_html(self.user))}</p>",
			reference_doctype=self.doctype,
			reference_name=self.name,
		)
		self.db_set("documents_requested_on", now_datetime())

	@frappe.whitelist()
	def get_submitted_details(self) -> dict:
		"""Schema and values for the HR-side review of what the employee sent."""
		self.check_permission("read")

		from hrms.hr.doctype.employee_onboarding.employee_onboarding_portal import (
			PORTAL_SECTIONS,
			PORTAL_TABLES,
			parse_details,
		)

		return {
			"sections": PORTAL_SECTIONS,
			"tables": PORTAL_TABLES,
			"details": parse_details(self.submitted_details),
			"submitted_on": self.details_submitted_on,
		}

	@frappe.whitelist(methods=["POST"])
	def update_submitted_details(self, details: str | dict) -> None:
		"""Let HR correct the employee's answers before the Employee is created."""
		self.check_permission("write")

		if self.employee:
			frappe.throw(
				_("Employee {0} is already created").format(get_link_to_form("Employee", self.employee))
			)

		from hrms.hr.doctype.employee_onboarding.employee_onboarding_portal import clean_details

		self.db_set("submitted_details", json.dumps(clean_details(details)))

	@frappe.whitelist(methods=["POST"])
	def sync_appointment_letter(self) -> str | None:
		self.check_permission("write")

		if self.appointment_letter:
			return self.appointment_letter

		letter = frappe.db.get_value("Appointment Letter", {"employee_onboarding": self.name}, "name")
		if letter:
			self.db_set("appointment_letter", letter)
		return letter

	@frappe.whitelist(methods=["POST"])
	def send_appointment_letter(self) -> None:
		self.check_permission("write")

		if not self.appointment_letter:
			frappe.throw(_("Create the Appointment Letter first"))

		recipient = self.get_employee_email()
		if not recipient:
			frappe.throw(_("Set a Company Email or Personal Email to send the letter"))

		frappe.sendmail(
			recipients=[recipient],
			subject=_("Your appointment letter"),
			message=_("Hello {0}, please find your appointment letter attached.").format(
				frappe.utils.escape_html(self.employee_name)
			),
			attachments=[frappe.attach_print("Appointment Letter", self.appointment_letter)],
			reference_doctype=self.doctype,
			reference_name=self.name,
		)
		self.db_set("appointment_letter_sent_on", now_datetime())
		self.save_activity_states()

	@frappe.whitelist(methods=["POST"])
	def create_employee(self) -> str:
		self.check_permission("write")

		if self.employee:
			frappe.throw(
				_("Employee {0} is already created").format(get_link_to_form("Employee", self.employee))
			)

		employee = make_employee(self.name)
		employee.insert()

		self.db_set("employee", employee.name)
		self.grant_employee_self_service()
		self.save_activity_states()
		return employee.name

	@frappe.whitelist(methods=["POST"])
	def mark_onboarding_as_completed(self) -> None:
		self.check_permission("write")
		self.complete_remaining_activities()
		self.save()


@frappe.whitelist()
def make_employee(source_name: str, target_doc: str | Document | None = None) -> Document:
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
		apply_submitted_details(source, target)

	return get_mapped_doc(
		"Employee Onboarding",
		source_name,
		{
			"Employee Onboarding": {
				"doctype": "Employee",
				"field_map": {"employee_grade": "grade"},
				"field_no_map": ["employee_name", "amended_from", "naming_series"],
			}
		},
		target_doc,
		set_missing_values,
	)


def apply_submitted_details(source: Document, target: Document) -> None:
	"""Overlay what the employee filled in on the portal onto the new Employee.

	HR's own values are set first, so anything the employee supplied wins. Blank entries
	are skipped so an untouched portal field never clears a value HR already set.
	"""
	from hrms.hr.doctype.employee_onboarding.employee_onboarding_portal import (
		SCALAR_FIELDNAMES,
		TABLE_FIELDNAMES,
		parse_details,
	)

	details = parse_details(source.submitted_details)
	if not details:
		return

	for fieldname in SCALAR_FIELDNAMES:
		value = details.get(fieldname)
		if value not in (None, ""):
			target.set(fieldname, value)

	for table, allowed in TABLE_FIELDNAMES.items():
		for row in details.get(table) or []:
			target.append(table, {key: value for key, value in row.items() if key in allowed})
