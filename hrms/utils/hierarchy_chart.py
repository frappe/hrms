# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt


import frappe
from frappe import _
from frappe.handler import is_valid_http_method

HIERARCHY_CHART_METHODS = ("hrms.hr.page.organizational_chart.organizational_chart.get_children",)


@frappe.whitelist()
def get_all_nodes(method: str, company: str):
	"""Recursively gets all data from nodes"""
	if method not in HIERARCHY_CHART_METHODS:
		frappe.throw(_("Not Permitted"), frappe.PermissionError)

	method = frappe.get_attr(frappe.override_whitelisted_method(method))
	frappe.is_whitelisted(method)
	if getattr(frappe.local, "request", None):
		is_valid_http_method(method)

	root_nodes = method(company=company)
	result = []
	nodes_to_expand = []

	for root in root_nodes:
		data = method(root.id, company)
		result.append(dict(parent=root.id, parent_name=root.name, data=data))
		nodes_to_expand.extend(
			[{"id": d.get("id"), "name": d.get("name")} for d in data if d.get("expandable")]
		)

	while nodes_to_expand:
		parent = nodes_to_expand.pop(0)
		data = method(parent.get("id"), company)
		result.append(dict(parent=parent.get("id"), parent_name=parent.get("name"), data=data))
		for d in data:
			if d.get("expandable"):
				nodes_to_expand.append({"id": d.get("id"), "name": d.get("name")})

	return result
