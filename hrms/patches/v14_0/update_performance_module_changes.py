import frappe


def execute():
	_create_kras()


def _create_kras():
	# Appraisal Template Goal's KRA field was changed from Small Text to Link
	# This patch will create KRA's for all existing Appraisal Template Goal entries
	# keeping 140 characters as the KRA title and the whole KRA as the description
	frappe.reload_doc("hr", "doctype", "kra")

	templates = frappe.get_all("Appraisal Template", pluck="name")

	for template in templates:
		template_doc = frappe.get_doc("Appraisal Template", template)
		for entry in template_doc.goals:
			kra_title = entry.kra[:140].strip()

			if not frappe.db.exists("KRA", kra_title):
				kra = frappe.get_doc(
					{
						"doctype": "KRA",
						"title": kra_title,
						"description": entry.kra,
					}
				).insert(ignore_permissions=True)

				kra_title = kra.name

			entry.kra = kra_title

		template_doc.save(ignore_permissions=True)
