"""One engine for every document an employee raises about themselves.

Expense claims, leave applications, attendance regularisations and advances all
obey the same three rules: you only ever see your own, you may only change it
while it is a draft, and submitting belongs to the approver. Only the field set
differs, so that is the only thing REQUEST_TYPES describes.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate

from hrms.api import get_current_employee
from hrms.api.portal import MAX_ATTACHMENTS, _validated_attachments


def _employee_row(employee: str):
	return frappe.db.get_value(
		"Employee",
		employee,
		["company", "expense_approver", "leave_approver", "salary_currency"],
		as_dict=True,
	)


# --- option sources, resolved server side so the client stays type-agnostic ---


def _leave_type_options(employee: str) -> list[str]:
	allocated = frappe.get_all(
		"Leave Allocation",
		filters={"employee": employee, "docstatus": 1, "to_date": [">=", nowdate()]},
		pluck="leave_type",
	)
	return sorted(set(allocated)) or frappe.get_all("Leave Type", pluck="name", limit=20)


def _expense_type_options(employee: str) -> list[str]:
	return frappe.get_all("Expense Claim Type", pluck="name", limit=50)


def _attendance_reason_options(employee: str) -> list[str]:
	df = frappe.get_meta("Attendance Request").get_field("reason")
	return [o for o in (df.options or "").split("\n") if o]


OPTION_SOURCES = {
	"leave_types": _leave_type_options,
	"expense_types": _expense_type_options,
	"attendance_reasons": _attendance_reason_options,
}


# --- per type defaults -------------------------------------------------------


def _leave_defaults(employee: str, emp) -> dict:
	return {
		"company": emp.company,
		"leave_approver": emp.leave_approver,
		"posting_date": nowdate(),
		"status": "Open",
	}


def _expense_defaults(employee: str, emp) -> dict:
	company_currency = frappe.db.get_value("Company", emp.company, "default_currency")
	currency = emp.salary_currency or company_currency
	from hrms.api.portal import _exchange_rate

	return {
		"company": emp.company,
		"expense_approver": emp.expense_approver,
		"posting_date": nowdate(),
		"currency": currency,
		"exchange_rate": _exchange_rate(currency, company_currency, nowdate()),
	}


def _attendance_defaults(employee: str, emp) -> dict:
	return {"company": emp.company}


def _advance_defaults(employee: str, emp) -> dict:
	company_currency = frappe.db.get_value("Company", emp.company, "default_currency")
	return {
		"company": emp.company,
		"posting_date": nowdate(),
		"currency": company_currency,
		"exchange_rate": 1,
	}


# --- per type summaries shown on the detail page -----------------------------


def _money(value, currency):
	return {"value": flt(value), "currency": currency, "kind": "money"}


def _leave_summary(doc) -> list[dict]:
	return [
		{"label": "Leave Type", "value": doc.leave_type},
		{"label": "From Date", "value": str(doc.from_date) if doc.from_date else None, "kind": "date"},
		{"label": "To Date", "value": str(doc.to_date) if doc.to_date else None, "kind": "date"},
		{"label": "Days", "value": flt(doc.total_leave_days, 1)},
	]


def _expense_summary(doc) -> list[dict]:
	rows = [{"label": "Claimed", **_money(doc.total_claimed_amount, doc.currency)}]
	if doc.docstatus != 0:
		rows.append({"label": "Sanctioned", **_money(doc.total_sanctioned_amount, doc.currency)})
	if flt(doc.total_amount_reimbursed):
		rows.append({"label": "Reimbursed", **_money(doc.total_amount_reimbursed, doc.currency)})
	return rows


def _attendance_summary(doc) -> list[dict]:
	return [
		{"label": "Reason", "value": doc.reason},
		{"label": "From Date", "value": str(doc.from_date) if doc.from_date else None, "kind": "date"},
		{"label": "To Date", "value": str(doc.to_date) if doc.to_date else None, "kind": "date"},
	]


def _advance_summary(doc) -> list[dict]:
	rows = [{"label": "Requested", **_money(doc.advance_amount, doc.currency)}]
	if flt(doc.paid_amount):
		rows.append({"label": "Paid", **_money(doc.paid_amount, doc.currency)})
	if flt(doc.claimed_amount):
		rows.append({"label": "Claimed Against", **_money(doc.claimed_amount, doc.currency)})
	return rows


REQUEST_TYPES = {
	"leave": {
		"doctype": "Leave Application",
		"label": "Leave Application",
		"list_route": "/leave",
		"approver_field": "leave_approver",
		"attachments": False,
		"defaults": _leave_defaults,
		"summary": _leave_summary,
		"fields": [
			{
				"fieldname": "leave_type",
				"label": "Leave Type",
				"type": "select",
				"options": "leave_types",
				"required": True,
				"full": True,
			},
			{"fieldname": "from_date", "label": "From Date", "type": "date", "required": True},
			{"fieldname": "to_date", "label": "To Date", "type": "date", "required": True},
			{"fieldname": "half_day", "label": "Half Day", "type": "checkbox", "full": True},
			{
				"fieldname": "description",
				"label": "Reason",
				"type": "textarea",
				"placeholder": "Anything your approver should know",
				"full": True,
			},
		],
	},
	"expense": {
		"doctype": "Expense Claim",
		"label": "Expense Claim",
		"list_route": "/expenses",
		"approver_field": "expense_approver",
		"currency_field": "currency",
		"attachments": True,
		"defaults": _expense_defaults,
		"summary": _expense_summary,
		"fields": [
			{
				"fieldname": "expenses",
				"label": "Expenses",
				"type": "table",
				"required": True,
				"row_label": "Expense",
				"fields": [
					{
						"fieldname": "expense_type",
						"label": "Type",
						"type": "select",
						"options": "expense_types",
						"required": True,
					},
					{"fieldname": "amount", "label": "Amount", "type": "number", "required": True},
					{
						"fieldname": "expense_date",
						"label": "Date of expense",
						"type": "date",
						"required": True,
					},
					{
						"fieldname": "description",
						"label": "Description",
						"type": "text",
						"placeholder": "What was this for?",
						"full": True,
					},
				],
			}
		],
	},
	"attendance": {
		"doctype": "Attendance Request",
		"label": "Attendance Request",
		"list_route": "/attendance",
		"attachments": False,
		"defaults": _attendance_defaults,
		"summary": _attendance_summary,
		"fields": [
			{
				"fieldname": "reason",
				"label": "Reason",
				"type": "select",
				"options": "attendance_reasons",
				"required": True,
				"full": True,
			},
			{"fieldname": "from_date", "label": "From Date", "type": "date", "required": True},
			{"fieldname": "to_date", "label": "To Date", "type": "date", "required": True},
			{"fieldname": "half_day", "label": "Half Day", "type": "checkbox", "full": True},
			{
				"fieldname": "explanation",
				"label": "Explanation",
				"type": "textarea",
				"placeholder": "Why was attendance not recorded?",
				"full": True,
			},
		],
	},
	"advance": {
		"doctype": "Employee Advance",
		"label": "Employee Advance",
		"list_route": "/advances",
		"currency_field": "currency",
		"attachments": False,
		"defaults": _advance_defaults,
		"summary": _advance_summary,
		"fields": [
			{
				"fieldname": "purpose",
				"label": "Purpose",
				"type": "textarea",
				"placeholder": "What is the advance for?",
				"required": True,
				"full": True,
			},
			{
				"fieldname": "advance_amount",
				"label": "Amount",
				"type": "number",
				"required": True,
			},
		],
	},
}


def _spec(request_type: str) -> dict:
	spec = REQUEST_TYPES.get(request_type)
	if not spec:
		frappe.throw(_("Unknown request type"))
	return spec


def _own_doc(request_type: str, name: str):
	"""Load a document, refusing anything that is not the current employee's."""
	spec = _spec(request_type)
	employee = get_current_employee()

	if not frappe.db.exists(spec["doctype"], name):
		frappe.throw(_("{0} not found").format(spec["label"]), frappe.DoesNotExistError)

	doc = frappe.get_doc(spec["doctype"], name)
	if doc.employee != employee:
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	return spec, doc


