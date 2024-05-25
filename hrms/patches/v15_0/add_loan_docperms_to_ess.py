import frappe

from hrms.setup import add_lending_docperms_to_ess, update_user_type_doctype_limit


def execute():
	if "lending" in frappe.get_installed_apps():
		update_user_type_doctype_limit()
		add_lending_docperms_to_ess()
