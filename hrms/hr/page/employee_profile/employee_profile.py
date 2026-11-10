"""The employee profile: one person's page in the company directory.

Everyone who may see the organizational chart of a company may see the public part of each profile
in it: the directory fields and what the person wrote about themselves. The private part (personal,
employment, bank and assets) is only for those who may read that Employee record, which is the
person themselves and HR.

The public part is written by the person only. In the private part the person changes their own
personal details and raises requests; those who may write the Employee record, HR, change the rest,
and those who may submit a request approve or reject it, though never their own.
"""

import json
import re
from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.core.doctype.access_log.access_log import make_access_log
from frappe.model.document import Document
from frappe.query_builder.functions import Max
from frappe.utils import (
	add_days,
	cint,
	date_diff,
	get_fullname,
	getdate,
	month_diff,
	now_datetime,
	today,
	validate_email_address,
	validate_phone_number,
)

from hrms.hr.page.organizational_chart.organizational_chart import get_allowed_companies, get_leave_status
from hrms.overrides.employee_master import get_retirement_date
from hrms.utils.holiday_list import get_holiday_list_for_employee

PAGE = "employee-profile"
SECTION_TYPES = ("Cover", "Headline", "Text", "Tags", "Photos", "Links")
# the most a person can write, so a profile stays a profile
MAX_SECTIONS = 20
MAX_TEXT = 5000
MAX_TITLE = 140
MAX_ITEMS = 12

CARD_FIELDS = [
	"name",
	"employee_name",
	"image",
	"designation",
	"department.department_name as department",
	"branch",
	"company",
	"company_email",
	"reports_to",
	"date_of_joining",
	"date_of_birth",
	"user_id",
	"status",
]
PERSONAL_FIELDS = ["date_of_birth", "gender", "blood_group", "marital_status"]
CONTACT_FIELDS = ["cell_number", "personal_email", "current_address", "permanent_address"]
EMERGENCY_FIELDS = ["person_to_be_contacted", "emergency_phone_number", "relation"]
EMPLOYMENT_FIELDS = [
	"date_of_joining",
	"employment_type",
	"grade",
	"default_shift",
	"notice_number_of_days",
]
BANK_FIELDS = ["bank_name", "bank_ac_no", "iban"]
PHONE_FIELDS = ("cell_number", "emergency_phone_number")
# what an employee may change about themselves; HR keeps the rest
SELF_EDITABLE = [
	*PERSONAL_FIELDS,
	*CONTACT_FIELDS,
	*EMERGENCY_FIELDS,
]
# what HR changes besides, on the Personal, Employment and Bank account tabs
HR_EDITABLE = ["department", "branch", *EMPLOYMENT_FIELDS, *BANK_FIELDS, "ifsc_code"]
REQUESTS = ("Bank Details Change Request", "Asset Request")
# options for the Link fields HR picks from; masters, so a few hundred at most
MAX_OPTIONS = 500
# how long a decided request stays on the profile: an approved one with its steps, a rejected one
# with HR's reason
DECIDED_DAYS = 30


@frappe.whitelist()
def get_profile(employee: str | None = None) -> dict:
	"""The profile of `employee`, or of the user's own employee when none is given"""
	employee = employee or get_user_employee()
	if not employee:
		frappe.throw(_("You do not have an employee record"), frappe.DoesNotExistError)

	person = get_person(employee)
	if not person:
		frappe.throw(_("Employee {0} not found").format(frappe.bold(employee)), frappe.DoesNotExistError)
	# those who may read the record, the person and HR, see all of it, also after the person left
	private = frappe.has_permission("Employee", "read", doc=employee)
	if not private:
		check_access(person)

	is_self = bool(person.user_id) and person.user_id == frappe.session.user
	can_manage = private and frappe.has_permission("Employee", "write", doc=employee)
	profile = {
		"card": get_card(person, private),
		"sections": get_sections(employee),
		"is_self": is_self,
		# the public part is the person's own words, so only they write it
		"can_edit": is_self,
		"can_edit_details": is_self or can_manage,
		"can_manage": can_manage,
		"can_open_record": private,
	}
	if private:
		profile["private"] = get_private(employee)
		profile["can_review"] = {
			doctype: not is_self and bool(frappe.has_permission(doctype, "submit")) for doctype in REQUESTS
		}
		# HR gives an asset with an Asset Movement, as for an approved request
		profile["can_assign_assets"] = not is_self and bool(frappe.has_permission("Asset Movement", "create"))
	if is_self or can_manage:
		profile["options"] = get_options(person.company, can_manage)
	return profile


