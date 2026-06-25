# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


TYPE_ORDER = {"Head Office": 0, "District Office": 1, "Branch": 2}


def _sort_tree(nodes: list) -> None:
	"""Order children Head Office → District Office → Branch, then by name."""
	nodes.sort(key=lambda n: (TYPE_ORDER.get(n.get("location_1"), 9), n.get("location") or ""))
	for node in nodes:
		if node.get("children"):
			_sort_tree(node["children"])


@frappe.whitelist()
def get_chart_data():
	"""Return organization units with a physical site as a nested tree for the chart."""
	locations = frappe.get_all(
		"Organization Unit",
		filters={"location_1": ["is", "set"]},
		fields=[
			"name",
			"unit_name",
			"unit_code",
			"location_1",
			"parent_organization_unit",
			"region",
			"zone",
			"city",
			"woreda",
			"status",
			"lft",
		],
		order_by="lft asc",
	)

	branch_counts = _branch_counts_by_parent()
	position_counts = _position_counts_by_site()

	nodes = {}
	for loc in locations:
		geo = _format_geography(loc)
		nodes[loc.name] = {
			"id": loc.name,
			"location": loc.unit_name,
			"location_code": loc.unit_code or "",
			"location_1": loc.location_1 or "",
			"status": loc.status or "",
			"geography": geo,
			"branch_count": branch_counts.get(loc.name, 0),
			"position_count": position_counts.get(loc.name, 0),
			"children": [],
		}

	roots = []
	for loc in locations:
		node = nodes[loc.name]
		parent = nodes.get(loc.parent_organization_unit)
		if parent:
			parent["children"].append(node)
		else:
			roots.append(node)

	_sort_tree(roots)
	return roots


def _format_geography(loc) -> str:
	parts = [loc.region, loc.zone, loc.city, loc.woreda]
	return " · ".join(part for part in parts if part)


def _branch_counts_by_parent() -> dict[str, int]:
	counts: dict[str, int] = {}
	for row in frappe.get_all(
		"Organization Unit",
		filters={"location_1": "Branch", "parent_organization_unit": ["is", "set"]},
		fields=["parent_organization_unit"],
	):
		counts[row.parent_organization_unit] = counts.get(row.parent_organization_unit, 0) + 1
	return counts


def _position_counts_by_site() -> dict[str, int]:
	counts: dict[str, int] = {}
	for row in frappe.get_all(
		"Position",
		fields=["site_organization_unit"],
		filters={"site_organization_unit": ["is", "set"]},
	):
		counts[row.site_organization_unit] = counts.get(row.site_organization_unit, 0) + 1
	return counts
