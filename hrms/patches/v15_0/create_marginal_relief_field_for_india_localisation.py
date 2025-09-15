# Copyright (c) 2019, Frappe and Contributors
# License: GNU General Public License v3. See license.txt

import frappe

from hrms.regional.india.setup import make_custom_fields


def execute():
	company = frappe.get_all("Company", filters={"country": "India"})
	if not company:
		return

	make_custom_fields()

	frappe.reload_doc("payroll", "doctype", "income_tax_slab")
