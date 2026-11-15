import frappe
from frappe.modules.import_file import import_file_by_path

BOARD = "Hiring Pipeline"


def execute():
	"""Sites that opened the old status-based board keep it as their own; the standard stage board replaces it."""
	board = frappe.db.get_value(
		"Kanban Board", BOARD, ["reference_doctype", "field_name", "is_standard"], as_dict=True
	)
	if not board or (board.reference_doctype, board.field_name, board.is_standard) != (
		"Job Applicant",
		"status",
		"No",
	):
		return

	frappe.delete_doc("Kanban Board", BOARD, force=True, ignore_permissions=True)
	import_file_by_path(
		frappe.get_app_path(
			"hrms", "recruitment", "doctype", "job_applicant", "kanban_board", "hiring_pipeline.json"
		),
		force=True,
	)