def get_person(employee: str) -> frappe._dict | None:
	person = frappe.get_all("Employee", filters={"name": employee}, fields=CARD_FIELDS, limit=1)
	return person[0] if person else None


def get_options(company: str, can_manage: bool) -> dict:
	"""The choices of the fields the user may change on this profile"""
	meta = frappe.get_meta("Employee")
	options = {
		field: [option for option in (meta.get_field(field).options or "").split("\n") if option]
		for field in ("blood_group", "marital_status")
	}
	options["gender"] = frappe.get_all("Gender", pluck="name", order_by="name")
	options["asset_categories"] = frappe.get_all("Asset Category", pluck="name", order_by="name")
	options["document_types"] = frappe.get_all(
		"Employee Document Type", fields=["name", "has_number", "has_expiry"], order_by="name"
	)
	if can_manage:
		for field in ("branch", "employment_type", "grade", "default_shift"):
			options[field] = frappe.get_all(
				meta.get_field(field).options, pluck="name", order_by="name", limit=MAX_OPTIONS
			)
		options["department"] = frappe.get_all(
			"Department",
			filters={"company": company, "is_group": 0},
			fields=["name as value", "department_name as label"],
			order_by="department_name",
			limit=MAX_OPTIONS,
		)
	return options


def check_access(person: frappe._dict):
	"""The public profile is for desk users who may see the organizational chart of its company"""
	# a page without roles is open to everyone, portal users included
	if frappe.get_cached_value("User", frappe.session.user, "user_type") != "System User" or (
		not frappe.get_cached_doc("Page", PAGE).is_permitted()
	):
		frappe.throw(_("You do not have access to employee profiles"), frappe.PermissionError)
	if person.status != "Active" or person.company not in get_allowed_companies():
		frappe.throw(_("You do not have access to this profile"), frappe.PermissionError)


def get_card(person: frappe._dict, private: bool) -> dict:
	manager = (
		frappe.db.get_value(
			"Employee",
			{"name": person.reports_to, "status": "Active"},
			["name as id", "employee_name as name", "image"],
			as_dict=True,
		)
		if person.reports_to
		else None
	)
	return {
		"id": person.name,
		"name": person.employee_name,
		"image": person.image,
		"designation": person.designation,
		"department": person.department,
		"branch": person.branch,
		"company": person.company,
		"email": person.company_email,
		"manager": manager,
		"reports": frappe.db.count("Employee", {"reports_to": person.name, "status": "Active"}),
		"tenure": get_tenure(person.date_of_joining),
		# the reminders already tell the whole company; only the day, never the year
		"birthday": get_birthday(person.date_of_birth)
		if private or cint(frappe.db.get_single_value("HR Settings", "send_birthday_reminders"))
		else None,
		"leave": get_leave_status({person.name: person.company}).get(person.name),
	}


