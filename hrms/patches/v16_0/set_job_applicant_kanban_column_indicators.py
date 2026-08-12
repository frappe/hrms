import frappe

INDICATOR_MAP = {
	"Replied": "Orange",
	"Shortlisted": "Blue",
	"Accepted": "Green",
}


def execute():
	columns = frappe.get_all(
		"Kanban Board Column",
		filters={"parent": "Hiring Pipeline", "parenttype": "Kanban Board"},
		fields=["name", "column_name"],
	)

	if not columns:
		return

	updates = {col.name: {"indicator": INDICATOR_MAP.get(col.column_name, "")} for col in columns}
	frappe.db.bulk_update("Kanban Board Column", updates, update_modified=False)
