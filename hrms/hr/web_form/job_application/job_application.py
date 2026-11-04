import frappe


def get_context(context):
	job_opening = frappe.form_dict.job_title
	if not job_opening or not isinstance(job_opening, str):
		return

	# the form is open to guests, so only titles already public on the website are shared
	context.web_form_doc.job_opening_title = frappe.db.get_value(
		"Job Opening", {"name": job_opening, "publish": 1}, "job_title"
	)
