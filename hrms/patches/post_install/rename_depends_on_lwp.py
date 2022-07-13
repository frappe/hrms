# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import scrub
from frappe.model.utils.rename_field import rename_field


def execute():
	for doctype in ("Salary Component", "Salary Detail"):
		if frappe.db.has_column(doctype, "depends_on_lwp"):
			frappe.reload_doc("Payroll", "doctype", scrub(doctype))
			rename_field(doctype, "depends_on_lwp", "depends_on_payment_days")
