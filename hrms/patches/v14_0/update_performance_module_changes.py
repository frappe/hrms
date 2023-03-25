import frappe
from frappe.model.utils.rename_field import rename_field


def execute():
	_rename_fields()
	_create_kras()
	update_existing_appraisals()


def _rename_fields():
	try:
		rename_field("Appraisal Template", "kra_title", "template_title")
		rename_field("Appraisal", "kra_template", "appraisal_template")

	except Exception as e:
		if e.args[0] != 1054:
			raise


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


def update_existing_appraisals():
	"""
	Update existing appraisals for backward compatibility

	- Set rate_goals_manually = True in existing Appraisals
	- Only new appraisals created after this patch can use the new method.

	- Set Appraisal Period Based on = 'Custom Date Range' for existing Appraisals
	- Because old Appraisals don't have an Appraisal Cycle linked
	"""

	Appraisal = frappe.qb.DocType("Appraisal")
	(
		frappe.qb.update(Appraisal)
		.set(Appraisal.rate_goals_manually, 1)
		.set(Appraisal.period_based_on, "Custom Date Range")
		.where(Appraisal.appraisal_cycle.isnull())
	).run()
