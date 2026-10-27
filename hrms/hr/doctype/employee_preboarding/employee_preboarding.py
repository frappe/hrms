# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import get_link_to_form, now_datetime

from hrms.hr.doctype.employee_preboarding.preboarding_activities import PreboardingActivities

EMPLOYEE_SELF_SERVICE_ROLE = "Employee Self Service"


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
		branch: DF.Link | None
		company: DF.Link
		company_email: DF.Data | None
		create_user_for: DF.Literal["Company Email", "Personal Email"]
		date_of_birth: DF.Date | None
		date_of_joining: DF.Date
		department: DF.Link | None
		designation: DF.Link | None
		employee: DF.Link | None
		employee_boarding_template: DF.Link | None
		employee_grade: DF.Link | None
		employee_name: DF.Data
		employment_type: DF.Link | None
		gender: DF.Link | None
		holiday_list: DF.Link | None
		job_applicant: DF.Link | None
		job_offer: DF.Link
		notify_users_by_email: DF.Check
		personal_email: DF.Data | None
		project: DF.Link | None
		reports_to: DF.Link | None
		user: DF.Data | None
	# end: auto-generated types

	def onload(self):
		self.set_onload("offer_defaults", self.get_offer_defaults())
		self.set_onload("appointment_letter", self.get_appointment_letter())

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

	def get_employee_email(self) -> str | None:
		return self.company_email or self.personal_email

	@frappe.whitelist(methods=["POST"])
	def create_user(self) -> str:
		self.check_permission("write")
		self.validate_started()

		if self.user:
			frappe.throw(_("User {0} is already linked").format(get_link_to_form("User", self.user)))

		email = self.company_email if self.create_user_for == "Company Email" else self.personal_email
		if not email:
			frappe.throw(_("Set the {0} to create a user").format(frappe.bold(_(self.create_user_for))))

		if frappe.db.exists("User", email):
			self.db_set("user", email)
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
		user.insert(ignore_permissions=True)

		self.db_set("user", user.name)
		self.save_activity_states()
		return user.name

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

	@frappe.whitelist(methods=["POST"])
	def send_appointment_letter(self) -> None:
		self.check_permission("write")
		self.validate_started()

		letter = self.get_appointment_letter()
		if not letter:
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
			attachments=[frappe.attach_print("Appointment Letter", letter)],
			reference_doctype=self.doctype,
			reference_name=self.name,
		)
		self.db_set("appointment_letter_sent_on", now_datetime())
		self.save_activity_states()

	def attach_employee(self, employee: str) -> None:
		self.db_set("employee", employee)
		self.grant_employee_self_service()
		self.save_activity_states()


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


def unlink_deleted_user(user: Document, method: str | None = None) -> None:
	"""Clear a deleted user from its preboarding and open the Create User row again.

	The preboarding keeps the user as a plain value, not a Link, so deleting the user is not
	blocked by the preboarding.
	"""
	for name in frappe.get_all("Employee Preboarding", filters={"user": user.name}, pluck="name"):
		preboarding = frappe.get_doc("Employee Preboarding", name)
		preboarding.db_set("user", None)
		preboarding.save_activity_states()


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
