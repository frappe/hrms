import frappe
from frappe.model.rename_doc import rename_doc


def execute():
	if frappe.db.has_table("Interview Round"):
		for interview_round, interview_type in frappe.get_all(
			"Interview Round", fields=["name", "interview_type"], as_list=True
		):
			if interview_type != interview_round and interview_type and interview_round:
				rename_doc("Interview Type", interview_type, interview_round)
