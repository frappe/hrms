# Copyright (c) 2026, Frappe Technologies and Contributors
# License: MIT. See LICENSE

import glob
import json
import os

import frappe
from frappe.tests import IntegrationTestCase


def shipped_workbooks():
	pattern = os.path.join(frappe.get_app_path("hrms"), "**", "insights_workbook", "*", "*.json")
	for path in glob.glob(pattern, recursive=True):
		with open(path) as f:
			yield json.load(f)


def tables_read_by(workbook):
	for query in workbook["queries"].values():
		for operation in query["operations"]:
			table = operation.get("table") or {}
			if table.get("type") == "table":
				yield table["table_name"].removeprefix("tab")


def readers_of(doctype):
	"""Insights reads a child table for a user who can read any of its parents."""
	meta = frappe.get_meta(doctype)
	if meta.istable:
		parents = frappe.get_all(
			"DocField",
			filters={"options": doctype, "fieldtype": ["in", frappe.model.table_fields]},
			pluck="parent",
			distinct=True,
		)
		return {role for parent in parents for role in readers_of(parent)}
	return {p.role for p in meta.permissions if p.read and not p.permlevel}


class TestInsightsWorkbooks(IntegrationTestCase):
	def test_every_role_a_dashboard_names_reads_every_table_it_queries(self):
		for workbook in shipped_workbooks():
			roles = {
				row["role"] for board in workbook["dashboards"].values() for row in board["visible_to_roles"]
			}
			for doctype in set(tables_read_by(workbook)):
				with self.subTest(workbook=workbook["name"], doctype=doctype):
					self.assertFalse(roles - readers_of(doctype), f"cannot read {doctype}")
