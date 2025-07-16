import frappe


def execute():
	"""There was a bug where per_billed was not exactly 100, but slightly more
	or less. This caused the status to not be correctly updated to "Billed".

	This patch re-runs the fixed `set_status()` on all Timesheets that are
	fully billed but still have the status "Submitted". If the status changed
	(likely to "Billed"), it silently updates the value in the database.
	"""
	for ts_name in frappe.get_all(
		"Timesheet", filters={"per_billed": 100, "status": "Submitted"}, pluck="name"
	):
		ts = frappe.get_doc("Timesheet", ts_name)
		old_status = ts.status
		ts.set_status()
		if ts.status != old_status:
			ts.db_set("status", ts.status, update_modified=False)
