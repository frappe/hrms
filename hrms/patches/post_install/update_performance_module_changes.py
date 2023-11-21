import frappe
from frappe.model.utils.rename_field import rename_field
from frappe.utils import cstr


def execute():
	create_kras()
	rename_fields()
	update_kra_evaluation_method()


def create_kras():
	# A new Link field `key_result_area` was added in the Appraisal Template Goal table
	# Old field's (`kra` (Small Text)) data now needs to be copied to the new field
	# This patch will create KRA's for all existing Appraisal Template Goal entries
	# keeping 140 characters as the KRA title and the whole KRA as the description
	# and then set the new title (140 characters) in the `key_result_area` field
	if not frappe.db.has_column("Appraisal Template Goal", "kra"):
		return

	template_goals = frappe.get_all(
		"Appraisal Template Goal",
		filters={"parenttype": "Appraisal Template", "key_result_area": ("is", "not set")},
		fields=["name", "kra"],
		as_list=True,
	)

	if len(template_goals) > 10000:
		frappe.db.auto_commit_on_many_writes = 1

	for name, kra in template_goals:
		if not kra:
			kra = "Key Result Area"

		kra_title = cstr(kra).replace("\n", " ").strip()[:140]

		if not frappe.db.exists("KRA", kra_title):
			frappe.get_doc(
				{
					"doctype": "KRA",
					"title": kra_title,
					"description": kra,
					"name": kra_title,
					"owner": "Administrator",
					"modified_by": "Administrator",
				}
			).db_insert()

		# set 140 char kra in the `key_result_area` field
		frappe.db.set_value(
			"Appraisal Template Goal", name, "key_result_area", kra_title, update_modified=False
		)

	if frappe.db.auto_commit_on_many_writes:
		frappe.db.auto_commit_on_many_writes = 0


def rename_fields():
	try:
		rename_field("Appraisal Template", "kra_title", "template_title")
		rename_field("Appraisal", "kra_template", "appraisal_template")

	except Exception as e:
		if e.args[0] != 1054:
			raise


def update_kra_evaluation_method():
	"""
	Update existing appraisals for backward compatibility
	- Set rate_goals_manually = True in existing Appraisals
	- Only new appraisals created after this patch can use the new method.
	"""

	Appraisal = frappe.qb.DocType("Appraisal")
	(
		frappe.qb.update(Appraisal)
		.set(Appraisal.rate_goals_manually, 1)
		.where(Appraisal.appraisal_cycle.isnull())
	).run()
