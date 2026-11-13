import frappe
from frappe.utils import escape_html

TERMS_TABLE = "Appointment Letter content"


def execute():
	if not frappe.db.table_exists(TERMS_TABLE):
		return

	for doctype in ("Appointment Letter Template", "Appointment Letter"):
		if not frappe.db.has_column(doctype, "introduction"):
			continue

		table = frappe.qb.DocType(doctype)
		fields = [table.name, table.introduction]
		if frappe.db.has_column(doctype, "closing_notes"):
			fields.append(table.closing_notes)

		for row in (
			frappe.qb.from_(table)
			.select(*fields)
			.where(table.letter_body.isnull() | (table.letter_body == ""))
			.run(as_dict=True)
		):
			body = get_letter_body(row.introduction, get_terms(doctype, row.name), row.get("closing_notes"))
			if body:
				frappe.db.set_value(doctype, row.name, "letter_body", body, update_modified=False)


def get_terms(parenttype: str, parent: str) -> list[dict]:
	terms = frappe.qb.DocType(TERMS_TABLE)
	return (
		frappe.qb.from_(terms)
		.select(terms.title, terms.description)
		.where((terms.parenttype == parenttype) & (terms.parent == parent))
		.orderby(terms.idx)
		.run(as_dict=True)
	)


def get_letter_body(introduction: str | None, terms: list[dict], closing_notes: str | None) -> str:
	clauses = "".join(get_clause(term) for term in terms)
	body = (
		get_paragraph(introduction)
		+ (f"<ol>{clauses}</ol>" if clauses else "")
		+ get_paragraph(closing_notes)
	)
	return f'<div class="ql-editor read-mode">{body}</div>' if body else ""


def get_clause(term: dict) -> str:
	title = f"<strong>{escape_html(term.title)}:</strong> " if term.title else ""
	return (
		'<li data-list="ordered"><span class="ql-ui" contenteditable="false"></span>'
		f"{title}{to_html(term.description)}</li>"
	)


def get_paragraph(text: str | None) -> str:
	return f"<p>{to_html(text)}</p>" if text else ""


def to_html(text: str | None) -> str:
	return escape_html(text or "").replace("\n", "<br>")
