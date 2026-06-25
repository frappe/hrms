# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

from hrms.organization_structure.doctype.position.position import resolve_position_chart_unit


@frappe.whitelist()
def get_chart_data():
	"""Return the Organization Unit hierarchy with positions nested under each unit.

	Each org unit box shows its head position (if any). All other active positions
	linked to the unit appear below it in a reporting sub-tree.
	"""
	units = frappe.get_all(
		"Organization Unit",
		fields=[
			"name",
			"unit_name",
			"unit_type",
			"parent_organization_unit",
			"lft",
		],
		order_by="lft asc",
	)

	head_positions = _get_head_positions()
	positions_by_unit = _get_positions_by_unit(head_positions)
	employee_names = _get_employee_names(_collect_employee_ids(head_positions, positions_by_unit))

	for unit_positions in positions_by_unit.values():
		_attach_employee_names(unit_positions, employee_names)

	nodes = {}
	for u in units:
		head = head_positions.get(u.name)
		unit_positions = positions_by_unit.get(u.name, [])
		display = head
		child_positions = unit_positions

		if not display and unit_positions:
			display_row = unit_positions[0]
			display = frappe._dict(
				position_name=display_row.get("title"),
				current_employee=display_row.get("current_employee"),
				is_occupied=display_row.get("occupied"),
			)
			child_positions = display_row.get("children") or []

		nodes[u.name] = {
			"id": u.name,
			"unit": u.unit_name,
			"unit_type": u.unit_type or "",
			"has_head": 1 if display else 0,
			"title": display.position_name if display else "",
			"employee": (employee_names.get(display.current_employee) if display else "") or "",
			"occupied": 1 if (display and display.is_occupied) else 0,
			"positions": child_positions,
			"children": [],
		}

	roots = []
	for u in units:
		node = nodes[u.name]
		parent = nodes.get(u.parent_organization_unit)
		if parent:
			parent["children"].append(node)
		else:
			roots.append(node)

	return roots


def _get_head_positions():
	"""Map each organization unit to its head position (first one wins)."""
	rows = frappe.get_all(
		"Position",
		filters={"is_head_position": 1, "position_status": "Active"},
		fields=[
			"name",
			"organization_unit",
			"org_district",
			"org_branch",
			"site_organization_unit",
			"position_name",
			"current_employee",
			"is_occupied",
		],
		order_by="lft asc",
	)

	heads = {}
	for row in rows:
		unit = resolve_position_chart_unit(row)
		if unit and unit not in heads:
			heads[unit] = row
	return heads


def _get_positions_by_unit(head_positions: dict) -> dict:
	"""Group active positions by organization unit, excluding head positions shown in the unit box."""
	rows = frappe.get_all(
		"Position",
		filters={"position_status": "Active"},
		fields=[
			"name",
			"position_name",
			"organization_unit",
			"org_district",
			"org_branch",
			"site_organization_unit",
			"parent_position",
			"current_employee",
			"is_occupied",
			"is_head_position",
			"lft",
		],
		order_by="lft asc",
	)

	head_ids = {head.name for head in head_positions.values()}
	by_unit: dict[str, list] = {}

	for row in rows:
		if row.name in head_ids:
			continue

		target_unit = resolve_position_chart_unit(row)
		if not target_unit:
			continue

		by_unit.setdefault(target_unit, []).append(
			{
				"id": row.name,
				"title": row.position_name,
				"current_employee": row.current_employee,
				"employee": "",
				"occupied": 1 if row.is_occupied else 0,
				"parent_position": row.parent_position,
			}
		)

	return {unit: _build_position_tree(positions) for unit, positions in by_unit.items()}


def _build_position_tree(positions: list) -> list:
	"""Build a nested reporting tree for positions within one organization unit."""
	index = {row["id"]: {**row, "children": []} for row in positions}
	roots = []

	for row in positions:
		node = index[row["id"]]
		parent = row.get("parent_position")
		if parent and parent in index:
			index[parent]["children"].append(node)
		else:
			roots.append(node)

	return roots


def _collect_employee_ids(head_positions: dict, positions_by_unit: dict) -> list[str]:
	employee_ids = [head.current_employee for head in head_positions.values() if head.current_employee]

	def walk(nodes):
		for node in nodes:
			if node.get("current_employee"):
				employee_ids.append(node["current_employee"])
			walk(node.get("children") or [])

	for roots in positions_by_unit.values():
		walk(roots)

	return employee_ids


def _attach_employee_names(nodes: list, employee_names: dict) -> None:
	for node in nodes:
		node["employee"] = employee_names.get(node.get("current_employee")) or ""
		_attach_employee_names(node.get("children") or [], employee_names)


def _get_employee_names(employee_ids: list) -> dict:
	if not employee_ids:
		return {}

	rows = frappe.get_all(
		"Employee",
		filters={"name": ["in", list(set(employee_ids))]},
		fields=["name", "employee_name"],
	)
	return {row.name: row.employee_name for row in rows}
