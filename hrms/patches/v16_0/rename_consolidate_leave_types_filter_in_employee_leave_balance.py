import frappe
from frappe.utils import cint

REPORT = "Employee Leave Balance"


def execute():
	# filter `consolidate_leave_types` (Check) -> `consolidate_by` (Select: "Leave Type" / "Employee")
	migrate_custom_reports()
	migrate_saved_filters("Auto Email Report", "filters", "report")
	migrate_saved_filters("Dashboard Chart", "filters_json", "report_name", type_field="chart_type")
	migrate_saved_filters("Number Card", "filters_json", "report_name", type_field="type")


def migrate_custom_reports():
	reports = frappe.get_all(
		"Report",
		filters={"report_type": "Custom Report", "reference_report": REPORT},
		fields=["name", "json"],
	)

	for report in reports:
		report_json = parse_json(report.json)
		if not report_json or not rewrite_filters(report_json.get("filters")):
			continue

		frappe.db.set_value(
			"Report", report.name, "json", frappe.as_json(report_json, indent=None), update_modified=False
		)


def migrate_saved_filters(doctype, filter_field, report_field, type_field=None):
	conditions = {report_field: REPORT}
	if type_field:
		conditions[type_field] = "Report"

	for row in frappe.get_all(doctype, filters=conditions, fields=["name", filter_field]):
		filters = parse_json(row.get(filter_field))
		if not rewrite_filters(filters):
			continue

		frappe.db.set_value(
			doctype, row.name, filter_field, frappe.as_json(filters, indent=None), update_modified=False
		)


def parse_json(raw):
	if not raw:
		return None

	try:
		return frappe.parse_json(raw)
	except ValueError:
		return None


def rewrite_filters(filters) -> bool:
	if not isinstance(filters, dict) or "consolidate_leave_types" not in filters:
		return False

	consolidate = cint(filters.pop("consolidate_leave_types"))
	filters["consolidate_by"] = "Leave Type" if consolidate else ""
	return True
