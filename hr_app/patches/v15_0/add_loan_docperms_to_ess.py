import frappe

from hr_app.setup import add_lending_docperms_to_ess


def execute():
	if "lending" in frappe.get_installed_apps():
		add_lending_docperms_to_ess()