def get_tenure(date_of_joining) -> dict | None:
	"""How long someone has been with the company, in whole years, or months in their first year"""
	if not date_of_joining or getdate(date_of_joining) > getdate():
		return None
	months = month_diff(getdate(), date_of_joining) - 1
	if months >= 12:
		return {"years": months // 12}
	return {"months": max(months, 0), "days": date_diff(getdate(), date_of_joining)}


def get_birthday(date_of_birth) -> dict | None:
	if not date_of_birth:
		return None
	day = getdate(date_of_birth)
	return {"month": day.month, "day": day.day}


def get_sections(employee: str) -> list[dict]:
	return [
		{"type": row.section_type, "title": row.title, "content": parse_content(row)}
		for row in frappe.get_all(
			"Employee Profile Section",
			filters={"parent": employee, "parenttype": "Employee", "parentfield": "profile_sections"},
			fields=["section_type", "title", "content"],
			order_by="idx",
		)
	]


def parse_content(row: frappe._dict):
	if row.section_type == "Tags":
		return [tag.strip() for tag in (row.content or "").splitlines() if tag.strip()]
	if row.section_type in ("Photos", "Links"):
		try:
			items = json.loads(row.content or "[]")
		except ValueError:
			return []
		return items if isinstance(items, list) else []
	return row.content or ""


def get_private(employee: str) -> dict:
	bank_fields = get_bank_fields()
	values = frappe.db.get_value(
		"Employee",
		employee,
		[
			*PERSONAL_FIELDS,
			*CONTACT_FIELDS,
			*EMERGENCY_FIELDS,
			*EMPLOYMENT_FIELDS,
			"department",
			"branch",
			*bank_fields,
		],
		as_dict=True,
	)
	pick = lambda fields: {field: values.get(field) for field in fields}  # noqa: E731
	bank = pick(bank_fields)
	# the profile shows which account, not the whole number
	bank["bank_ac_no"] = mask(bank["bank_ac_no"])
	bank["iban"] = mask(bank["iban"])
	return {
		"personal": pick(PERSONAL_FIELDS),
		"contact": pick(CONTACT_FIELDS),
		"emergency": pick(EMERGENCY_FIELDS),
		"employment": {
			**pick([*EMPLOYMENT_FIELDS, "department", "branch"]),
			# HR sets it through Holiday List Assignment, for the employee or their company
			"holiday_list": get_holiday_list_for_employee(employee, raise_exception=False),
		},
		"bank": bank,
		"bank_request": get_open_bank_request(employee),
		"bank_decided": get_decided_bank_request(employee),
		"assets": get_assets(employee),
		"asset_requests": get_asset_requests(employee),
		"documents": get_documents(employee),
	}


def get_asset_requests(employee: str) -> list[dict]:
	"""The employee's open asset requests, the approved ones whose Asset Movement, which HR makes
	from the request, is not submitted yet, and the ones rejected lately, with the reason"""
	fields = [
		"name",
		"request_type",
		"status",
		"asset_category",
		"asset",
		"asset_name",
		"required_by",
		"reason",
		"rejection_reason",
		"creation",
		"modified",
	]
	requests = frappe.get_all(
		"Asset Request",
		filters={"employee": employee, "docstatus": 0},
		fields=fields,
		order_by="creation desc",
	)
	approved = frappe.get_all(
		"Asset Request",
		filters={"employee": employee, "docstatus": 1, "status": "Approved"},
		fields=fields,
		order_by="creation desc",
		limit=20,
	)
	rejected = get_rejected("Asset Request", employee, fields)
	if not approved:
		return requests + rejected
	movements = {}
	for movement in frappe.get_all(
		"Asset Movement",
		filters={
			"reference_doctype": "Asset Request",
			"reference_name": ["in", [request.name for request in approved]],
			"docstatus": ["!=", 2],
		},
		fields=["name", "reference_name", "docstatus"],
	):
		movements[movement.reference_name] = movement
	for request in approved:
		movement = movements.get(request.name)
		if movement and movement.docstatus == 1:
			continue
		request.asset_movement = movement.name if movement else None
		requests.append(request)
	return requests + rejected


def get_rejected(doctype: str, employee: str, fields: list[str], limit: int = 20) -> list[dict]:
	"""The employee's requests HR rejected lately; `modified` is when HR decided"""
	return frappe.get_all(
		doctype,
		filters={
			"employee": employee,
			"docstatus": 1,
			"status": "Rejected",
			"modified": [">=", add_days(now_datetime(), -DECIDED_DAYS)],
		},
		fields=fields,
		order_by="modified desc",
		limit=limit,
	)


def get_bank_fields() -> list[str]:
	# the India regional setup adds the IFSC code
	return [*BANK_FIELDS, "ifsc_code"] if frappe.get_meta("Employee").has_field("ifsc_code") else BANK_FIELDS


BANK_REQUEST_FIELDS = [
	"name",
	"status",
	"bank_name",
	"bank_ac_no",
	"ifsc_code",
	"iban",
	"reason",
	"proof",
	"rejection_reason",
	"creation",
	"modified",
	"modified_by",
]


def get_open_bank_request(employee: str) -> dict | None:
	request = frappe.db.get_value(
		"Bank Details Change Request",
		{"employee": employee, "docstatus": 0},
		BANK_REQUEST_FIELDS,
		as_dict=True,
	)
	return prepare_bank_request(request) if request else None


def get_decided_bank_request(employee: str) -> dict | None:
	"""The last change HR approved or rejected lately, while no new one is open, so the employee
	and HR still see how it went"""
	if frappe.db.exists("Bank Details Change Request", {"employee": employee, "docstatus": 0}):
		return None
	decided = frappe.get_all(
		"Bank Details Change Request",
		filters={
			"employee": employee,
			"docstatus": 1,
			"modified": [">=", add_days(now_datetime(), -DECIDED_DAYS)],
		},
		fields=BANK_REQUEST_FIELDS,
		order_by="modified desc",
		limit=1,
	)
	if not decided:
		return None
	# `modified` is when HR decided, as the request is not changed after that
	decided_by = get_fullname(decided[0].modified_by)
	request = prepare_bank_request(decided[0])
	request.decided_by = decided_by
	return request


def prepare_bank_request(request: frappe._dict) -> frappe._dict:
	request.bank_ac_no = mask(request.bank_ac_no)
	request.iban = mask(request.iban)
	request.proof_name = frappe.db.get_value(
		"File",
		{
			"file_url": request.proof,
			"attached_to_doctype": "Bank Details Change Request",
			"attached_to_name": request.name,
		},
		"file_name",
	)
	request.pop("modified_by", None)
	return request


@frappe.whitelist()
def get_bank_number(employee: str, request: str | None = None) -> dict:
	"""The whole account number and IBAN, which the profile shows only the end of: of the
	employee's account, or of a change they asked for, so HR can check it against the proof. For
	the employee and for HR, and each look is kept in the Access Log."""
	if request:
		doc = frappe.get_doc("Bank Details Change Request", request)
		doc.check_permission("read")
		if doc.employee != employee:
			frappe.throw(_("{0} is not a request of {1}").format(request, employee), frappe.PermissionError)
		values = {"bank_ac_no": doc.bank_ac_no, "iban": doc.iban}
		make_access_log(doctype=doc.doctype, document=doc.name, method="get_bank_number")
	else:
		if not frappe.has_permission("Employee", "read", doc=employee):
			frappe.throw(_("Not permitted to see this bank account"), frappe.PermissionError)
		values = frappe.db.get_value("Employee", employee, ["bank_ac_no", "iban"], as_dict=True)
		make_access_log(doctype="Employee", document=employee, method="get_bank_number")
	return values


def get_assets(employee: str) -> list[dict]:
	"""What the employee holds, and since when: the last Asset Movement that gave it to them"""
	assets = frappe.get_all(
		"Asset",
		filters={"custodian": employee, "docstatus": 1},
		fields=["name", "asset_name", "item_name", "asset_category"],
		limit=50,
	)
	if not assets:
		return []
	movement = frappe.qb.DocType("Asset Movement")
	item = frappe.qb.DocType("Asset Movement Item")
	since = dict(
		frappe.qb.from_(item)
		.join(movement)
		.on(item.parent == movement.name)
		.select(item.asset, Max(movement.transaction_date))
		.where(
			(movement.docstatus == 1)
			& (item.to_employee == employee)
			& (item.asset.isin([asset.name for asset in assets]))
		)
		.groupby(item.asset)
		.run()
	)
	for asset in assets:
		asset.since = since.get(asset.name)
	return sorted(assets, key=lambda asset: str(asset.since or ""), reverse=True)


def get_documents(employee: str) -> list[dict]:
	"""The employee's documents, and the required ones they have not given yet"""
	types = {
		document.name: document
		for document in frappe.get_all(
			"Employee Document Type", fields=["name", "is_required", "has_number", "has_expiry"]
		)
	}
	documents = frappe.get_all(
		"Employee Document",
		filters={"parent": employee, "parenttype": "Employee", "parentfield": "documents"},
		fields=[
			"document_type",
			"attachment",
			"document_number",
			"expiry_date",
			"status",
			"verified_on",
			"due_date",
			"remarks",
		],
		order_by="idx",
	)
	given = {document.document_type for document in documents}
	documents += [
		{"document_type": name, "status": "Missing"}
		for name, document in types.items()
		if document.is_required and name not in given
	]
	for document in documents:
		kind = types.get(document["document_type"]) or {}
		document["has_number"] = kind.get("has_number")
		document["has_expiry"] = kind.get("has_expiry")
	return documents


def mask(number: str | None) -> str | None:
	return f"••••{number[-4:]}" if number else None


def get_user_employee() -> str | None:
	return frappe.db.get_value("Employee", {"user_id": frappe.session.user, "status": "Active"}, "name")


def get_own_employee() -> str:
	"""The session user's employee. Nobody edits another person's profile here."""
	employee = get_user_employee()
	if not employee:
		frappe.throw(_("You do not have an employee record"), frappe.PermissionError)
	return employee


def can_manage_employee(employee: str | None) -> bool:
	"""Whether the user may change this employee's record, as HR does, beyond their own details"""
	if not employee:
		frappe.throw(_("You do not have an employee record"), frappe.PermissionError)
	can_manage = frappe.has_permission("Employee", "write", doc=employee)
	if not can_manage and employee != get_user_employee():
		frappe.throw(_("You cannot change this employee's details"), frappe.PermissionError)
	return can_manage


@frappe.whitelist(methods=["POST"])
def save_details(values: dict | str, employee: str | None = None) -> dict:
	"""Update an employee's details, the listed fields only: an employee their own personal and
	contact details, HR also the employment and bank details"""
	employee = employee or get_user_employee()
	can_manage = can_manage_employee(employee)
	values = frappe.parse_json(values)
	if not isinstance(values, dict):
		frappe.throw(_("Details must be a set of fields"))
	unknown = set(values) - set((SELF_EDITABLE + HR_EDITABLE) if can_manage else SELF_EDITABLE)
	if unknown:
		frappe.throw(_("You cannot change {0} here").format(", ".join(sorted(unknown))))

	doc = frappe.get_doc("Employee", employee)
	meta = frappe.get_meta("Employee")
	for field, value in values.items():
		df = meta.get_field(field)
		if not df:
			frappe.throw(_("You cannot change {0} here").format(field))
		doc.set(field, clean_value(doc, df, value))
	if values.get("bank_ac_no"):
		doc.salary_mode = "Bank"

	if can_manage:
		doc.save()
	else:
		# The Employee role may read its own record but not write it. Only the listed fields
		# change, the employee is the session user, and Employee tracks changes, so HR sees each
		# edit.
		doc.save(ignore_permissions=True)
	return {"private": get_private(employee), "card": get_card(get_person(employee), True)}


def clean_value(doc, df, value):
	value = str(value or "").strip()[:MAX_TEXT] or None
	if not value:
		return 0 if df.fieldtype == "Int" else None
	if df.fieldtype == "Select" and value not in (df.options or "").split("\n"):
		frappe.throw(_("{0} is not a valid {1}").format(frappe.bold(value), _(df.label)))
	if df.fieldtype == "Link" and not frappe.db.exists(df.options, value):
		frappe.throw(_("{0} is not a valid {1}").format(frappe.bold(value), _(df.label)))
	if df.fieldname == "department" and frappe.db.get_value("Department", value, "company") != doc.company:
		frappe.throw(_("Department {0} is not in {1}").format(frappe.bold(value), frappe.bold(doc.company)))
	if df.fieldname == "personal_email":
		validate_email_address(value, throw=True)
	if df.fieldname in PHONE_FIELDS:
		validate_phone_number(value, throw=True)
		if not 7 <= len(re.sub(r"\D", "", value)) <= 15:
			frappe.throw(_("{0} must have 7 to 15 digits").format(_(df.label)))
	if df.fieldtype == "Int":
		if not value.isdigit():
			frappe.throw(_("{0} must be a whole number").format(_(df.label)))
		return cint(value)
	if df.fieldtype == "Date":
		value = getdate(value)
	if df.fieldname == "date_of_birth":
		# as the Employee form does when the date of birth changes
		doc.date_of_retirement = get_retirement_date(str(value))
	return value


@frappe.whitelist(methods=["POST"])
def save_sections(sections: list | str) -> list[dict]:
	"""Replace the user's own profile sections"""
	employee = get_own_employee()
	sections = frappe.parse_json(sections)
	if not isinstance(sections, list):
		frappe.throw(_("Profile sections must be a list"))

	rows = [clean_section(section, employee) for section in sections[: MAX_SECTIONS + 1]]
	if len(rows) > MAX_SECTIONS:
		frappe.throw(_("A profile can have at most {0} sections").format(MAX_SECTIONS))

	doc = frappe.get_doc("Employee", employee)
	doc.set("profile_sections", rows)
	# The Employee role may read its own record but not write it. Only the profile sections change
	# here, the employee is the session user, and Employee tracks changes, so HR sees each edit.
	doc.save(ignore_permissions=True)
	return get_sections(employee)


def clean_section(section: dict, employee: str) -> dict:
	if not isinstance(section, dict) or section.get("type") not in SECTION_TYPES:
		frappe.throw(_("Unknown profile section"))

	kind = section["type"]
	title = str(section.get("title") or "")[:MAX_TITLE]
	content = section.get("content")
	if kind == "Cover":
		content = clean_photo({"image": content}, employee)["image"]
	elif kind in ("Headline", "Text"):
		content = str(content or "")[:MAX_TEXT]
	elif kind == "Tags":
		tags = [str(tag).strip()[:60] for tag in (content or []) if str(tag).strip()]
		content = "\n".join(tags[:30])
	elif kind == "Links":
		content = json.dumps([clean_link(item) for item in (content or [])[:MAX_ITEMS]])
	else:
		content = json.dumps([clean_photo(item, employee) for item in (content or [])[:MAX_ITEMS]])
	return {"section_type": kind, "title": title, "content": content}


def clean_link(item: dict) -> dict:
	url = str((item or {}).get("url") or "").strip()
	if urlparse(url).scheme not in ("http", "https"):
		frappe.throw(_("Links must start with http:// or https://"))
	return {
		"title": str(item.get("title") or url)[:MAX_TITLE],
		"url": url[:1000],
		"note": str(item.get("note") or "")[:MAX_TITLE],
	}


def clean_photo(item: dict, employee: str) -> dict:
	image = str((item or {}).get("image") or "")
	if not frappe.db.exists(
		"File", {"file_url": image, "attached_to_doctype": "Employee", "attached_to_name": employee}
	):
		attach_file(get_own_upload(image), "Employee", employee)
	return {"image": image, "caption": str(item.get("caption") or "")[:MAX_TITLE]}


def get_own_upload(file_url: str) -> str:
	"""The File the session user uploaded and nothing holds yet. The profile uploads files on their
	own, because an employee may not write their record, and attaches them once they are used."""
	file = frappe.db.get_value(
		"File",
		{
			"file_url": str(file_url or ""),
			"owner": frappe.session.user,
			"attached_to_doctype": ["is", "not set"],
			"is_folder": 0,
		},
		"name",
	)
	if not file:
		frappe.throw(_("Files must be uploaded from your profile"))
	return file


def attach_file(file: str, doctype: str, name: str, field: str | None = None):
	frappe.db.set_value(
		"File",
		file,
		{"attached_to_doctype": doctype, "attached_to_name": name, "attached_to_field": field},
	)


@frappe.whitelist(methods=["POST"])
def request_bank_details_change(values: dict | str, name: str | None = None) -> dict:
	"""Ask HR to change the user's own salary account, or change the open request named. HR
	approves it in the request. The profile shows only the end of the numbers asked for, so a
	change that leaves one empty keeps it."""
	employee = get_own_employee()
	values = frappe.parse_json(values)
	if not isinstance(values, dict):
		frappe.throw(_("Bank details must be a set of fields"))
	if name:
		request = get_own_open_request("Bank Details Change Request", name, employee)
	else:
		request = frappe.get_doc({"doctype": "Bank Details Change Request", "employee": employee})

	for field in ("bank_name", "bank_ac_no", "ifsc_code", "iban"):
		value = str(values.get(field) or "").strip()[:MAX_TITLE] or None
		if value or not name or field not in ("bank_ac_no", "iban"):
			request.set(field, value)
	request.reason = str(values.get("reason") or "").strip()[:MAX_TEXT] or None

	# a new proof is the user's own upload; the one already on the request stays
	proof = None
	if not name or values.get("proof") != request.proof:
		proof = get_own_upload(values.get("proof"))
		request.proof = values.get("proof")

	request.save()
	if proof:
		attach_file(proof, request.doctype, request.name, "proof")
	return get_private(employee)


@frappe.whitelist(methods=["POST"])
def request_asset(values: dict | str, name: str | None = None) -> dict:
	"""Ask for an asset, or to return one the user holds, or change the open request named. HR
	approves it in the request. A change keeps what is asked for: the kind of request, and the
	asset to return."""
	employee = get_own_employee()
	values = frappe.parse_json(values)
	if not isinstance(values, dict):
		frappe.throw(_("Asset request must be a set of fields"))
	if name:
		request = get_own_open_request("Asset Request", name, employee)
	elif values.get("request_type") in ("Issue", "Return"):
		is_issue = values["request_type"] == "Issue"
		request = frappe.get_doc(
			{
				"doctype": "Asset Request",
				"employee": employee,
				"request_type": values["request_type"],
				"asset": None if is_issue else str(values.get("asset") or "") or None,
			}
		)
	else:
		frappe.throw(_("Choose whether to request or return an asset"))

	if request.request_type == "Issue":
		request.asset_category = str(values.get("asset_category") or "") or None
		request.required_by = getdate(values["required_by"]) if values.get("required_by") else None
	request.reason = str(values.get("reason") or "").strip()[:MAX_TEXT] or None
	request.save()
	return get_private(employee)


@frappe.whitelist(methods=["POST"])
def withdraw_request(doctype: str, name: str) -> dict:
	"""Take back the user's own open request. It is discarded, as a draft is, so it stays, as
	Cancelled, and HR sees it was made."""
	if doctype not in REQUESTS:
		frappe.throw(_("Only bank details and asset requests can be withdrawn here"))
	employee = get_own_employee()
	get_own_open_request(doctype, name, employee).discard()
	return get_private(employee)


def get_own_open_request(doctype: str, name: str, employee: str) -> Document:
	"""The user's own request that HR has not decided yet: only that one can be changed or taken back"""
	request = frappe.get_doc(doctype, name)
	if request.employee != employee or not request.docstatus.is_draft() or request.status != "Open":
		frappe.throw(_("Only your own open requests can be changed"), frappe.PermissionError)
	return request


@frappe.whitelist(methods=["POST"])
def review_request(doctype: str, name: str, status: str, reason: str | None = None) -> dict:
	"""Approve or reject an open request and submit it. Approving a bank details change updates the
	employee's account; an approved asset request waits for its Asset Movement. A rejection says
	why, and the employee sees it."""
	if doctype not in REQUESTS or status not in ("Approved", "Rejected"):
		frappe.throw(_("Only bank details and asset requests can be approved or rejected here"))
	request = frappe.get_doc(doctype, name)
	request.check_permission("submit")
	if request.docstatus != 0 or request.status != "Open":
		frappe.throw(_("{0} is no longer open").format(frappe.bold(request.name)), title=_("Request Closed"))
	if request.employee == get_user_employee():
		frappe.throw(_("You cannot approve or reject your own request"), frappe.PermissionError)
	request.status = status
	if status == "Rejected":
		request.rejection_reason = str(reason or "").strip()[:MAX_TEXT] or None
		if not request.rejection_reason:
			frappe.throw(_("Say why the request is rejected, so {0} knows").format(request.employee_name))
	request.submit()
	return get_private(request.employee)


@frappe.whitelist(methods=["POST"])
def upload_document(
	document_type: str,
	file_url: str,
	document_number: str | None = None,
	expiry_date: str | None = None,
	employee: str | None = None,
) -> dict:
	"""Put a document on an employee's record. One the employee uploads counts once HR verifies it;
	one HR uploads for them is verified already."""
	employee = employee or get_user_employee()
	can_manage = can_manage_employee(employee)
	document = frappe.get_cached_doc("Employee Document Type", document_type)
	file = get_own_upload(file_url)

	doc = frappe.get_doc("Employee", employee)
	row = get_document_row(doc, document.name) or doc.append("documents", {"document_type": document.name})
	row.attachment = file_url
	row.document_number = (
		str(document_number or "").strip()[:MAX_TITLE] or None if document.has_number else None
	)
	row.expiry_date = getdate(expiry_date) if expiry_date and document.has_expiry else None
	row.status = "Verified" if can_manage and employee != get_user_employee() else "Submitted"
	if row.status == "Verified":
		row.verified_on = today()
	row.remarks = None
	if can_manage:
		doc.save()
	else:
		# The Employee role may read its own record but not write it. Only this document row
		# changes, always to Submitted, and Employee tracks changes, so HR sees each upload before
		# verifying it.
		doc.save(ignore_permissions=True)
	attach_file(file, "Employee", employee, "documents")
	return get_private(employee)


@frappe.whitelist(methods=["POST"])
def review_document(employee: str, document_type: str, status: str, remarks: str | None = None) -> dict:
	"""Verify a document the employee uploaded, or send it back to them with what is wrong"""
	if status not in ("Verified", "Rejected"):
		frappe.throw(_("A document can only be verified or rejected"))
	doc = frappe.get_doc("Employee", employee)
	doc.check_permission("write")
	if employee == get_user_employee():
		frappe.throw(_("You cannot verify your own documents"), frappe.PermissionError)
	row = get_document_row(doc, document_type)
	if not row or not row.attachment:
		frappe.throw(
			_("{0} has not uploaded {1}").format(frappe.bold(doc.employee_name), frappe.bold(document_type))
		)
	row.status = status
	if status == "Verified":
		row.verified_on = today()
	row.remarks = str(remarks or "").strip()[:MAX_TEXT] or None
	doc.save()
	return get_private(employee)


@frappe.whitelist(methods=["POST"])
def request_document(employee: str, document_type: str, due_date: str | None = None) -> dict:
	"""Ask the employee for a document, by a date if given"""
	doc = frappe.get_doc("Employee", employee)
	doc.check_permission("write")
	document = frappe.get_cached_doc("Employee Document Type", document_type)
	row = get_document_row(doc, document.name) or doc.append("documents", {"document_type": document.name})
	row.status = "Pending"
	row.due_date = getdate(due_date) if due_date else None
	row.remarks = None
	doc.save()
	return get_private(employee)


@frappe.whitelist(methods=["POST"])
def remove_document(document_type: str, employee: str | None = None) -> dict:
	"""Take a document off an employee's record. The employee takes back their own upload until HR
	verifies it: one HR asked for by a date goes back to asked for, and a required one shows as
	required again. HR removes any."""
	own = get_user_employee()
	employee = employee or get_own_employee()
	doc = frappe.get_doc("Employee", employee)
	row = get_document_row(doc, document_type)
	if not row:
		frappe.throw(_("{0} is not on the record").format(frappe.bold(document_type)))

	if employee != own:
		doc.check_permission("write")
		doc.remove(row)
		doc.save()
		return get_private(employee)

	# once HR has verified it, a newer upload replaces it, so taking that back would lose both
	if row.status not in ("Submitted", "Rejected") or row.verified_on:
		frappe.throw(
			_("HR has verified {0}. Ask HR to remove it.").format(frappe.bold(document_type)),
			frappe.PermissionError,
		)
	if row.due_date:
		row.update(
			{
				"attachment": None,
				"document_number": None,
				"expiry_date": None,
				"status": "Pending",
				"remarks": None,
			}
		)
	else:
		doc.remove(row)
	# as with an upload: only this row of the user's own record changes, and Employee tracks changes
	doc.save(ignore_permissions=True)
	return get_private(employee)


def get_document_row(doc, document_type: str):
	return next((row for row in doc.documents if row.document_type == document_type), None)