def _flat_fields(spec: dict) -> list[dict]:
	return [f for f in spec["fields"] if f["type"] != "table"]


def _table_field(spec: dict) -> dict | None:
	return next((f for f in spec["fields"] if f["type"] == "table"), None)


def _coerce(field: dict, raw):
	"""Turn one submitted value into something safe to write to the doc."""
	kind = field["type"]
	if kind == "number":
		value = flt(raw)
		if field.get("required") and value <= 0:
			frappe.throw(_("{0} must be greater than zero").format(field["label"]))
		return value
	if kind == "date":
		if not raw:
			if field.get("required"):
				frappe.throw(_("Pick a {0}").format(field["label"].lower()))
			return None
		return getdate(raw)
	if kind == "checkbox":
		return 1 if raw in (True, 1, "1", "true", "True") else 0
	if kind == "select":
		value = (raw or "").strip()
		if not value and field.get("required"):
			frappe.throw(_("Pick a {0}").format(field["label"].lower()))
		return value
	value = (raw or "").strip() if isinstance(raw, str) else raw
	if field.get("required") and not value:
		frappe.throw(_("{0} is required").format(field["label"]))
	return value


def _apply_values(spec: dict, doc, values: dict):
	for field in _flat_fields(spec):
		if field["fieldname"] in values:
			doc.set(field["fieldname"], _coerce(field, values.get(field["fieldname"])))

	table = _table_field(spec)
	if table:
		rows = values.get(table["fieldname"])
		if not rows or not isinstance(rows, list):
			frappe.throw(_("Add at least one {0}").format(table["row_label"].lower()))
		doc.set(table["fieldname"], [])
		for raw_row in rows:
			row = {}
			for field in table["fields"]:
				row[field["fieldname"]] = _coerce(field, raw_row.get(field["fieldname"]))
			doc.append(table["fieldname"], row)


