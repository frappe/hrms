# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Backend for the Employee Documents portal.

The onboarding employee holds the Employee Onboarding Candidate role, which carries no
DocType permissions. Every method here resolves the onboarding from the session user and
writes with ignore_permissions, so the session is the only gate and no HR field is
reachable from the portal.
"""

import json

import frappe
from frappe import _
from frappe.utils import now_datetime

PORTAL_SECTIONS = [
	{
		"name": "personal",
		"label": "Personal Details",
		"description": "Your name as it should appear on official records.",
		"fields": [
			{"fieldname": "salutation", "fieldtype": "Link", "options": "Salutation", "label": "Salutation"},
			{"fieldname": "first_name", "fieldtype": "Data", "label": "First Name", "reqd": 1},
			{"fieldname": "middle_name", "fieldtype": "Data", "label": "Middle Name"},
			{"fieldname": "last_name", "fieldtype": "Data", "label": "Last Name"},
			{"fieldname": "gender", "fieldtype": "Link", "options": "Gender", "label": "Gender", "reqd": 1},
			{"fieldname": "date_of_birth", "fieldtype": "Date", "label": "Date of Birth", "reqd": 1},
			{
				"fieldname": "marital_status",
				"fieldtype": "Select",
				"options": ["", "Single", "Married", "Divorced", "Widowed"],
				"label": "Marital Status",
			},
			{
				"fieldname": "blood_group",
				"fieldtype": "Select",
				"options": ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
				"label": "Blood Group",
			},
		],
	},
	{
		"name": "contact",
		"label": "Contact",
		"description": "How we reach you, and who we call in an emergency.",
		"fields": [
			{"fieldname": "cell_number", "fieldtype": "Data", "label": "Mobile", "reqd": 1},
			{"fieldname": "personal_email", "fieldtype": "Data", "label": "Personal Email"},
			{"fieldname": "emergency_phone_number", "fieldtype": "Data", "label": "Emergency Phone"},
			{"fieldname": "person_to_be_contacted", "fieldtype": "Data", "label": "Emergency Contact Name"},
			{"fieldname": "relation", "fieldtype": "Data", "label": "Relation"},
		],
	},
	{
		"name": "address",
		"label": "Address",
		"description": "Your appointment letter is posted to the permanent address.",
		"fields": [
			{
				"fieldname": "permanent_accommodation_type",
				"fieldtype": "Select",
				"options": ["", "Rented", "Owned"],
				"label": "Permanent Address Is",
			},
			{"fieldname": "permanent_address", "fieldtype": "Small Text", "label": "Permanent Address"},
			{
				"fieldname": "current_accommodation_type",
				"fieldtype": "Select",
				"options": ["", "Rented", "Owned"],
				"label": "Current Address Is",
			},
			{"fieldname": "current_address", "fieldtype": "Small Text", "label": "Current Address"},
		],
	},
	{
		"name": "identification",
		"label": "Identification",
		"description": "Passport and health details. Leave blank if they do not apply.",
		"fields": [
			{"fieldname": "passport_number", "fieldtype": "Data", "label": "Passport Number"},
			{"fieldname": "date_of_issue", "fieldtype": "Date", "label": "Date of Issue"},
			{"fieldname": "valid_upto", "fieldtype": "Date", "label": "Valid Up To"},
			{"fieldname": "place_of_issue", "fieldtype": "Data", "label": "Place of Issue"},
			{"fieldname": "family_background", "fieldtype": "Small Text", "label": "Family Background"},
			{"fieldname": "health_details", "fieldtype": "Small Text", "label": "Health Details"},
		],
	},
	{
		"name": "bank",
		"label": "Bank Details",
		"description": "Where your salary is paid.",
		"fields": [
			{
				"fieldname": "salary_mode",
				"fieldtype": "Select",
				"options": ["", "Bank", "Cash", "Cheque"],
				"label": "Salary Mode",
			},
			{"fieldname": "bank_name", "fieldtype": "Data", "label": "Bank Name"},
			{"fieldname": "bank_ac_no", "fieldtype": "Data", "label": "Bank A/C No."},
			{"fieldname": "iban", "fieldtype": "Data", "label": "IBAN"},
		],
	},
	{
		"name": "bio",
		"label": "About You",
		"description": "A short introduction for your team. Optional.",
		"fields": [
			{"fieldname": "bio", "fieldtype": "Text Editor", "label": "Bio / Cover Letter"},
		],
	},
]

PORTAL_TABLES = [
	{
		"fieldname": "education",
		"label": "Educational Qualification",
		"add_label": "Add Qualification",
		"description": "Highest qualification first.",
		"empty_message": "No qualifications added yet.",
		"fields": [
			{"fieldname": "school_univ", "fieldtype": "Small Text", "label": "School / University"},
			{"fieldname": "qualification", "fieldtype": "Data", "label": "Qualification"},
			{
				"fieldname": "level",
				"fieldtype": "Select",
				"options": ["", "Under Graduate", "Graduate", "Post Graduate"],
				"label": "Level",
			},
			{"fieldname": "year_of_passing", "fieldtype": "Int", "label": "Year of Passing"},
			{"fieldname": "class_per", "fieldtype": "Data", "label": "Class / Percentage"},
			{"fieldname": "maj_opt_subj", "fieldtype": "Text", "label": "Major / Optional Subjects"},
		],
	},
	{
		"fieldname": "external_work_history",
		"label": "Previous Work Experience",
		"add_label": "Add Experience",
		"description": "Most recent employer first.",
		"empty_message": "No previous experience added yet.",
		"fields": [
			{"fieldname": "company_name", "fieldtype": "Data", "label": "Company"},
			{"fieldname": "designation", "fieldtype": "Data", "label": "Designation"},
			{"fieldname": "total_experience", "fieldtype": "Data", "label": "Total Experience"},
			{"fieldname": "salary", "fieldtype": "Currency", "label": "Salary"},
			{"fieldname": "address", "fieldtype": "Small Text", "label": "Address"},
			{"fieldname": "contact", "fieldtype": "Data", "label": "Contact"},
		],
	},
]

PORTAL_STEPS = [
	{
		"name": "personal",
		"label": "Personal Details",
		"sections": ["personal", "identification", "bio"],
		"tables": [],
	},
	{"name": "contact", "label": "Address & Contacts", "sections": ["contact", "address"], "tables": []},
	{"name": "bank", "label": "Bank Details", "sections": ["bank"], "tables": []},
	{
		"name": "experience",
		"label": "Education & Work",
		"sections": [],
		"tables": ["education", "external_work_history"],
	},
	{"name": "documents", "label": "Documents", "sections": [], "tables": [], "documents": True},
]

SCALAR_FIELDNAMES = {field["fieldname"] for section in PORTAL_SECTIONS for field in section["fields"]}
TABLE_FIELDNAMES = {table["fieldname"]: {f["fieldname"] for f in table["fields"]} for table in PORTAL_TABLES}


def get_own_onboarding(for_update: bool = False) -> "frappe.Document":
	"""Resolve the session user's onboarding, or refuse.

	This is the only authorisation check in the portal. The candidate role grants no
	DocType permission, so a user with no onboarding of their own reaches nothing.
	"""
	name = frappe.db.get_value(
		"Employee Onboarding", {"user": frappe.session.user, "docstatus": ["!=", 2]}, "name"
	)
	if not name:
		frappe.throw(_("No onboarding is assigned to you."), frappe.PermissionError)

	doc = frappe.get_doc("Employee Onboarding", name)
	if for_update and (doc.details_confirmed_on or doc.employee):
		frappe.throw(_("Your details are with HR now and can no longer be changed."))

	return doc


@frappe.whitelist()
def get_onboarding_form() -> dict:
	"""Answer instead of throwing, so the portal can render a reason rather than a toast.

	save_onboarding_form still refuses hard - this is for the page shell, not the gate.
	"""
	from hrms.hr.doctype.employee_onboarding.employee_onboarding import ONBOARDING_CANDIDATE_ROLE

	if ONBOARDING_CANDIDATE_ROLE not in frappe.get_roles():
		return {"allowed": False, "reason": "no_role"}

	name = frappe.db.get_value(
		"Employee Onboarding", {"user": frappe.session.user, "docstatus": ["!=", 2]}, "name"
	)
	if not name:
		return {"allowed": False, "reason": "no_onboarding"}

	doc = frappe.get_doc("Employee Onboarding", name)

	return {
		"allowed": True,
		"onboarding": doc.name,
		"employee_name": doc.employee_name,
		"company": doc.company,
		"designation": doc.designation,
		"date_of_joining": doc.date_of_joining,
		"steps": PORTAL_STEPS,
		"sections": portal_sections_for_employee(),
		"tables": PORTAL_TABLES,
		"details": parse_details(doc.submitted_details) or seed_details(doc),
		"documents": [
			{
				"idx": row.idx,
				"document_name": row.document_name,
				"description": row.description,
				"required": row.required,
				"attachment": row.attachment,
			}
			for row in doc.documents
		],
		"submitted_on": doc.details_submitted_on,
		"confirmed_on": doc.details_confirmed_on,
		"is_submitted": bool(doc.details_confirmed_on),
		"is_locked": bool(doc.details_confirmed_on or doc.employee),
		"hr_contact": get_hr_contact(doc),
	}


@frappe.whitelist(methods=["POST"])
def save_onboarding_form(details: str | dict, documents: str | list | None = None) -> dict:
	doc = get_own_onboarding(for_update=True)

	clean = clean_details(details)
	doc.db_set("submitted_details", json.dumps(clean), update_modified=False)
	doc.db_set("details_submitted_on", now_datetime(), update_modified=False)

	save_documents(doc, documents)

	return {"submitted_on": doc.details_submitted_on}


def portal_sections_for_employee() -> list[dict]:
	"""Turn Link fields into Selects the portal can render.

	The candidate role grants no read on Gender or Salutation, so the page cannot run a
	link search. Sending the options with the schema keeps the lookup on this side.
	"""
	sections = []

	for section in PORTAL_SECTIONS:
		fields = [
			{**field, "fieldtype": "Select", "options": ["", *get_link_options(field["options"])]}
			if field["fieldtype"] == "Link"
			else field
			for field in section["fields"]
		]
		sections.append({**section, "fields": fields})

	return sections


def get_link_options(doctype: str) -> list[str]:
	return frappe.get_all(doctype, pluck="name", order_by="name", ignore_permissions=True)


@frappe.whitelist(methods=["POST"])
def submit_onboarding_form(details: str | dict, documents: str | list | None = None) -> dict:
	"""Final hand-off. The employee cannot edit after this, only HR can."""
	save_onboarding_form(details, documents)

	doc = get_own_onboarding(for_update=True)
	doc.db_set("details_confirmed_on", now_datetime(), update_modified=False)

	return {"confirmed_on": doc.details_confirmed_on}


def get_hr_contact(doc: "frappe.Document") -> str:
	"""Who the employee should follow up with - whoever raised the onboarding."""
	return frappe.db.get_value("User", doc.owner, "full_name") or doc.owner


def clean_details(details: str | dict) -> dict:
	"""Keep only the fields the portal owns, so no HR field can be smuggled in."""
	if isinstance(details, str):
		details = json.loads(details)

	clean = {fieldname: details.get(fieldname) for fieldname in SCALAR_FIELDNAMES if fieldname in details}

	for table, allowed in TABLE_FIELDNAMES.items():
		rows = details.get(table) or []
		clean[table] = [
			{fieldname: row.get(fieldname) for fieldname in allowed if fieldname in row}
			for row in rows
			if any(row.get(fieldname) for fieldname in allowed)
		]

	return clean


def save_documents(doc: "frappe.Document", documents: str | list | None) -> None:
	"""Write the uploaded file back to its row and attach it to the onboarding.

	The portal uploads an unattached private File, which the employee owns and so may
	create. Linking it here keeps it off the orphan list and lets HR read it.
	"""
	if isinstance(documents, str):
		documents = json.loads(documents)
	if not documents:
		return

	by_idx = {int(row["idx"]): row.get("attachment") for row in documents if row.get("idx")}

	for row in doc.documents:
		attachment = by_idx.get(row.idx)
		if attachment is None or attachment == row.attachment:
			continue

		frappe.db.set_value("Employee Onboarding Document", row.name, "attachment", attachment)
		attach_file_to_onboarding(doc, attachment)


def attach_file_to_onboarding(doc: "frappe.Document", file_url: str) -> None:
	file_name = frappe.db.get_value("File", {"file_url": file_url, "attached_to_name": ["is", "not set"]})
	if not file_name:
		return

	frappe.db.set_value(
		"File",
		file_name,
		{"attached_to_doctype": doc.doctype, "attached_to_name": doc.name},
		update_modified=False,
	)


def parse_details(submitted_details: str | None) -> dict:
	if not submitted_details:
		return {}

	try:
		return json.loads(submitted_details)
	except json.JSONDecodeError:
		return {}


def seed_details(doc: "frappe.Document") -> dict:
	"""Pre-fill what HR already knows, so the employee is not retyping it."""
	from hrms.hr.doctype.employee_onboarding.employee_onboarding import split_full_name

	first_name, middle_name, last_name = split_full_name(doc.employee_name)

	return {
		"first_name": first_name,
		"middle_name": middle_name,
		"last_name": last_name,
		"gender": doc.gender,
		"date_of_birth": doc.date_of_birth,
		"personal_email": doc.personal_email,
		"education": [],
		"external_work_history": [],
	}
