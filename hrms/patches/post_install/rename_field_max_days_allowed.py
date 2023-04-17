import frappe
from frappe.model.utils.rename_field import rename_field


def execute():
	if not frappe.db.has_column("Leave Type", "max_days_allowed"):
		return

	frappe.db.sql(
		"""
		UPDATE `tabLeave Type`
		SET max_days_allowed = '0'
		WHERE trim(coalesce(max_days_allowed, '')) = ''
	"""
	)
	frappe.db.sql_ddl("""ALTER table `tabLeave Type` modify max_days_allowed int(8) NOT NULL""")
	frappe.reload_doc("hr", "doctype", "leave_type")
	rename_field("Leave Type", "max_days_allowed", "max_continuous_days_allowed")

	if frappe.db.has_column("Leave Type", "max_days_allowed"):
		frappe.db.sql("alter table `tabLeave Type` drop column max_days_allowed")
		# clear cache for doctype as it stores table columns in cache
		frappe.clear_cache(doctype="Leave Type")