def _sync_attachments(spec: dict, doc, attachments, removed):
	if not spec.get("attachments"):
		return

	if isinstance(removed, str):
		removed = frappe.parse_json(removed)
	for file_name in removed or []:
		owned = frappe.db.get_value(
			"File", file_name, ["attached_to_doctype", "attached_to_name"], as_dict=True
		)
		if owned and owned.attached_to_doctype == doc.doctype and owned.attached_to_name == doc.name:
			frappe.delete_doc("File", file_name, force=True, ignore_permissions=True)

	files = _validated_attachments(attachments)
	if not files:
		return

	existing = frappe.db.count("File", {"attached_to_doctype": doc.doctype, "attached_to_name": doc.name})
	if existing + len(files) > MAX_ATTACHMENTS:
		frappe.throw(_("You can attach at most {0} files").format(MAX_ATTACHMENTS))

	for f in files:
		frappe.get_doc(
			{
				"doctype": "File",
				"attached_to_doctype": doc.doctype,
				"attached_to_name": doc.name,
				"folder": "Home/Attachments",
				"is_private": 1,
				**f,
			}
		).insert(ignore_permissions=True)


def _display_status(doc) -> str:
	if doc.docstatus == 0:
		return "Draft"
	if doc.docstatus == 2:
		return "Cancelled"
	return getattr(doc, "status", None) or "Submitted"


def _serialise(spec: dict, doc) -> dict:
	approver = getattr(doc, spec["approver_field"], None) if spec.get("approver_field") else None
	approver_name = frappe.db.get_value("User", approver, "full_name") if approver else None

	attachments = []
	if spec.get("attachments"):
		attachments = frappe.get_all(
			"File",
			filters={"attached_to_doctype": doc.doctype, "attached_to_name": doc.name},
			fields=["name", "file_name", "file_url", "file_size"],
			order_by="creation asc",
		)

	values = {}
	for field in _flat_fields(spec):
		raw = doc.get(field["fieldname"])
		values[field["fieldname"]] = str(raw) if field["type"] == "date" and raw else raw

	table = _table_field(spec)
	if table:
		values[table["fieldname"]] = [
			{
				f["fieldname"]: (
					str(row.get(f["fieldname"]))
					if f["type"] == "date" and row.get(f["fieldname"])
					else row.get(f["fieldname"])
				)
				for f in table["fields"]
			}
			| {"idx": row.idx}
			for row in doc.get(table["fieldname"])
		]

	return {
		"type": next(k for k, v in REQUEST_TYPES.items() if v["doctype"] == doc.doctype),
		"name": doc.name,
		"label": spec["label"],
		"list_route": spec["list_route"],
		"docstatus": doc.docstatus,
		# a draft is the only state the employee can still change
		"editable": doc.docstatus == 0,
		"display_status": _display_status(doc),
		"posting_date": str(getattr(doc, "posting_date", None) or doc.creation.date()),
		"currency": doc.get(spec["currency_field"]) if spec.get("currency_field") else None,
		"approver": approver,
		"approver_name": approver_name or approver,
		"summary": spec["summary"](doc),
		"values": values,
		"attachments": attachments,
		"supports_attachments": bool(spec.get("attachments")),
	}


@frappe.whitelist()
def get_form(request_type: str) -> dict:
	"""Field schema for a type, with select options already resolved."""
	spec = _spec(request_type)
	employee = get_current_employee()

	def resolve(fields):
		out = []
		for field in fields:
			item = {k: v for k, v in field.items() if k != "fields"}
			if field.get("options") in OPTION_SOURCES:
				item["options"] = OPTION_SOURCES[field["options"]](employee)
			if field["type"] == "table":
				item["fields"] = resolve(field["fields"])
			out.append(item)
		return out

	return {
		"type": request_type,
		"label": spec["label"],
		"list_route": spec["list_route"],
		"supports_attachments": bool(spec.get("attachments")),
		"fields": resolve(spec["fields"]),
	}


@frappe.whitelist()
def get_request(request_type: str, name: str) -> dict:
	spec, doc = _own_doc(request_type, name)
	return _serialise(spec, doc)


@frappe.whitelist(methods=["POST"])
def create_request(request_type: str, values: str | dict, attachments: str | list | None = None) -> dict:
	spec = _spec(request_type)
	if isinstance(values, str):
		values = frappe.parse_json(values)

	employee = get_current_employee()
	emp = _employee_row(employee)

	doc = frappe.new_doc(spec["doctype"])
	doc.employee = employee
	for key, value in spec["defaults"](employee, emp).items():
		doc.set(key, value)
	_apply_values(spec, doc, values or {})
	doc.insert(ignore_permissions=True)

	_sync_attachments(spec, doc, attachments, None)
	frappe.db.commit()  # nosemgrep

	return {"ok": True, "name": doc.name, "type": request_type}


@frappe.whitelist(methods=["POST"])
def update_request(
	request_type: str,
	name: str,
	values: str | dict,
	attachments: str | list | None = None,
	removed_attachments: str | list | None = None,
) -> dict:
	spec, doc = _own_doc(request_type, name)
	if doc.docstatus != 0:
		frappe.throw(
			_("This {0} has been submitted and can no longer be edited").format(spec["label"].lower())
		)

	if isinstance(values, str):
		values = frappe.parse_json(values)

	_apply_values(spec, doc, values or {})
	doc.save(ignore_permissions=True)

	_sync_attachments(spec, doc, attachments, removed_attachments)
	frappe.db.commit()  # nosemgrep

	return {"ok": True, "name": doc.name, "type": request_type}


@frappe.whitelist(methods=["POST"])
def delete_request(request_type: str, name: str) -> dict:
	spec, doc = _own_doc(request_type, name)
	if doc.docstatus != 0:
		frappe.throw(_("Only a draft {0} can be deleted").format(spec["label"].lower()))

	frappe.delete_doc(spec["doctype"], doc.name, force=True, ignore_permissions=True)
	frappe.db.commit()  # nosemgrep
	return {"ok": True}
